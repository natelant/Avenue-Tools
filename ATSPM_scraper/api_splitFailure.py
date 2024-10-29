import requests
import json
import sqlite3
from datetime import datetime, date
import pandas as pd
from datetime import timedelta

# Add this function at the beginning of your script
def adapt_date(val):
    return val.isoformat()

# Register the adapter
sqlite3.register_adapter(date, adapt_date)

# Replace with the actual URL for the split failure API
url = 'https://report-api-bdppc3riba-wm.a.run.app/v1/SplitFail/GetReportData'

# If there are any specific headers, like authorization tokens, add them here
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    # Add other headers you might need
    'Origin': 'https://atspm-website-bdppc3riba-wm.a.run.app',
    'Referer': 'https://atspm-website-bdppc3riba-wm.a.run.app/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"'
}

# Read location identifiers from signals.csv
signals_df = pd.read_csv('data/signals.csv')
location_identifiers = signals_df['Signal_ID'].astype(str).tolist()

# Create a date range for start dates
start_date = datetime(2024, 10, 10)  # Adjust this to your desired start date
end_date = datetime(2024, 10, 23)  # Adjust this to your desired end date
date_range = pd.date_range(start=start_date, end=end_date, freq='D')

print(f"Number of locations: {len(location_identifiers)}")
print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

for location in location_identifiers:
    for date in date_range:
        # Construct start and end datetime strings
        start = date.strftime('%Y-%m-%dT00:00:00')
        end = (date + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')

        # Payload for the request
        payload = {
            "locationIdentifier": location,
            "start": start,
            "end": end,
            "firstSecondsOfRed": "5",
            "showAvgLines": True,
            "showFailLines": True,
            "showPercentFailLines": False
        }

        # Make the API request
        response = requests.post(url, headers=headers, json=payload)

        # Check the status code and content
        if response.status_code == 200:
            try:
                data = response.json()
                # Connect to SQLite database
                conn = sqlite3.connect('data/split_failure.db', detect_types=sqlite3.PARSE_DECLTYPES)
                cursor = conn.cursor()

                # Create tables
                cursor.execute('''CREATE TABLE IF NOT EXISTS phases
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     phase_number INTEGER,
                     phase_type TEXT,
                     total_split_fails INTEGER,
                     approach_id INTEGER,
                     approach_description TEXT,
                     location_identifier TEXT,
                     location_description TEXT,
                     date DATE,
                     UNIQUE(phase_number, location_identifier, date))''')

                cursor.execute('''CREATE TABLE IF NOT EXISTS plans
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     phase_id INTEGER,
                     location_identifier TEXT,
                     total_cycles INTEGER,
                     fails_in_plan INTEGER,
                     percent_fails REAL,
                     plan_number TEXT,
                     start DATETIME,
                     end DATETIME,
                     plan_description TEXT,
                     FOREIGN KEY(phase_id) REFERENCES phases(id))''')

                cursor.execute('''CREATE TABLE IF NOT EXISTS occupancy_data
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     phase_id INTEGER,
                     location_identifier TEXT,
                     data_type TEXT,
                     value REAL,
                     timestamp DATETIME,
                     FOREIGN KEY(phase_id) REFERENCES phases(id))''')

                # Insert data
                for phase in data:
                    cursor.execute('''INSERT OR REPLACE INTO phases 
                        (phase_number, phase_type, total_split_fails, approach_id, approach_description, 
                        location_identifier, location_description, date) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (phase['phaseNumber'], phase['phaseType'], phase['totalSplitFails'],
                         phase['approachId'], phase['approachDescription'], phase['locationIdentifier'],
                         phase['locationDescription'], datetime.strptime(phase['start'], '%Y-%m-%dT%H:%M:%S').date()))
                
                    phase_id = cursor.lastrowid

                    for plan in phase['plans']:
                        cursor.execute('''INSERT INTO plans 
                            (phase_id, location_identifier, total_cycles, fails_in_plan, percent_fails, plan_number, start, end, plan_description) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (phase_id, phase['locationIdentifier'], plan['totalCycles'], plan['failsInPlan'], plan['percentFails'],
                             plan['planNumber'], plan['start'], plan['end'], plan['planDescription']))

                    for data_type in ['gapOutGreenOccupancies', 'gapOutRedOccupancies', 'forceOffGreenOccupancies', 'forceOffRedOccupancies', 'averageGor', 'averageRor', 'percentFails']:
                        for item in phase[data_type]:
                            cursor.execute('''INSERT INTO occupancy_data 
                                (phase_id, location_identifier, data_type, value, timestamp) 
                                VALUES (?, ?, ?, ?, ?)''',
                                (phase_id, phase['locationIdentifier'], data_type, item['value'], item['timestamp']))

                conn.commit()
                conn.close()

                print(f"Data for location {location} on {date.strftime('%Y-%m-%d')} successfully stored in the database.")
            except requests.exceptions.JSONDecodeError as e:
                print(f"Error decoding JSON for location {location} on {date.strftime('%Y-%m-%d')}: {e}")
        else:
            print(f"Request failed for location {location} on {date.strftime('%Y-%m-%d')} with status code {response.status_code}")
