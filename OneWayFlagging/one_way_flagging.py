# This tool converts a folder with .xlsm, .gpx, and .kml files
# .xlsm should have the counts from one-way flagging
# .gpx comes directly from the GPX app
# .kml should have the two stop bars (i.e. EB and WB) and the estimated "end of queue" points = so there are 4 total points from the KML file

# --------------------------------------------------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------------------------------------------------
# Run - from start of EB to Start of WB (i.e. odd runs are EB and even runs are WB)
#     - runs connect the count data to GPX data. Migrate the Start Stop library into the GPX data and organize by direction and time stamp



# --------------------------------------------------------------------------------------------------------------------------------------------
# imports and directories
# --------------------------------------------------------------------------------------------------------------------------------------------
import pandas as pd
import os
from datetime import datetime, time
import plotly.express as px
import plotly.graph_objects as go

# Specify the directory containing the Excel files
directory = 'data'
output_file = 'output/testing.xlsx'

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

# --------------------------------------------------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------------------------------------------------

# Read in, clean and combine .xlsm -> count_data
count_data = readin_counts(directory)

# Add headway to count_data
headway_data = calculate_headway(count_data)

# Visualize headway - make sure the data is clean
my_headway = visualize_headway(headway_data)
my_headway.show()


# Read in .gpx -> gpx_data



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
    headway_data.to_excel(writer, sheet_name='Headway Raw Data', index=False)

print(f"File was successfully written to '{output_file}'.")

# Open the Excel file
# os.system(f'start excel {output_file}')