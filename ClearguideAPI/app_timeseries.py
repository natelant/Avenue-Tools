import datetime
import psycopg2
from psycopg2 import extras
from examples.apiexample00 import ClearGuideApiHandler
import sqlite3


# Define the API parameters
API_URL = 'https://api.iteris-clearguide.com/v1/route/timeseries/'
CUSTOMER_KEY = 'ut'
ROUTE_ID_TYPE = 'customer_route_number'
START_TIMESTAMP = 	1726812000    # unix timestamp start in local time
END_TIMESTAMP = 	1726984800      # unix timestamp end in local time
INTERVAL = 86400                 # one day
METRIC = 'avg_speed'
GRANULARITY = '5min'
INCLUDE_HOLIDAYS = 'true'

# Define the list of route IDs to query
route_ids = [9946, 9947]

# Open a PostgreSQL connection
conn = sqlite3.connect('timeseries_data.db') 

cg_api_handler = ClearGuideApiHandler(username='dbassett@avenueconsultants.com', password='The$onofman1') 
# also try with username='dbassett@avenueconsultants.com', password='The$onofman1'

try:
    with conn:
        cur = conn.cursor()

        # Create the table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS avg_speed (
                route_id INTEGER,
                timestamp DATETIME,
                avg_speed REAL
            )
        ''')

        for route_id in route_ids:
            # while START_TIMESTAMP < END_TIMESTAMP:
            #     if START_TIMESTAMP + INTERVAL > END_TIMESTAMP:
            #         REQUEST_END_TIMESTAMP = END_TIMESTAMP
            #     else:
            #         REQUEST_END_TIMESTAMP = START_TIMESTAMP + INTERVAL
                query = f'https://api.iteris-clearguide.com/v1/route/timeseries/?customer_key={CUSTOMER_KEY}&route_id={route_id}&route_id_type={ROUTE_ID_TYPE}&s_timestamp={START_TIMESTAMP}&e_timestamp={END_TIMESTAMP}&metrics={METRIC}&holidays={INCLUDE_HOLIDAYS}&granularity={GRANULARITY}'
                response = cg_api_handler.call(url=query)
                data = response['series']['all']['avg_speed']['data']
                inserts = [(route_id, datetime.datetime.fromtimestamp(d[0]), d[1]) for d in data]
                
                for insert in inserts:
                    cur.execute("INSERT INTO avg_speed (route_id, timestamp, avg_speed) VALUES (?, ?, ?)", insert)
                
                conn.commit()
                # START_TIMESTAMP += INTERVAL + 300 # next 5min interval
finally:
    conn.close()