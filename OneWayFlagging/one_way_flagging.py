# This tool converts a folder with .xlsm, .gpx, and .kml files
# .xlsm should have the counts from one-way flagging
# .gpx comes directly from the GPX app
# .kml should have the two stop bars (i.e. EB and WB) and the estimated "end of queue" points = so there are 4 total points from the KML file

# --------------------------------------------------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------------------------------------------------
# Run - from Start of EB to Start of WB (i.e. odd runs are EB and even runs are WB)
#     - runs connect the count data to GPX data. Migrate the Start Stop library into the GPX data and organize by direction and time stamp



# --------------------------------------------------------------------------------------------------------------------------------------------
# imports and directories
# --------------------------------------------------------------------------------------------------------------------------------------------
import pandas as pd
import os
from datetime import datetime, time
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import xml.etree.ElementTree as ET
import pytz
import folium
import geopandas as gpd
from fastkml import kml
import gpxpy
import zipfile
import matplotlib.pyplot as plt

# Define Salt Lake City's timezone
LOCAL_TZ = pytz.timezone('America/Denver')

# --------------------------------------------------------------------------------------------------------------------------------------------
# functions
# --------------------------------------------------------------------------------------------------------------------------------------------

# function that cleans the excel files
def clean_xlsm(filename):
    file_path = os.path.join(directory, filename)
    # Read the Excel file into a dataframe
    df = pd.read_excel(file_path)
    
    # Filter out invalid segments between multiple 'Start's without an intervening 'Stop'
    segments = []
    start_idx = None
    valid_segment = True

    for i, row in df.iterrows():
        if row['Vehicle'] == 'Start':
            if start_idx is not None:
                # Exclude the segment if 'Start' is immediately followed by 'Stop'
                if i == start_idx + 1 and df.loc[i, 'Vehicle'] == 'Stop':
                    start_idx = None
                    valid_segment = False
                    continue
            start_idx = i
            valid_segment = True
        elif row['Vehicle'] == 'Stop':
            if start_idx is not None:
                # Include only segments with valid data between 'Start' and 'Stop'
                if valid_segment:
                    segments.append(df.loc[start_idx:i])
            start_idx = None
            valid_segment = False

    # Concatenate valid segments into a single DataFrame
    if segments:
        cleaned = pd.concat(segments)
    else:
        cleaned = pd.DataFrame(columns=filename.columns)

    # remove consecutive start-stops
    drop_rows = cleaned[(cleaned['Vehicle'] == 'Start') & (cleaned['Vehicle'].shift(-1) == 'Stop')].index
    drop_rows = drop_rows.union(drop_rows+1)

    cleaned = cleaned.drop(drop_rows)

    return cleaned

# function that reads in excel, cleans, combines, and filters the data
def readin_counts(file_path):
    # List to hold dataframes
    df_list = []

    # Iterate over all files in the directory
    for filename in os.listdir(file_path):
        if filename.endswith(".xlsm"):
            # run clean function
            clean_df = clean_xlsm(filename)
            # Append the dataframe to the list
            df_list.append(clean_df)

    # Concatenate all dataframes in the list into a single dataframe
    combined_df = pd.concat(df_list, ignore_index=True)
    columns = ['Time Stamp', 'Vehicle', 'Direction']
    df = combined_df[columns]

    # Sort the DataFrame by timestamp and Remove rows with NA values in the 'time stamp' column
    filtered_df = df.sort_values('Time Stamp').dropna(subset=['Time Stamp'])

    # Create the Runs column - Remember, Run is from "Start" to "Start"
    run = 0
    runs = []

    for i, row in filtered_df.iterrows():
        if row['Vehicle'] == 'Start':
            run += 1
        runs.append(run)

    filtered_df['Run'] = runs

    # reorder the columns
    filtered_df = filtered_df[['Run', 'Time Stamp', 'Direction', 'Vehicle']]

    return filtered_df

# write fucntion to convert Time Stamp to a datetime variable
def time_to_datetime(t):
    return datetime.combine(datetime.today(), t)

# Define a function to determine the 'Group' value based on conditions
def determine_group(row):
    if row['Vehicle'] == 'Truck' and row['Following'] == 'Truck':
        return 'Truck Following Truck'
    elif row['Vehicle'] == 'Car' and row['Following'] == 'Truck':
        return 'Car Following Truck'
    elif row['Vehicle'] == 'Truck' and row['Following'] == 'Car':
        return 'Truck Following Car'
    elif row['Vehicle'] == 'Car' and row['Following'] == 'Car':
        return 'Car Following Car'
    elif row['Vehicle'] == 'Car' and row['Following'] == 'Start':
        return 'Car Following Start'
    elif row['Vehicle'] == 'Truck' and row['Following'] == 'Start':
        return 'Truck Following Start'
    else:
        return None

# function converts count_data to headway_data. 
def calculate_headway(data):
    df = data.copy()
    # Convert 'time stamp' to datetime for continuous axis plotting
    df['Timestamp'] = df['Time Stamp'].apply(time_to_datetime)

    # Calculate the 'Headway' column and convert to seconds
    df['Headway'] = df['Timestamp'].diff().dt.total_seconds()
    # Create the 'Following' column by shifting the 'classification' column
    df['Following'] = df['Vehicle'].shift(1).apply(lambda x: 'Car' if x == 'Probe' else x)
    # Create the 'Group' column using the determine_group function
    df['Group'] = df.apply(determine_group, axis=1)

    # Assign Nan to 'Headway' for rows where classification is 'stop' or 'start'
    df.loc[df['Vehicle'] == 'Stop', 'Headway'] = float('nan')
    df.loc[df['Vehicle'] == 'Start', 'Headway'] = float('nan')

    # Remove column 'Timestamp' in-place
    df.drop('Timestamp', axis=1, inplace=True)


    return df

# visualize headway
def visualize_headway(df):
    data = df.copy()
    # Convert 'time stamp' to datetime for continuous axis plotting
    data['Timestamp'] = data['Time Stamp'].apply(time_to_datetime)
    # Create a bar chart using Plotly
    fig = px.bar(data, x='Timestamp', y='Headway', 
                title='Headway Over Time - Visualize the Data Collection',
                # labels={'Time Stamp': 'Time Stamp', 'Headway': 'Headway (seconds)'},
                hover_data={'Time Stamp': True, 'Headway': True, 'Group': True, 'Timestamp': False},
                color='Direction',  # Color bars by vehicle classification
                color_discrete_map={'EB': 'purple', 'WB': 'pink', 'NB': 'Orange', 'SB': 'blue'})  # Example color mapping

    # Add vertical lines for 'start' and 'stop'
    for _, row in data.iterrows():
        if row['Vehicle'] == 'Start':
            fig.add_vline(x=row['Timestamp'], line=dict(color='green', width=2))
        elif row['Vehicle'] == 'Stop':
            fig.add_vline(x=row['Timestamp'], line=dict(color='red', width=2))

    # this solves the problem of looking faded. Something to do with the lines in between the bars. Going to be rough when I introduce a second direction
    fig.update_traces(marker_color='blue',
                      marker_line_color='blue',
                      selector=dict(type="bar"))
    return fig

def format_headway(data):
    # filter NA values from the Group (NA values are stop and start rows... no headway value)
    data = data.dropna(subset=['Group'])
    # Get unique group names from the 'Group' column
    unique_groups = data['Group'].unique()
    # Create a dictionary to store the values for each group
    group_dict = {group: data[data['Group'] == group]['Headway'].tolist() for group in unique_groups}
    # Find the maximum length among the groups
    max_length = max(len(values) for values in group_dict.values())

    # Pad shorter lists with NaN values to make all lists the same length
    for key in group_dict:
        group_dict[key] += [np.nan] * (max_length - len(group_dict[key]))

    # Create the new dataframe
    excel = pd.DataFrame(group_dict)

    return excel

# Haversine formula to calculate distance between two points on Earth
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c  # in meters
    return distance

# Function to parse GPX file and calculate speed (and grade) returns a df
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
        elevation = trkpt.find('gpx:ele', namespaces).text
        
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

        # GRADE --------

        # --------------
        
        data.append([time_of_day_local.strftime('%H:%M:%S'), lat, lon, speed, elevation])
        previous_point = (lat, lon)
        previous_time = time_of_day_local
    
    df = pd.DataFrame(data, columns=['TimeOfDay', 'Latitude', 'Longitude', 'Speed', 'Elevation'])

    bins = [-float('inf'), 3, 15, 30, float('inf')]
    labels = ['Below 3 mph', '3-15 mph', '15-30 mph', 'Above 30 mph']
    df['SpeedCategory'] = pd.cut(df['Speed'], bins=bins, labels=labels)

    # Ensure 'SpeedCategory' is an ordered categorical type
    speed_category_order = ['Below 3 mph', '3-15 mph', '15-30 mph', 'Above 30 mph']
    df['SpeedCategory'] = pd.Categorical(df['SpeedCategory'], categories=speed_category_order, ordered=True)


    return df

# function searches folder for GPX data. It cleans individually and appends to a df
def readin_gpx(file_path):
    all_gpx_data = []

    for filename in os.listdir(file_path):
        if filename.lower().endswith('.gpx'):
            file_path = os.path.join(file_path, filename)
            print(f'Processing file: {filename}')
            df = parse_gpx(file_path)
            all_gpx_data.append(df)

    df = pd.concat(all_gpx_data, ignore_index=True)

    return df

# Function to plot data on a map
def plot_data_on_map(df, output_path, json_points):
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

    # Add JSON points to the map
    for point in json_points:
        folium.Marker(
            location=[point['lat'], point['lon']],
            popup=f"Route ID: {point['route_id']}<br>Segment ID: {point['segment_id']}<br>Lat: {point['lat']}<br>Lon: {point['lon']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Save the map to an HTML file
    m.save(output_path)
    print(f'Map has been saved to {output_path}')

# Function to convert KMZ to KML and return the path to the KML file
def convert_kmz_to_kml(kmz_file):
    with zipfile.ZipFile(kmz_file, 'r') as kmz:
        for file_name in kmz.namelist():
            if file_name.endswith('.kml'):
                kmz.extract(file_name, os.path.dirname(kmz_file))
                return os.path.join(os.path.dirname(kmz_file), file_name)
    return None

# function to parse KML file containing significant intersection information
# ------------------
def parse_kml(folder):
    intersections = []

    # search folder for the kml file
    for filename in os.listdir(folder):
        if filename.lower().endswith('.kml'):
            file_path = os.path.join(folder, filename)
            print(f'Processing file: {filename}')
            kml_file = file_path
        elif filename.lower().endswith('.kmz'):
            # might need some QC here...
            kml_file = convert_kmz_to_kml(filename)

    
    with open(kml_file, 'rb') as file:
        doc = file.read()
        k = kml.KML()
        k.from_string(doc)
        
        # Assuming the KML has a single document
        for document in k.features():
            for folder in document.features():
                for feature in folder.features():
                    if isinstance(feature, kml.Placemark):
                        geometry = feature.geometry
                        if geometry:
                            if geometry.geom_type == 'Point':
                                coordinates = list(geometry.coords)[0]
                                intersections.append({
                                    'route_id': feature.name,
                                    'segment_id': feature.name,
                                    #'description': feature.description if feature.description else '',
                                    'lat': coordinates[1],
                                    'lon': coordinates[0]
                                })
                            
    return intersections

# Function to calculate travel time between two timestamps. This function is used in the process travel times function
def calculate_travel_time(start_time, end_time):
    start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
    return (end_datetime - start_datetime).total_seconds()

# Function to parse GPX file and calculate travel times
def process_travel_times(folder, intersections):
    gpx_data = []

    # search folder for the kml file
    for filename in os.listdir(folder):
        if filename.lower().endswith('.gpx'):
            file_path = os.path.join(folder, filename)
            print(f'Processing file: {filename}')
            # ---- # add something to join multiple gpx files just in case
            gpx_file = file_path

    # Parse the GPX file
    with open(gpx_file, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        # Extract data from GPX
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    gpx_data.append({'lat': point.latitude, 'lon': point.longitude, 'time': point.time.strftime('%Y-%m-%dT%H:%M:%SZ')})

    # Initialize variables
    output_data = []  # Initialize output data list
    prev_intersection = None  # Initialize previous intersection

    # Iterate through each point in GPX data
    for point in gpx_data:
        closest_intersection = None
        # Iterate through each significant intersection
        for intersection in intersections:
            # Calculate the distance between the current point and the intersection
            distance = haversine(point['lat'], point['lon'], intersection['lat'], intersection['lon'])
            # Check if the distance is within the threshold (50 feet)
            if distance <= 15:  # 50 feet in meters
                closest_intersection = intersection
                # Assign the time of the current point to the closest intersection
                closest_intersection['time'] = point['time']
                break  # Exit the loop if a significant intersection is found within the threshold

        # If a closest intersection is found within the threshold, process it
        if closest_intersection:
            if prev_intersection:
                # Calculate travel time between the previous intersection and the current closest intersection
                travel_time = calculate_travel_time(prev_intersection['time'], point['time'])
                # Store the segment start, segment finish, and travel time in the output data
                output_data.append({'route_ID': prev_intersection['route_id'] + ' / ' + closest_intersection['route_id'], 'segment_start': prev_intersection['segment_id'], 'segment_finish': closest_intersection['segment_id'], 'travel_time': travel_time})
            prev_intersection = closest_intersection

    # Convert output data to DataFrame
    output_df = pd.DataFrame(output_data)
    return output_df

def summarize_counts(df):
    # Convert 'Time Stamp' to datetime and extract the hour
    df['TimeStamp'] = pd.to_datetime(df['Time Stamp'], format='%H:%M:%S')
    df['Hour'] = df['TimeStamp'].dt.hour

    # Exclude 'Start' and 'Stop' from the dataset
    df_filtered = df[~df['Vehicle'].isin(['Start', 'Stop'])]

    # Group by hour and direction, and calculate the total volume and truck percentage
    summary = df_filtered.groupby(['Hour', 'Direction']).agg(
        Volume=('Vehicle', 'count'),
        Trucks=('Vehicle', lambda x: (x == 'Truck').sum())
    ).reset_index()

    # Calculate the truck percentage
    summary['Truck Percentage'] = (summary['Trucks'] / summary['Volume']) * 100

    # Drop the Trucks column as it's no longer needed
    summary_table = summary.drop(columns=['Trucks'])
    return summary_table

# --------------------------------------------------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------------------------------------------------

# Specify the directory containing the Excel files
directory = 'data'
output_file = 'output/testing.xlsx'
output_map = 'output/map.html'

# Read in, clean and combine .xlsm -> count_data
count_data = readin_counts(directory)
summary_counts = summarize_counts(count_data)

# Add headway to count_data
headway_data = calculate_headway(count_data)

# format headway data for excel
headway_formatted = format_headway(headway_data)

# Visualize headway - make sure the data is clean
my_headway = visualize_headway(headway_data)
## my_headway.show()


# Read in .gpx -> gpx_data as a df
gpx_data = readin_gpx(directory)




# Calculate Travel times
# parse KML output as json
key_intersections = parse_kml(directory)
print(key_intersections)

# write GPX to a map.html and include the KML points (input as json)
plot_data_on_map(gpx_data, output_map, key_intersections)

# join with GPX and calculate travel times
# ------------------------------------------
travel_times = process_travel_times(directory, key_intersections)
print(travel_times)

# Remove rows with travel_time equal to 0.0
df_filtered = travel_times[travel_times['travel_time'] != 0.0]

# Group by route_ID and create columns for each run
runs_df = df_filtered.groupby('route_ID')['travel_time'].apply(list).reset_index()

# Split the travel_time list into separate columns
max_runs = runs_df['travel_time'].apply(len).max()
runs_df = pd.concat([runs_df.drop(['travel_time'], axis=1), 
                     pd.DataFrame(runs_df['travel_time'].to_list(), columns=[f'Run {i+1}' for i in range(max_runs)])], axis=1)
print(runs_df)

# # Melt the DataFrame for visualization
# melted_df = runs_df.melt(id_vars=['route_ID'], value_vars=[f'Run {i+1}' for i in range(max_runs)], 
#                          var_name='Run', value_name='travel_time').dropna()

# # Plotting with matplotlib
# plt.figure(figsize=(12, 6))
# melted_df.boxplot(column='travel_time', by='route_ID', grid=False)
# plt.title('Travel Times for Each Route ID')
# plt.suptitle('')  # Remove the default title to avoid overlapping
# plt.xlabel('Route ID')
# plt.ylabel('Travel Time (seconds)')
# plt.xticks(rotation=45)
# plt.show()
# ---------------------------------------------




# --------------------------------------------------------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------------------------------------------------------

# Write excel ouptut file ---
# Sheet 1 - raw count data (Time Stamp, Vehicle, Direction)
# Sheet 2 - raw gpx data (Time Stamp, lat, lon, speed, grade)
# Sheet 3 - Hourly summary table (Direction: Hourly Volume, classification, 
# Sheet 4 - headway data (Truck, Car) or (Truck following Truck, Truck following Car, Car Following Car, Car Following Truck) - for histograms and box plots
#           average headway - exclude first car/truck
# Sheet 5 - Runs travel times data (Run, Route, direction, avg speed, distance, travel time, stops, grade) start time (to link to hour...)
# Sheet  5... Runs summary (From GPX data)
## Sheet 6 - Cycle summary (Run, total run time, green time, red time, all red time, ) 
# Sheet 7 - start up loss time?
# Sheet REGRESSION... master data, selective data?

# HOURLY Delay = actual Travel time - expected travel time (inside the max queue zone)

# # Create an Excel writer
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    # Write the data tables to sheets in order
    count_data.to_excel(writer, sheet_name='Vehicle Count Data', index=False)
    gpx_data.drop('SpeedCategory', axis=1, inplace=True)
    gpx_data.to_excel(writer, sheet_name='GPX Data', index=False)
    summary_counts.to_excel(writer, sheet_name='Count Summary', index=False)
    headway_data.to_excel(writer, sheet_name='Headway Raw Data', index=False)
    headway_formatted.to_excel(writer, sheet_name='Headway Graphs', index=False)
    travel_times.to_excel(writer, sheet_name='Travel Times Raw Data', index=False)
    runs_df.to_excel(writer, sheet_name='Travel Times Runs', index=False)



print(f"File was successfully written to '{output_file}'.")

# Open the Excel file
os.system(f'start excel {output_file}')