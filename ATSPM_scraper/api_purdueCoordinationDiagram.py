import requests
import json
import sqlite3
from datetime import datetime, date
import pandas as pd
from datetime import datetime, timedelta

# Add this function at the beginning of your script
def adapt_date(val):
    return val.isoformat()

# Register the adapter
sqlite3.register_adapter(date, adapt_date)

# Replace with the URL you found in the developer console
url = 'https://report-api-bdppc3riba-wm.a.run.app/v1/PurdueCoordinationDiagram/GetReportData'

# If there are any specific headers, like authorization tokens, add them here
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    # Add other headers you might need
}

# # List of location identifiers and start dates
# location_identifiers = ["7157", "7158", "7159"]  # Add more as needed
# start_dates = ["2024-08-21", "2024-08-22", "2024-08-23"]  # Add more as needed

# Read location identifiers from signals.csv
signals_df = pd.read_csv('data/signals.csv')
location_identifiers = signals_df['Signal_ID'].astype(str).tolist()

# Create a date range for start dates
start_date = datetime(2024, 8, 1)  # Adjust this to your desired start date
end_date = datetime(2024, 8, 27)  # Adjust this to your desired end date
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
start_dates = [date.strftime('%Y-%m-%d') for date in date_range]

print(f"Number of locations: {len(location_identifiers)}")
print(f"Date range: {start_dates[0]} to {start_dates[-1]}")


for location in location_identifiers:
    for start_date in start_dates:
        # Construct start and end datetime strings
        start = f"{start_date}T00:00:00"
        end = f"{start_date}T23:59:59"

        payload = {
            "locationIdentifier": location,
            "start": start,
            "end": end,
            "binSize": "15",
            "showPlanStatistics": True,
            "showVolumes": True,
            "showArrivalsOnGreen": True
        }

        # Convert the payload to a JSON string
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Connect to SQLite database
            conn = sqlite3.connect('data/purdue_coordination_diagram.db', detect_types=sqlite3.PARSE_DECLTYPES)
            cursor = conn.cursor()
            
            # Create tables with primary keys (if they don't exist)
            cursor.execute('''CREATE TABLE IF NOT EXISTS phases
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 phase_number INTEGER,
                 phase_description TEXT,
                 location_identifier TEXT,
                 location_description TEXT,
                 total_on_green_events INTEGER,
                 total_detector_hits INTEGER,
                 percent_arrival_on_green REAL,
                 date DATE,
                 UNIQUE(phase_number, location_identifier, date))''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS plans
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 phase_id INTEGER,
                 location_identifier TEXT,
                 percent_green_time REAL,
                 percent_arrival_on_green REAL,
                 platoon_ratio REAL,
                 plan_number INTEGER,
                 start DATETIME,
                 end DATETIME,
                 plan_description TEXT,
                 FOREIGN KEY(phase_id) REFERENCES phases(phase_number))''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS volume_per_hour
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 phase_id INTEGER,
                 location_identifier TEXT,
                 value INTEGER,
                 timestamp DATETIME,
                 FOREIGN KEY(phase_id) REFERENCES phases(phase_number))''')

            # Insert data (reuse your existing insertion code here)
            for phase in data:
                cursor.execute('''INSERT OR IGNORE INTO phases 
                    (phase_number, phase_description, location_identifier, location_description, 
                    total_on_green_events, total_detector_hits, percent_arrival_on_green, date) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (phase['phaseNumber'], phase['phaseDescription'], location, phase['locationDescription'],
                    phase['totalOnGreenEvents'], phase['totalDetectorHits'], phase['percentArrivalOnGreen'], 
                    datetime.strptime(phase['plans'][0]['start'], '%Y-%m-%dT%H:%M:%S').date()))
                
                phase_id = phase['phaseNumber']

                for plan in phase['plans']:
                    cursor.execute('''INSERT OR IGNORE INTO plans 
                        (phase_id, location_identifier, percent_green_time, percent_arrival_on_green, platoon_ratio, plan_number, start, end, plan_description) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (phase_id, location, plan['percentGreenTime'], plan['percentArrivalOnGreen'], plan['platoonRatio'],
                        plan['planNumber'], plan['start'], plan['end'], plan['planDescription']))

                for volume in phase['volumePerHour']:
                    cursor.execute('''INSERT OR IGNORE INTO volume_per_hour 
                        (phase_id, location_identifier, value, timestamp) 
                        VALUES (?, ?, ?, ?)''',
                        (phase_id, location, volume['value'], volume['timestamp']))

            conn.commit()
            conn.close()
            
            print(f"Data for location {location} on {start_date} successfully stored in the database.")
        else:
            print(f"Request failed for location {location} on {start_date} with status code {response.status_code}")























