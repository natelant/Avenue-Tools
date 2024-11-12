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
start_date = datetime(2024, 10, 29)  # Adjust this to your desired start date
end_date = datetime(2024, 11, 10)  # Adjust this to your desired end date
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

                # Create plans table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plans (
                        locationIdentifier TEXT,
                        locationDescription TEXT,
                        phaseNumber TEXT,
                        approachDescription TEXT,
                        planNumber TEXT,
                        planDescription TEXT,
                        start TIMESTAMP,
                        end TIMESTAMP,
                        totalCycles REAL,
                        failsInPlan REAL,
                        percentFails REAL
                    )
                ''')

                # Insert data
                for phase in data:
                    for plan in phase['plans']:
                        cursor.execute('''INSERT INTO plans 
                            (locationIdentifier, locationDescription, phaseNumber, approachDescription, 
                             planNumber, planDescription, start, end, totalCycles, failsInPlan, percentFails) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (phase['locationIdentifier'], 
                             phase.get('locationDescription', ''),
                             phase['phaseNumber'], 
                             phase.get('approachDescription', ''),
                             plan['planNumber'], 
                             plan['planDescription'], 
                             plan['start'], 
                             plan['end'], 
                             plan['totalCycles'],
                             plan['failsInPlan'],
                             plan['percentFails']))

                conn.commit()
                conn.close()

                print(f"Data for location {location} on {date.strftime('%Y-%m-%d')} successfully stored in the database.")
            except requests.exceptions.JSONDecodeError as e:
                print(f"Error decoding JSON for location {location} on {date.strftime('%Y-%m-%d')}: {e}")
        else:
            print(f"Request failed for location {location} on {date.strftime('%Y-%m-%d')} with status code {response.status_code}")
