# pems_collector.py
import os
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import pandas as pd
import requests
from pathlib import Path
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from tqdm import tqdm

@dataclass
class ConfigSettings:
    """Configuration settings for PeMS data collection."""
    browser: str
    start_date: date
    end_date: date
    second_param: str
    granularity: str
    session_id: str
    directory_name: str

    @classmethod
    def from_csv(cls, config_file: str) -> 'ConfigSettings':
        """Create ConfigSettings from a CSV file."""
        try:
            df = pd.read_csv(config_file)
            row = df.iloc[0]  # Assume first row contains settings
            
            return cls(
                browser=row['Browser'],
                start_date=pd.to_datetime(row['StartDate']).date(),
                end_date=pd.to_datetime(row['EndDate']).date(),
                second_param=row['Variable'],
                granularity=row['Gran'],
                session_id=f"PHPSESSID={row['PHP']}",
                directory_name=row['Directory']
            )
        except Exception as e:
            logging.error(f"Failed to read config file: {e}")
            raise

class PeMSCollector:
    """Handles collection of PeMS traffic data."""
    
    BASE_URL = "https://udot.iteris-pems.com"
    MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def __init__(self, config: ConfigSettings):
        self.config = config
        self.session = requests.Session()
        self._setup_session()
        Path(config.directory_name).mkdir(parents=True, exist_ok=True)

    def _setup_session(self):
        """Configure the requests session with necessary headers."""
        self.session.headers.update({
            'User-Agent': f'Chrome/{self.config.browser}',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cookie': self.config.session_id
        })

    @staticmethod
    def read_stations(station_file: str) -> List[int]:
        """Read station IDs from CSV file."""
        try:
            return pd.read_csv(station_file)['stationID'].astype(int).tolist()
        except Exception as e:
            logging.error(f"Failed to read stations file: {e}")
            raise

    def _get_increment(self) -> int:
        """Determine file increment based on granularity."""
        return {
            'sec': 1,    # daily files
            '5min': 7,   # weekly files
        }.get(self.config.granularity, 92)  # default to 92 days

    def _create_filename(self, start_date: date, end_date: date, station: int) -> str:
        """Generate filename for the data file."""
        return (f"{self.config.directory_name}/"
                f"{self.MONTH_NAMES[start_date.month - 1]}-{start_date.day:02d}-{start_date.year}_"
                f"{self.MONTH_NAMES[end_date.month - 1]}-{end_date.day:02d}-{end_date.year}_"
                f"{self.config.granularity}_{station}.xlsx")

    def _create_url_params(self, start_date: date, station: int, start_sec: int, end_sec: int) -> dict:
        """Create URL parameters for PeMS API request."""
        return {
            'report_form': '1',
            'dnode': 'VDS',
            'content': 'detector_health',
            'tab': 'dh_raw',
            'export': 'xls',
            'station_id': station,
            's_time_id': start_sec,
            's_mm': start_date.month,
            's_dd': start_date.day,
            's_yy': start_date.year,
            's_hh': '0',
            's_mi': '0',
            'e_time_id': end_sec,
            'e_mm': start_date.month,
            'e_dd': start_date.day,
            'e_yy': start_date.year,
            'e_hh': '23',
            'e_mi': '55',
            'lanes': f'{station}-0',
            'q': 'flow',
            'q2': self.config.second_param,
            'gn': self.config.granularity
        }

    def collect_data(self, station: int, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Collect data for a specific station and date range and return as DataFrame."""
        try:
            # Convert dates to Unix timestamps for the API request
            start_sec = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_sec = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            # Create parameters for the API request
            params = self._create_url_params(start_date, station, start_sec, end_sec)
            
            # Make the API request
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
            
            # Read Excel data from the response content
            # BytesIO is needed because response.content is in bytes format
            from io import BytesIO
            df = pd.read_excel(BytesIO(response.content), engine='openpyxl')

            # Write the response to a csv file
            df.to_csv(f"{self.config.directory_name}/raw_data_{station}.csv", index=False)
            
            
            all_data = []
            
            # Find available lanes by checking column names
            # Some stations might not have all lanes, so we need to check which ones exist
            available_lanes = []
            for lane in range(1, 7):  # Check lanes 1-6
                flow_col = f'{station} Lane {lane} Flow'
                speed_col = f'{station} Lane {lane} Speed - Used in Calculations'
                # Only include lanes that have both flow and speed data
                if flow_col in df.columns and speed_col in df.columns:
                    available_lanes.append(lane)
            
            # If no valid lanes found, log warning and skip this station
            if not available_lanes:
                logging.warning(f"No valid lanes found for station {station}")
                return None
            
            # Process each available lane
            for lane in available_lanes:
                # Create a standardized DataFrame for each lane
                # This makes it easier to combine data from multiple stations later
                lane_data = pd.DataFrame({
                    'StationID': station,
                    'ReadingDateTime': df['Sample Time'],
                    'Lane': lane,
                    'Volume': df[f'{station} Lane {lane} Flow'],
                    'Speed': df[f'{station} Lane {lane} Speed - Used in Calculations']
                })
                all_data.append(lane_data)
            
            # Combine all lanes into a single DataFrame
            return pd.concat(all_data, ignore_index=True)
            
        except Exception as e:
            # Log any errors that occur during data collection
            logging.error(f"Failed to collect data for station {station}: {e}")
            return None

    def _get_date_chunks(self, start_date: date, end_date: date, chunk_size: int) -> List[tuple]:
        """Break the date range into chunks for parallel processing.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            chunk_size: Number of days per chunk
            
        Returns:
            List of (chunk_start_date, chunk_end_date) tuples
        """
        chunks = []
        current_date = start_date
        
        while current_date <= end_date:
            chunk_end = min(
                current_date + timedelta(days=chunk_size - 1),
                end_date
            )
            chunks.append((current_date, chunk_end))
            current_date = chunk_end + timedelta(days=1)
            
        return chunks

    def _save_progress(self, station: int, completed_chunks: List[tuple]):
        """Save progress to a JSON file for resume capability."""
        progress_file = Path(self.config.directory_name) / f"progress_{station}.json"
        with open(progress_file, 'w') as f:
            json.dump({
                'station': station,
                'completed_chunks': [(c[0].isoformat(), c[1].isoformat()) for c in completed_chunks]
            }, f)

    def _load_progress(self, station: int) -> List[tuple]:
        """Load previously completed chunks from progress file."""
        progress_file = Path(self.config.directory_name) / f"progress_{station}.json"
        if progress_file.exists():
            with open(progress_file) as f:
                data = json.load(f)
                return [(date.fromisoformat(c[0]), date.fromisoformat(c[1])) 
                        for c in data['completed_chunks']]
        return []

    def run(self, stations: List[int], max_workers: int = 3) -> pd.DataFrame:
        """Run the data collection process using parallel processing.
        
        Args:
            stations: List of station IDs to collect
            max_workers: Maximum number of parallel threads (default: 3)
        
        Returns:
            Combined DataFrame of all collected data
        """
        all_data = []
        chunk_size = self._get_increment()
        
        # Process each station
        for station in stations:
            logging.info(f"Processing station {station}")
            
            # Load any previously completed chunks
            completed_chunks = self._load_progress(station)
            
            # Get all chunks for the date range
            chunks = self._get_date_chunks(self.config.start_date, self.config.end_date, chunk_size)
            
            # Filter out completed chunks
            chunks = [c for c in chunks if c not in completed_chunks]
            
            if not chunks:
                logging.info(f"Station {station} already completed")
                continue
            
            station_data = []
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create a progress bar
                with tqdm(total=len(chunks), desc=f"Station {station}") as pbar:
                    # Submit all chunks for processing
                    future_to_chunk = {
                        executor.submit(self.collect_data, station, chunk[0], chunk[1]): chunk 
                        for chunk in chunks
                    }
                    
                    # Process completed futures as they finish
                    for future in as_completed(future_to_chunk):
                        chunk = future_to_chunk[future]
                        try:
                            data = future.result()
                            if data is not None:
                                station_data.append(data)
                                completed_chunks.append(chunk)
                                self._save_progress(station, completed_chunks)
                        except Exception as e:
                            logging.error(f"Failed to process chunk {chunk}: {e}")
                        pbar.update(1)
            
            # Combine all data for this station
            if station_data:
                station_df = pd.concat(station_data, ignore_index=True)
                all_data.append(station_df)
                
                # Save intermediate results
                station_file = Path(self.config.directory_name) / f"station_{station}_data.csv"
                station_df.to_csv(station_file, index=False)
                logging.info(f"Saved data for station {station} to {station_file}")
        
        # Combine all station data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df.sort_values('ReadingDateTime')
        return pd.DataFrame()

def main():
    """Main entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        config = ConfigSettings.from_csv("old/PeMS_config.csv")
        stations = PeMSCollector.read_stations("old/PeMS_Stations.csv")
        
        # Collect and process data
        collector = PeMSCollector(config)
        raw_data = collector.run(stations, max_workers=3)  # Adjust max_workers based on your system
        
        # Save final processed data
        output_file = Path(config.directory_name) / "processed_data.csv"
        raw_data.to_csv(output_file, index=False)
        logging.info(f"Processed data saved to {output_file}")
        
    except Exception as e:
        logging.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()