import requests
from bs4 import BeautifulSoup
import sqlite3  # No need to install, part of Python standard library

intersection_ids = ['7164', '7163']  # Example list of intersection IDs


# Fetch the web page
url = 'https://udottraffic.utah.gov/ATSPM/Signals/SignalDetail'

# Example function to fetch data for a given intersection ID
def fetch_intersection_data(intersection_id):
    payload = {'intersection_id': intersection_id}
    response = requests.post(url, data=payload)
    return response.text


# Function to parse HTML and extract table data
def parse_table_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    table_data = []
    for table in tables:
        headers = [th.text.strip() for th in table.find_all('th')]
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            if cols:  # Ensure it's not an empty row
                table_data.append(dict(zip(headers, cols)))
    return table_data

# Fetch and parse data for each intersection ID
for intersection_id in intersection_ids:
    html_content = fetch_intersection_data(intersection_id)
    table_data = parse_table_data(html_content)
    print(f"Data for intersection ID {intersection_id}:")
    for row in table_data:
        print(row)
        

