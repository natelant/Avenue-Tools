import os
import pandas as pd
import numpy as np
import xlsxwriter
from datetime import datetime

from pathlib import Path

def print_ascii_art():
    
    Fire = [
        
        '                       )                       )     )  (    (     ',
        '   (                ( /(              *   ) ( /(  ( /(  )\ ) )\ )  ',
        '   )\    (   (  (   )\())   (  (    ` )  /( )\()) )\())(()/((()/(  ',
        '((((_)(  )\  )\ )\ ((_)\    )\ )\    ( )(_)|(_)\ ((_)\  /(_))/(_)) ',
        ' )\ _ )\((_)((_|(_) _((_)_ ((_|(_)  (_(_())  ((_)  ((_)(_)) (_))   ',
        ' (_)_\(_) \ / /| __| \| | | | | __| |_   _| / _ \ / _ \| |  / __|  ',
        '  / _ \  \ V / | _|| .` | |_| | _|    | |  | (_) | (_) | |__\__ \  ',
        ' /_/ \_\  \_/  |___|_|\_|\___/|___|   |_|   \___/ \___/|____|___/  '
                                                                   

    ]

    for line in Fire:
        print(line)

def calculate_average_travel_time(folder_path, start_time, stop_time, output_file):
    # Read all CSV files from the specified folder
    files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    
    if not files:
        print("No CSV files found in the specified folder.")
        return

    # Initialize an empty DataFrame to store the combined data
    combined_data = pd.DataFrame()

    # Combine all CSV files into a single DataFrame
    dfs = []
    for file in files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        # Add a new column with the source filename
        df['source_file'] = file
        dfs.append(df)

        combined_data = pd.concat(dfs, ignore_index=True)
        combined_data['local_datetime'] = pd.to_datetime(combined_data['local_datetime'])

    # Create a new column 'before_after' based on the input implementation date
    combined_data['before_after'] = np.where(pd.to_datetime(combined_data['local_datetime']) < filter_date, 'before', 'after')

    # Outlier Analysis -----------------------------------
    # set time variable to index for time series calculations
    data_index = combined_data.set_index('local_datetime')

    # Extract the time component and create a new column 'hour'
    data_index['hour'] = data_index.index.hour

    # Calculate the hourly average travel time for each hour of the day on each route (source_file)
    hourly_avg_travel_time = data_index.groupby(['source_file', 'hour'])['avg_travel_time'].mean().rename('hourly_average')
    print(data_index)
    print(data_index.index)
    print("Number of Levels:", data_index.index.nlevels)
    print('---------------------------')
    print(hourly_avg_travel_time)
    print(hourly_avg_travel_time.index)
    print("Number of levels:", hourly_avg_travel_time.index.nlevels)


    # Merge the hourly averages back to the original DataFrame
    data_index = data_index.merge(hourly_avg_travel_time, left_on='hour', right_on='hour', suffixes=('', '_hourly'))

    # Calculate the z-score for each travel time based on the average for its respective hour
    data_index['z_score'] = (data_index['avg_travel_time'] - data_index['hourly_average']) / data_index['hourly_average'].std()

    # Set a threshold for outliers (e.g., z-score greater than 3 or less than -3)
    outlier_threshold = 3
    outliers = data_index[(data_index['z_score'] > outlier_threshold) | (data_index['z_score'] < -outlier_threshold)]

    # Filter data based on peak hour range and remove outliers
    peak_hour_mask = (combined_data['local_datetime'].dt.time >= start_time) & (combined_data['local_datetime'].dt.time <= stop_time)
    filtered_data = combined_data[peak_hour_mask & ~combined_data['local_datetime'].isin(outliers.index)]

    # Calculate Travel Times ---------------------------------
    # Create summary table to compare before and after travel times, excluding the outliers
    summary_table = (
        filtered_data
        .groupby(['source_file','before_after'])
        ['avg_travel_time']
        .mean()
        .reset_index()
        .pivot(index='source_file', columns='before_after', values='avg_travel_time')
        .reset_index()
    )

    # Reorder the columns
    # Check if 'before' and 'after' columns exist in the DataFrame
    if 'before' in summary_table.columns and 'after' in summary_table.columns:
        # Reorder the columns if both 'before' and 'after' exist
        summary_table = summary_table[['source_file', 'before', 'after']]
    elif 'before' in summary_table.columns:
        # Reorder the columns if only 'before' exists
        summary_table = summary_table[['source_file', 'before']]
    elif 'after' in summary_table.columns:
        # Reorder the columns if only 'after' exists
        summary_table = summary_table[['source_file', 'after']]

    # Create an Excel writer
    excel_writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

    # Write the filtered data to Sheet 1
    combined_data.to_excel(excel_writer, sheet_name='Raw Data', index=False)

    # Write the summary table to Sheet 2
    summary_table.to_excel(excel_writer, sheet_name='Summary Table', index=False)

    # Write the outliers to Sheet 3
    outliers.to_excel(excel_writer, sheet_name='Outliers', index=False)

    # Save and close the Excel writer
    excel_writer.close()

    # Assuming 'output_file' is the variable holding the desired file name
    print(f"The travel times have been calculated, grouped by Clearguide routes, and saved as '{output_file}'.")
    os.system(f'start excel {output_file}')  # Open the Excel file


if __name__ == "__main__":
    # Call the function to print the ASCII art
    print_ascii_art()
    # Explain the tool
    print(
        "Avenue Tools helps you get work done faster.",
        "This tool is the Travel Time Tool and",
        "will help you process travel times from ClearGuide.",
        "Make sure you have saved all your .csv files to a folder and",
        "follow the instructions below.",
        "The output here is a .xlsx file with the raw data on sheet1 and",
        "a summary table of average travel times."
    )
    print("_______________________________________")

    # Prompt the user to input the folder path via command line
    folder_path = input("Enter the folder path containing CSV files: ").strip()
    
    # Validate the folder path
    if not os.path.exists(folder_path):
        print("Invalid folder path. Please provide a valid path.")
    else:
        # Prompt the user to enter the peak hour start time and stop time
        start_time_str = input("Enter peak hour start time (HH:MM): ")
        stop_time_str = input("Enter peak hour stop time (HH:MM): ")

        # Convert input times to datetime.time objects
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        stop_time = datetime.strptime(stop_time_str, "%H:%M").time()

        # Prompt the user to enter the date to split the data
        implementation_date_str = input("Enter the implementation date (MM/DD/YYYY): ")
        filter_date = pd.to_datetime(implementation_date_str, format="%m/%d/%Y")

        # Prompt the user to enter the file path of output file
        output_file = input("Enter the file name of output file (.xlsx): ").strip()

        # Call the function to merge and analyze the data
        calculate_average_travel_time(folder_path, start_time, stop_time, output_file) # note the function does not include filter date
