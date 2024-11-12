import datetime
from examples.apiexample01 import ClearGuideApiHandler
import json
from datetime import datetime, timezone
import csv
import pandas as pd  
import matplotlib.pyplot as plt
import seaborn as sns
from pykml import parser
import numpy as np
from geopy.distance import geodesic
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Define the list of route IDs to query
# State Street 6100 S to Williams = [9946, 9947]
# State Street 11400 S to 9000 S = [13236, 13237]
route_ids = [13236, 13237]
route_name = 'Pattern 22 - State St (11400 S to 9000 S)'

# User input to determine the direction of the routes
NB = 13237
SB = 13236
EB = np.nan
WB = np.nan

# Read KML file (replace with your actual KML file path)
kml_file_path = 'kml/State Street (9000 South to 11400 South).kml'

# Data download window (YYYY-MM-DD HH:MM:SS)
start_datetime_str = "2024-09-1 00:00:00"
end_datetime_str = "2024-10-31 23:59:59"

# Define the comparisonwindow date thresholds (you should set these as input parameters)
before_start = datetime(2024, 9, 1, 0, 0, 0)
before_end = datetime(2024, 9, 30, 23, 59, 59)
after_start = datetime(2024, 10, 16, 0, 0, 0)
after_end = datetime(2024, 10, 31, 23, 59, 59)

# Hardcoded username and password
username = 'dbassett@avenueconsultants.com'
password = 'The$onofman1'
#-------------------------------------------------------------------------
def parse_json_response(response, route_id):
    csv_data = []
    
    # Extract the data array
    data_array = response['series']['all']['avg_speed']['data']
    
    for entry in data_array:
        timestamp = entry[0]  # Unix timestamp
        measurements = entry[1]
        
        for measurement in measurements:
            distance = measurement[0]
            speed = measurement[1]
            
            # Convert Unix timestamp to datetime
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            
            csv_data.append([route_id, formatted_time, distance, speed])
    
    return csv_data

def calculate_distances(intersections, direction):
    if direction in ['Northbound', 'Eastbound']:
        start_point = intersections[-1]  # Last intersection (northernmost or easternmost)
    else:
        start_point = intersections[0]  # First intersection (southernmost or westernmost)
    
    distances = []
    for intersection in intersections:
        distance_miles = geodesic((start_point[1], start_point[2]), (intersection[1], intersection[2])).miles
        distances.append((intersection[0], round(distance_miles, 2)))
    
    return distances

# Read in a KML file for the y axis of the heatmap
def read_kml_intersections(kml_file_path):
    with open(kml_file_path, 'rb') as kml_file:
        root = parser.parse(kml_file).getroot()
        placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
        intersections = []
        for placemark in placemarks:
            name = placemark.find('{http://www.opengis.net/kml/2.2}name').text
            coordinates = placemark.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.split(',')
            lat, lon = float(coordinates[1]), float(coordinates[0])
            intersections.append((name, lat, lon))
    return intersections


#------------------------------------------------------------------------


# Convert to datetime objects
start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M:%S")

# Define the API parameters
API_URL = 'https://api.iteris-clearguide.com/v1/route/spatial/contours/'
CUSTOMER_KEY = 'ut'
ROUTE_ID_TYPE = 'customer_route_number'
# Convert to Unix timestamps (seconds since epoch)
START_TIMESTAMP = int(start_datetime.replace(tzinfo=timezone.utc).timestamp())
END_TIMESTAMP = int(end_datetime.replace(tzinfo=timezone.utc).timestamp())
METRIC = 'avg_speed'
DOWS = 'sat' #'mon,tue,wed,thu'
GRANULARITY = 'hour'
INCLUDE_HOLIDAYS = 'false'

cg_api_handler = ClearGuideApiHandler(username=username, password=password)

all_parsed_data = []  # List to store parsed data for all routes

try:
    for route_id in route_ids:
        query = f'{API_URL}?customer_key={CUSTOMER_KEY}&route_id={route_id}&route_id_type={ROUTE_ID_TYPE}&s_timestamp={START_TIMESTAMP}&e_timestamp={END_TIMESTAMP}&metrics={METRIC}&holidays={INCLUDE_HOLIDAYS}&granularity={GRANULARITY}'
        
        print(f"Constructed URL: {query}")
        
        response = cg_api_handler.call(url=query)
        
        if 'error' in response and response['error']:
            raise Exception(f"Error fetching response for route_id {route_id}... Message: {response.get('msg', 'No message provided')}")
        
        # Write the response to a JSON file
        json_filename = f'response_{route_id}.json'
        with open(json_filename, 'w') as json_file:
            json.dump(response, json_file, indent=4)
        
        print(f"Response for route_id {route_id} written to {json_filename}")
        
        # Parse JSON response
        parsed_data = parse_json_response(response, route_id)
        all_parsed_data.extend(parsed_data)
    
    # Create a single dataframe from all parsed data
    columns = ['route_id', 'timestamp', 'distance', 'speed']
    total_df = pd.DataFrame(all_parsed_data, columns=columns)
    
    # Save the total dataframe to sheet 1 of an Excel file
    excel_filename = f'contours_raw_{route_name}.xlsx'
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        total_df.to_excel(writer, sheet_name='Sheet1', index=False)
    print(f"Total parsed data saved to {excel_filename}, Sheet1")

except Exception as e:
    print(f"An error occurred: {e}")


#-------------------------------------------------------------------------
# Analysis 
# Group by route_id, hour, and binned_distance, then calculate average speed and calculate the speed difference

# Load the CSV data into a pandas DataFrame
df = total_df

# Convert the 'timestamp' column to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')



# Create a function to bin distances
def bin_distance(distance):
    return round(distance, 2)  # Round to 2 decimal places for binning

# Add hour and binned distance columns
df['hour'] = df['timestamp'].dt.hour
df['dow'] = df['timestamp'].dt.dayofweek
df['binned_distance'] = df['distance'].apply(bin_distance)

# filter out fridays and saturdays and sundays
df = df[df['dow'] != 0]
df = df[df['dow'] != 1]
df = df[df['dow'] != 2]
df = df[df['dow'] != 3]
df = df[df['dow'] != 4]
# df = df[df['dow'] != 5]
df = df[df['dow'] != 6]

# Filter data for before and after windows
before_df = df[(df['timestamp'] >= before_start) & (df['timestamp'] <= before_end)]
after_df = df[(df['timestamp'] >= after_start) & (df['timestamp'] <= after_end)]

# Group by route_id, hour, and binned_distance, then calculate average speed
before_grouped = before_df.groupby(['route_id', 'hour', 'binned_distance'])['speed'].mean().reset_index()
after_grouped = after_df.groupby(['route_id', 'hour', 'binned_distance'])['speed'].mean().reset_index()

# Rename speed columns
before_grouped = before_grouped.rename(columns={'speed': 'before_speed'})
after_grouped = after_grouped.rename(columns={'speed': 'after_speed'})

# Merge before and after data
merged_df = pd.merge(before_grouped, after_grouped, on=['route_id', 'hour', 'binned_distance'], how='outer')

# Calculate the speed difference
merged_df['speed_difference'] = merged_df['after_speed'] - merged_df['before_speed']

# Sort the results
result_df = merged_df.sort_values(['route_id', 'hour', 'binned_distance'])

# Write the results to sheet 2 of the same Excel file
with pd.ExcelWriter(excel_filename, engine='openpyxl', mode='a') as writer:
    result_df.to_excel(writer, sheet_name='Sheet2', index=False)
print(f"Analysis results saved to {excel_filename}, Sheet2")

# Display the results
print(result_df)

#-------------------------------------------------------------------------
# Plotting the speed difference in a heatmap using Plotly
intersections = read_kml_intersections(kml_file_path)

# Create a dictionary to map route_id to direction
route_direction = {NB: 'Northbound', SB: 'Southbound', EB: 'Eastbound', WB: 'Westbound'}

# Prepare data for heatmap
for route_id in [NB, SB, EB, WB]:
    route_data = result_df[result_df['route_id'] == route_id]
    direction = route_direction[route_id]
    
    # Calculate distances based on direction
    intersection_distances = calculate_distances(intersections, direction)
    
    # Create a pivot table for the heatmap
    pivot_data = route_data.pivot(index='binned_distance', columns='hour', values='speed_difference')
    
    # Sort the pivot_data index to ensure it's in ascending order
    pivot_data = pivot_data.sort_index()
    
    # Prepare y-axis labels
    y_ticks = [dist for _, dist in intersection_distances]
    y_labels = [f"{name} ({dist:.2f} mi)" for name, dist in intersection_distances]
    
    # Create the heatmap using Plotly
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlGn',
        zmid=0,
        colorbar=dict(title='Speed Difference (mph)')
    ))

    # Update layout
    fig.update_layout(
        title=f"Speed Difference Heatmap - {direction}",
        xaxis_title="Hour of Day",
        yaxis_title="Distance (miles)",
        height=1000,  # Adjust the height as needed
        width=2000,    # Adjust the width as needed
    )

    # Customize y-axis ticks and labels
    fig.update_yaxes(
        tickmode='array',
        tickvals=y_ticks,
        ticktext=y_labels,
        autorange='reversed'  # This inverts the y-axis
    )

    # Save the plot as an interactive HTML file
    fig.write_html(f'heatmap_{route_name}_{route_direction[route_id]}.html')
    
    # Optionally, you can also save as a static image
    fig.write_image(f'heatmap_{route_name}_{route_direction[route_id]}.png', scale=2)

print("Plotly heatmaps have been generated and saved.")

#-------------------------------------------------------------------------
# Calculate the average speed between intersections for each time period and write to the excel file


