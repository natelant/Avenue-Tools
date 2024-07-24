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

    return cleaned

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

    return filtered_df

# --------------------------------------------------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------------------------------------------------

# Read in, clean and combine .xlsm -> count_data
count_data = readin_counts(directory)

print(count_data.head(30))

# 

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

