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
    R = 6371.0*0.621371 # Earth radius in (kilometers * 1 mile / 1 kilometer) = miles
    
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c  # in miles
    return distance

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
def plot_data_on_map(df, output_path):
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
    
    # Save the map to an HTML file
    m.save(output_path)
    print(f'Map has been saved to {output_path}')

# --------------------------------------------------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------------------------------------------------

# Specify the directory containing the Excel files
directory = 'data'
output_file = 'output/testing.xlsx'
output_map = 'output/map.html'

# Read in, clean and combine .xlsm -> count_data
count_data = readin_counts(directory)

# Add headway to count_data
headway_data = calculate_headway(count_data)

# format headway data for excel
headway_formatted = format_headway(headway_data)

# Visualize headway - make sure the data is clean
my_headway = visualize_headway(headway_data)
## my_headway.show()


# Read in .gpx -> gpx_data as a df
gpx_data = readin_gpx(directory)
print(gpx_data.head(50))

# write GPX to a map.html
plot_data_on_map(gpx_data, output_map)


# Calculate Travel times
# parse KML
# join with GPX





# --------------------------------------------------------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------------------------------------------------------

# Write excel ouptut file ---
# Sheet 1 - raw count data (Time Stamp, Vehicle, Direction)
# Sheet 2 - raw gpx data (Time Stamp, lat, lon, speed, grade)
# Sheet 3 - summary table (Direction: Volume, Arrival rate, classification, travel time, average speed, distance, average car headway, average truck headway...)
# Sheet 4 - headway data (Truck, Car) or (Truck following Truck, Truck following Car, Car Following Car, Car Following Truck) - for histograms and box plots
# Sheet 5 - raw travel times data (Run, Route, direction, avg speed, distance, travel time, stops)
# Sheet 6 - green time summary (Run, total run time, green time, red time, average travel time, )
# Sheet 7 - start up loss time?
# Sheet REGRESSION... master data, selective data?

# # Create an Excel writer
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    # Write the data tables to sheets in order
    count_data.to_excel(writer, sheet_name='Vehicle Count Data', index=False)
    gpx_data.drop('SpeedCategory', axis=1, inplace=True)
    gpx_data.to_excel(writer, sheet_name='GPX Data', index=False)
    headway_data.to_excel(writer, sheet_name='Headway Raw Data', index=False)
    headway_formatted.to_excel(writer, sheet_name='Headway Graphs', index=False)

print(f"File was successfully written to '{output_file}'.")

# Open the Excel file
os.system(f'start excel {output_file}')