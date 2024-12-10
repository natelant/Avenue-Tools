import aiohttp
import asyncio
import json
import sqlite3
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
import time as time_module  # Rename the import to avoid conflicts

# Add this function at the beginning of your script
def adapt_date(val):
    return val.isoformat()

# Register the adapter
sqlite3.register_adapter(date, adapt_date)

# Replace with the URL you found in the developer console
url = 'https://udottraffic.utah.gov/ATSPM/DefaultCharts/GetTMCMetric'

# If there are any specific headers, like authorization tokens, add them here
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://udottraffic.utah.gov',
    'Referer': 'https://udottraffic.utah.gov/atspm/',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

# Define intersection IDs and date range
# intersection_ids = ['6035', '6038', '6039']
# start_date = datetime(2023, 3, 1)
# end_date = datetime(2024, 8, 17)
# current_date = start_date

async def fetch_data(session, intersection_id, date_str):
    payload = {
        "SignalID": intersection_id,
        "StartDate": f"{date_str} 12:00 AM",
        "EndDate": f"{date_str} 11:59 PM",
        "YAxisMax": "1000",
        "Y2AxisMax": "300",
        "MetricTypeID": 5,
        "SelectedBinSize": "60",
        "ShowLaneVolumes": True,
        "ShowTotalVolumes": True,
        "ShowDataTable": True
    }

    max_retries = 6
    retry_delay = 30

    for attempt in range(max_retries):
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    content = await response.text()
                    error_messages = [
                        "Object reference not set to an instance of an object",
                        "An error occurred while executing the command definition",
                        "The underlying provider failed on Open",
                        "Invalid attempt to read when no data is present"
                    ]
                    for error in error_messages:
                        if error in content:
                            error_message = f"Error message received for intersection {intersection_id} on {date_str}: {error}. Retrying... (Attempt {attempt + 1}/{max_retries})"
                            print(error_message)
                            with open('data/error_messages.txt', 'a') as error_file:
                                error_file.write(f"{error_message}\n")
                            await asyncio.sleep(retry_delay)
                            break
                    else:
                        return content
                    continue
                else:
                    print(f"Request failed for intersection {intersection_id} on {date_str} with status code {response.status}. Retrying... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
        except aiohttp.ClientError as e:
            print(f"Request error for intersection {intersection_id} on {date_str}: {e}. Retrying... (Attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(retry_delay)
    
    print(f"Failed to get a successful response after {max_retries} attempts")
    return None

def parse_data(html_content, intersection_id, date_str):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='table table-bordered table-striped table-condensed')
    
    if not table:
        error_message = f"Error: No table found for intersection {intersection_id} on {date_str}. Response content: {html_content[:200]}..."
        print(error_message)
        with open('data/error_messages.txt', 'a') as error_file:
            error_file.write(error_message + "\n")
        return []

    data = []
    rows = table.find_all('tr')[3:]  # Skip header rows
    for row in rows[:-1]:  # Exclude the last row (Total)
        cells = row.find_all('td')
        time = cells[0].text.strip()
        
        cell_index = 1
        for direction in ['Eastbound', 'Westbound', 'Northbound', 'Southbound']:
            movements = ['L', 'T', 'R']
            for movement in movements:
                if cell_index < len(cells) and not cells[cell_index].has_attr('class'):
                    volume = int(cells[cell_index].text.strip())
                    data.append((intersection_id, date_str, time, direction, movement, volume))
                    cell_index += 1
                else:
                    # Skip the movement if it's missing or if it's a total column
                    with open('data/warning_messages.txt', 'a') as warning_file:
                        warning_message = f"Warning: Missing data for {direction} {movement} at {time} for intersection {intersection_id} on {date_str}\n"
                        warning_file.write(warning_message)
                        print(warning_message.strip())
            
            # Skip the total column for each direction
            cell_index += 1
    
    return data

async def process_date(session, date, intersection_ids):
    date_str = date.strftime("%m/%d/%Y")
    tasks = [fetch_data(session, intersection_id, date_str) for intersection_id in intersection_ids]
    results = await asyncio.gather(*tasks)
    
    all_data = []
    for intersection_id, html_content in zip(intersection_ids, results):
        if html_content:
            all_data.extend(parse_data(html_content, intersection_id, date_str))
    
    return all_data

def insert_batch(conn, data):
    cursor = conn.cursor()
    cursor.executemany('''INSERT INTO tmc_data_detailed 
                          (intersection_id, date, time, direction, movement, volume) 
                          VALUES (?, ?, ?, ?, ?, ?)''', data)
    conn.commit()

async def main():
    # lower state st = ['7174', '7643', '7175', '7640', '7176', '7352', '7177', '7178', '7179', '7353', '7351'] 
    # SR 209 (9000 S) = ['7522', '7521', '7386', '7423', '7422', '7421', '7067']
    # SR 48 (7800 S) = ['7066', '7354', '7012', '7011', '7010', '7116']
    intersection_ids = ['6226'] 
    start_date = datetime(2022, 12, 1)
    end_date = datetime(2024, 12, 1)
    current_date = start_date

    conn = sqlite3.connect('data/PaysonMOT_6226_TMC.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tmc_data_detailed
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       intersection_id TEXT,
                       date DATE,
                       time TEXT,
                       direction TEXT,
                       movement TEXT,
                       volume INTEGER)''')
    conn.commit()

    async with aiohttp.ClientSession(headers=headers) as session:
        while current_date <= end_date:
            data = await process_date(session, current_date, intersection_ids)
            insert_batch(conn, data)
            print(f"Data for {current_date.date()} processed and stored.")
            current_date += timedelta(days=1)

    conn.close()

if __name__ == "__main__":
    asyncio.run(main())

