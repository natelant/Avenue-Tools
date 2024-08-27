import requests
import json
import sqlite3
from datetime import datetime

# Replace with the URL you found in the developer console
url = 'https://report-api-bdppc3riba-wm.a.run.app/v1/PurdueCoordinationDiagram/GetReportData'

# If there are any specific headers, like authorization tokens, add them here
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    # Add other headers you might need
}

# If it's a POST request, include the data or payload
payload = {
    "locationIdentifier": "7157",
    "start": "2024-08-21T00:00:00",
    "end": "2024-08-21T23:59:00",
    "binSize": "15",
    "showPlanStatistics": True,  # Use True/False instead of 'true'/'false'
    "showVolumes": True,
    "showArrivalsOnGreen": True
}

# Convert the payload to a JSON string
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Assuming the response is JSON
    
    # Save data as JSON file
    with open('purdue_coordination_data.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print("Data successfully saved as JSON file.")

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('purdue_coordination_diagram.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS phases (
        phase_number INTEGER PRIMARY KEY,
        phase_description TEXT,
        total_on_green_events INTEGER,
        total_detector_hits INTEGER,
        percent_arrival_on_green INTEGER,
        date DATE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase_id INTEGER,
        percent_green_time INTEGER,
        percent_arrival_on_green INTEGER,
        platoon_ratio REAL,
        plan_number TEXT,
        start DATETIME,
        end DATETIME,
        plan_description TEXT,
        FOREIGN KEY (phase_id) REFERENCES phases(phase_number)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS volume_per_hour (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase_id INTEGER,
        value INTEGER,
        timestamp DATETIME,
        FOREIGN KEY (phase_id) REFERENCES phases(phase_number)
    )''')

    # Insert data
    for phase in data:
        cursor.execute('''INSERT OR REPLACE INTO phases 
            (phase_number, phase_description, total_on_green_events, total_detector_hits, percent_arrival_on_green, date) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (phase['phaseNumber'], phase['phaseDescription'], phase['totalOnGreenEvents'],
            phase['totalDetectorHits'], phase['percentArrivalOnGreen'], 
            datetime.strptime(phase['plans'][0]['start'], '%Y-%m-%dT%H:%M:%S').date()))
        
        phase_id = phase['phaseNumber']

        for plan in phase['plans']:
            cursor.execute('''INSERT INTO plans 
                (phase_id, percent_green_time, percent_arrival_on_green, platoon_ratio, plan_number, start, end, plan_description) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (phase_id, plan['percentGreenTime'], plan['percentArrivalOnGreen'], plan['platoonRatio'],
                plan['planNumber'], plan['start'], plan['end'], plan['planDescription']))

        for volume in phase['volumePerHour']:
            cursor.execute('''INSERT INTO volume_per_hour 
                (phase_id, value, timestamp) 
                VALUES (?, ?, ?)''',
                (phase_id, volume['value'], volume['timestamp']))

    conn.commit()
    conn.close()
    
    print("Data successfully stored in the database.")
else:
    print(f"Request failed with status code {response.status_code}")























