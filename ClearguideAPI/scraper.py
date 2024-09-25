import requests
from bs4 import BeautifulSoup

# URL of the website
url = "https://ut.iteris-clearguide.com/reports"

# Send a GET request to the URL
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find the table (you'll need to specify the correct selector)
table = soup.find('table', {'id': 'your-table-id'})

# Extract data from the table
if table:
    # Extract headers
    headers = [th.text.strip() for th in table.find_all('th')]
    print("Headers:", headers)
    
    # Extract rows
    for row in table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        row_data = [column.text.strip() for column in columns]
        print(row_data)
else:
    print("Table not found")
