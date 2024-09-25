import datetime
import sqlite3
from apiexample01 import ClearGuideApiHandler
import json


# Define the API parameters
API_URL = 'https://api.iteris-clearguide.com/v1/route/spatial/contours/'
CUSTOMER_KEY = 'ut'
ROUTE_ID_TYPE = 'customer_route_number'
START_TIMESTAMP = 	1726812000    # unix timestamp start in local time
END_TIMESTAMP = 	1726984800      # unix timestamp end in local time
METRIC = 'avg_speed'
DOWS = 'mon,tue,wed,thu'
GRANULARITY = 'hour'
INCLUDE_HOLIDAYS = 'false'

# Define the list of route IDs to query
route_ids = [9947]

# Open an SQLite connection
conn = sqlite3.connect('speed_data_api.db')

# Hardcoded username and password
username = 'dbassett@avenueconsultants.com'
password = 'The$onofman1'

cg_api_handler = ClearGuideApiHandler(username=username, password=password)

try:
    with conn:
        cur = conn.cursor()
        # Create table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS avg_speed (
                route_id INTEGER,
                timestamp DATETIME,
                avg_speed REAL
            )
        ''')
        
        for route_id in route_ids:
            query = f'{API_URL}?customer_key={CUSTOMER_KEY}&route_id={route_id}&route_id_type={ROUTE_ID_TYPE}&s_timestamp={START_TIMESTAMP}&e_timestamp={END_TIMESTAMP}&metrics={METRIC}&holidays={INCLUDE_HOLIDAYS}&granularity={GRANULARITY}'
            
            # Print the constructed URL for debugging
            print(f"Constructed URL: {query}")
            
            response = cg_api_handler.call(url=query)
            
            # Check for errors in the response
            if 'error' in response and response['error']:
                raise Exception(f"Error fetching response from ClearGuide... Message: {response.get('msg', 'No message provided')}")
            
            # Write the response to a JSON file
            with open(f'response_{route_id}.json', 'w') as json_file:
                json.dump(response, json_file, indent=4)
            
            print(f"Response for route_id {route_id} written to response_{route_id}.json")
            
            data = response['series']['all']['avg_speed']['data']
            
            # Ensure data is in the correct format
            inserts = []
            for d in data:
                if isinstance(d, list) and len(d) == 2:
                    timestamp = datetime.datetime.fromtimestamp(d[0])
                    avg_speed = d[1]
                    if isinstance(avg_speed, (int, float)):  # Ensure avg_speed is a number
                        inserts.append((route_id, timestamp, avg_speed))
                    else:
                        print(f"Skipping invalid avg_speed value: {avg_speed}")
                else:
                    print(f"Skipping invalid data entry: {d}")
            
            cur.executemany("INSERT INTO avg_speed (route_id, timestamp, avg_speed) VALUES (?, ?, ?)", inserts)
            
            conn.commit()
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()