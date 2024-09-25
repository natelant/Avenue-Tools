import datetime
import psycopg2
from psycopg2 import extras
from apiexample00 import ClearGuideApiHandler


# Define the API parameters
API_URL = 'https://api.iteris-clearguide.com/v1/route/timeseries/'
CUSTOMER_KEY = 'ut'
ROUTE_ID_TYPE = 'customer_route_number'
START_TIMESTAMP = 1641020400    # unix timestamp start in local time
END_TIMESTAMP = 1672556399      # unix timestamp end in local time
INTERVAL = 2630000                 # one month
METRIC = 'avg_speed'
GRANULARITY = '5min'
INCLUDE_HOLIDAYS = 'true'

# Define the list of route IDs to query
route_ids = [7877,
7876,
7875,
7874,
7873,
7872,
7871,
7870,
7869,
7868,
7867,
7865,
7864,
7863,
7862,
7861,
7860,
7859,
7858,
7857,
7856,
]

# Open a PostgreSQL connection
conn = psycopg2.connect(
    host='esrisql01',
    database='safety_dashboard',
    user='mstanley',
    password='msAVE#2022'
)

cg_api_handler = ClearGuideApiHandler(username='slarson@avenueconsultants.com', password='Toad22#24#14')

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