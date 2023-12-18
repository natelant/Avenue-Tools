import os
import pandas as pd
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

def calculate_average_travel_time(folder_path, start_time, stop_time):
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

    # Calculate Travel Times ---------------------------------

    # Create a new column 'before_after' based on the input date
    combined_data['before_after'] = pd.to_datetime(combined_data['local_datetime']).apply(lambda x: 'before' if x < filter_date else 'after')

    
    # Filter data based on peak hour range
    peak_hour_mask = (combined_data['local_datetime'].dt.time >= start_time) & (combined_data['local_datetime'].dt.time <= stop_time)
    peak_hour_data = combined_data[peak_hour_mask]

    # Calculate the average travel time during the peak hour
    average_travel_time = peak_hour_data['avg_travel_time'].mean()

    # Create a summary table (average travel times by clearguide files)
    summary_table = peak_hour_data.groupby('source_file')['avg_travel_time'].mean().reset_index()
    # test
    summary_table_1 = (
        peak_hour_data
        .groupby(['source_file','before_after'])
        ['avg_travel_time']
        .mean()
        .reset_index()
        .pivot(index='source_file', columns='before_after', values='avg_travel_time')
        .reset_index()
    )

    # Create an Excel writer
    excel_writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')

    # Write the filtered data to Sheet 1
    combined_data.to_excel(excel_writer, sheet_name='Sheet1', index=False)

    # Write the summary table to Sheet 2
    summary_table_1.to_excel(excel_writer, sheet_name='Sheet2', index=False)

    # Save and close the Excel writer
    excel_writer.close()

    print("The travel times have been calculated, grouped by Clearguide routes, and saved as 'output.xlsx'.")
    os.system('start excel output.xlsx')  # Open the Excel file

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

        # Call the function to merge and analyze the data
        calculate_average_travel_time(folder_path, start_time, stop_time)
