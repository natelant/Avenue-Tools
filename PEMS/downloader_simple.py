# pems_collector.py
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import pandas as pd
import requests
from pathlib import Path
import logging
from typing import List
import configparser

@dataclass
class ConfigSettings:
    """Configuration settings for PeMS data collection."""
    start_date: date
    end_date: date
    username: str
    password: str
    second_param: str = "speed"
    granularity: str = "5min"
    directory_name: str = "data"

    @classmethod
    def from_dates(cls, start_date: str, end_date: str, username: str, password: str) -> 'ConfigSettings':
        """Create ConfigSettings from date strings and credentials."""
        return cls(
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
            username=username,
            password=password
        )

class PeMSCollector:
    """Handles collection of PeMS traffic data."""
    
    BASE_URL = "https://udot.iteris-pems.com"
    
    def __init__(self, config: ConfigSettings):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest'
        })
        Path(config.directory_name).mkdir(parents=True, exist_ok=True)
        self._login()

    def _login(self):
        """Login to PeMS website."""
        try:
            # First get the login page to get any necessary cookies
            self.session.get(f"{self.BASE_URL}/")
            
            # Perform login
            login_data = {
                'username': self.config.username,
                'password': self.config.password,
                'login': 'Login'
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/account/login",
                data=login_data,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Verify login was successful
            if 'Login failed' in response.text:
                raise ValueError("Login failed - check credentials")
                
            logging.info("Successfully logged in to PeMS")
            
        except Exception as e:
            logging.error(f"Login failed: {e}")
            raise

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
                f"{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}_"
                f"{self.config.granularity}_{station}.xlsx")

    def collect_data(self, station: int, start_date: date, end_date: date):
        """Collect data for a specific station and date range."""
        try:
            params = {
                'report_form': '1',
                'dnode': 'VDS',
                'content': 'detector_health',
                'tab': 'dh_raw',
                'export': 'xls',
                'station_id': station,
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'start_time': '00:00',
                'end_time': '23:59',
                'q': 'flow',
                'q2': self.config.second_param,
                'gn': self.config.granularity,
            }
            
            filename = self._create_filename(start_date, end_date, station)
            
            self.session.get(f"{self.BASE_URL}/")
            
            response = self.session.get(
                f"{self.BASE_URL}/data/export", 
                params=params, 
                stream=True,
                timeout=30
            )
            
            retries = 3
            while response.status_code == 500 and retries > 0:
                logging.warning(f"Retrying request for station {station} ({retries} attempts left)")
                response = self.session.get(
                    f"{self.BASE_URL}/data/export", 
                    params=params, 
                    stream=True,
                    timeout=30
                )
                retries -= 1
            
            response.raise_for_status()
            
            if 'application/vnd.ms-excel' not in response.headers.get('Content-Type', ''):
                raise ValueError(f"Unexpected response type: {response.headers.get('Content-Type')}")
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info(f"Successfully downloaded data to {filename}")
            
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error for station {station}: {e}")
            if response.status_code == 500:
                logging.error(f"Response content: {response.text[:200]}...")
            raise
        except Exception as e:
            logging.error(f"Failed to collect data for station {station}: {e}")
            raise

    def run(self, stations: List[int]):
        """Run the data collection process for all stations."""
        increment = self._get_increment()
        
        for station in stations:
            try:
                current_date = self.config.start_date
                while current_date <= self.config.end_date:
                    end_date = min(
                        current_date + timedelta(days=increment - 1),
                        self.config.end_date
                    )
                    try:
                        self.collect_data(station, current_date, end_date)
                    except Exception as e:
                        logging.error(f"Failed to collect data for station {station} "
                                    f"from {current_date} to {end_date}: {e}")
                        current_date += timedelta(days=increment)
                        continue
                    current_date += timedelta(days=increment)
            except Exception as e:
                logging.error(f"Failed processing station {station}: {e}")
                continue

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Read credentials from config file
        config_parser = configparser.ConfigParser()
        config_parser.read('config.ini')
        
        username = config_parser.get('credentials', 'username')
        password = config_parser.get('credentials', 'password')
        
        # Create config with credentials
        config = ConfigSettings.from_dates(
            start_date="2024-01-01",
            end_date="2024-01-31",
            username=username,
            password=password
        )
        
        # Read stations and run collector
        stations = PeMSCollector.read_stations("stations.csv")
        collector = PeMSCollector(config)
        collector.run(stations)
        
    except Exception as e:
        logging.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()