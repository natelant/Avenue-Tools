# this is my first draft at creating a contour speed map using GPX files
# this file should read in a KML and as many GPX files as possible (from various cars doing observations)
# then the file outputs a speed contour (sort of) chart where x axis is time of day and y axis is intersections on the corridor
# color will represent speed, so that stops are easy to identify

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import xml.etree.ElementTree as ET
from datetime import datetime
import geopandas as gpd
import numpy as np
import mplcursors
import plotly.express as px
import plotly.graph_objects as go
import pytz
import folium

# Define Salt Lake City's timezone
LOCAL_TZ = pytz.timezone('America/Denver')


# Function to parse GPX file and calculate speed
def parse_gpx(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespaces = {
        'gpx': 'http://www.topografix.com/GPX/1/1'
    }
    
    data = []
    previous_point = None
    previous_time = None
    
    for trkpt in root.findall('.//gpx:trkpt', namespaces):
        timestamp = trkpt.find('gpx:time', namespaces).text
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        
        # Handle different timestamp formats
        try:
            time_of_day_utc = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            time_of_day_utc = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
        
        # Convert UTC time to local time
        time_of_day_local = time_of_day_utc.replace(tzinfo=pytz.utc).astimezone(LOCAL_TZ)
        
        if previous_point is not None and previous_time is not None:
            distance = haversine(previous_point[0], previous_point[1], lat, lon)
            time_diff = (time_of_day_local - previous_time).total_seconds() / 3600.0  # time difference in hours
            speed = distance / time_diff if time_diff != 0 else 0
        else:
            speed = 0.0
        
        data.append([time_of_day_local.strftime('%H:%M:%S'), lat, lon, speed])
        previous_point = (lat, lon)
        previous_time = time_of_day_local
    
    df = pd.DataFrame(data, columns=['TimeOfDay', 'Latitude', 'Longitude', 'Speed'])

    bins = [-float('inf'), 3, 15, 30, float('inf')]
    labels = ['Below 3 mph', '3-15 mph', '15-30 mph', 'Above 30 mph']
    df['SpeedCategory'] = pd.cut(df['Speed'], bins=bins, labels=labels)

    # Ensure 'SpeedCategory' is an ordered categorical type
    speed_category_order = ['Below 3 mph', '3-15 mph', '15-30 mph', 'Above 30 mph']
    df['SpeedCategory'] = pd.Categorical(df['SpeedCategory'], categories=speed_category_order, ordered=True)


    return df

# Haversine formula to calculate distance between two points on Earth
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0*0.621371 # Earth radius in (kilometers * 1 mile / 1 kilometer) = miles
    
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c  # in miles
    return distance

# Function to parse KML file
def parse_kml(file_path):
    gdf = gpd.read_file(file_path, driver='KML')
    key_intersections = gdf[['geometry', 'Name']].copy()
    key_intersections['Longitude'] = key_intersections['geometry'].x
    key_intersections['Latitude'] = key_intersections['geometry'].y
    key_intersections['Intersection'] = range(len(key_intersections))
    return key_intersections

# Function to map lat/lon to intersections
def map_to_intersections(df, key_intersections, direction):
    # Create dictionaries to map intersection names to latitude and longitude values
    intersection_to_lat = key_intersections.set_index('Name')['Latitude'].to_dict()
    intersection_to_lon = key_intersections.set_index('Name')['Longitude'].to_dict()

    def get_nearest_intersection(lat, lon):
        min_distance = float('inf')
        nearest_intersection = None
        for _, row in key_intersections.iterrows():
            dist = haversine(lat, lon, row.geometry.y, row.geometry.x)
            if dist < min_distance:
                min_distance = dist
                nearest_intersection = row['Intersection']
        return nearest_intersection
    
    df['Intersection'] = df.apply(lambda row: get_nearest_intersection(row['Latitude'], row['Longitude']), axis=1)
    df = df.merge(key_intersections[['Intersection', 'Name']], on='Intersection', how='left')

    # Map intersection names to latitudes and longitudes
    df['LatitudeForPlot'] = df['Name'].map(intersection_to_lat)
    df['LongitudeForPlot'] = df['Name'].map(intersection_to_lon)
    
    return df, intersection_to_lat if direction == 'NS' else intersection_to_lon

def make_time_plot(data, intersection_coords, direction):
    fig = go.Figure()
    
    y_column = 'Latitude' if direction == 'NS' else 'Longitude'
    
    fig.add_trace(go.Scatter(
        x=data['TimeOfDay'],
        y=data[y_column],
        mode='markers',
        marker=dict(
            color=data['Speed'],
            # color=gpx_data['SpeedCategory'].apply(lambda x: color_map[x]),  # Map categorical values to colors
            colorscale=[[0, 'red'], [0.05, 'yellow'], [0.3, 'lightgreen'], [0.5, 'green'], [0.8, 'darkgreen'], [1, 'purple']],
            colorbar=dict(title='Speed Scale'),
            size=10
        ),
        text=data['Name'],
        hoverinfo='text'
    ))

    # Customize y-axis to show intersection names
    fig.update_yaxes(
        tickvals=list(intersection_coords.values()),
        ticktext=list(intersection_coords.keys()),
        title='Key Intersections'
    )

    # Customize x-axis
    fig.update_xaxes(
        tickformat='%H:%M',
        dtick=360
    )

    # Set title
    fig.update_layout(
        title=f'Key Intersections vs Time of Day with Speed Gradient ({direction} Direction)'
    )

    fig.show()

# Function to plot data on a map
def plot_data_on_map(df):
    # Create a base map
    m = folium.Map(tiles="cartodb positron", location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=12)
    
    # Define color for each speed category
    colors = {
        'Below 3 mph': 'red',
        '3-15 mph': 'orange',
        '15-30 mph': 'yellow',
        'Above 30 mph': 'green'
    }

    # Add points to the map
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5,
            color=colors[row['SpeedCategory']],
            # fill=True,
            fill_color= colors[row['SpeedCategory']], #'RdYlGn',
            fill_opacity=0.7,
            legend_name = 'Speed from GPX Data',
            popup=f"Time: {row['TimeOfDay']}<br>Speed: {row['Speed']} mph<br>Lat: {row['Latitude']}<br>Lon: {row['Longitude']}"
        ).add_to(m)
    
    # Define the output file name
    map_output = 'gpx_map.html'

    # Save the map to an HTML file
    m.save(map_output)
    print(f'Map has been saved as {map_output}')

# Main function
def main():
    # Prompt user for inputs
    gpx_folder = input("Enter the path to the GPX folder: ")
    kml_file = input("Enter the path to the KML file: ")
    direction = input("Enter the direction (NS or EW): ")

    # Validate direction input
    while direction not in ['NS', 'EW']:
        print("Invalid direction. Please enter either 'NS' or 'EW'.")
        direction = input("Enter the direction (NS or EW): ")

    # Process the data and create visualizations
    all_gpx_data = []

    for filename in os.listdir(gpx_folder):
        if filename.lower().endswith('.gpx'):
            file_path = os.path.join(gpx_folder, filename)
            print(f'Processing file: {filename}')
            df = parse_gpx(file_path)
            all_gpx_data.append(df)

    gpx_data = pd.concat(all_gpx_data, ignore_index=True)

    # Parse KML files
    key_intersections = parse_kml(kml_file)

    # Map lat/lon to intersections
    gpx_data, intersection_coords = map_to_intersections(gpx_data, key_intersections, direction)

    # Print the first 20 rows of the gpx_data DataFrame
    print(gpx_data.head(20))
    # Sort data by DateTime
    gpx_data = gpx_data.sort_values(by='TimeOfDay')

    # plot using plotly for dynamic visualization. lat/lon by time
    make_time_plot(gpx_data, intersection_coords, direction)

    # Plot the data on a map
    plot_data_on_map(gpx_data)

# Run the script
if __name__ == "__main__":
    main()