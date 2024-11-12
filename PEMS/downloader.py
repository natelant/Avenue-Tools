# pems_collector.py
import os
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import pandas as pd
import requests
from pathlib import Path
import logging
from typing import List, Optional

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

    def collect_data(self, station: int, start_date: date, end_date: date):
        """Collect data for a specific station and date range."""
        try:
            start_sec = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_sec = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            params = self._create_url_params(start_date, station, start_sec, end_sec)
            filename = self._create_filename(start_date, end_date, station)
            
            response = self.session.get(self.BASE_URL, params=params, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info(f"Successfully downloaded data to {filename}")
            
        except Exception as e:
            logging.error(f"Failed to collect data for station {station}: {e}")
            raise

    def run(self, stations: List[int]):
        """Run the data collection process for all stations."""
        increment = self._get_increment()
        
        for station in stations:
            current_date = self.config.start_date
            while current_date <= self.config.end_date:
                end_date = min(
                    current_date + timedelta(days=increment - 1),
                    self.config.end_date
                )
                self.collect_data(station, current_date, end_date)
                current_date += timedelta(days=increment)

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        config = ConfigSettings.from_csv("old/PeMS_config.csv")
        stations = PeMSCollector.read_stations("old/PeMS_Stations.csv")
        
        collector = PeMSCollector(config)
        collector.run(stations)
        
    except Exception as e:
        logging.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()