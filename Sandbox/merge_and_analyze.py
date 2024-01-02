import os
import pandas as pd
import xlsxwriter

from pathlib import Path

def merge_and_analyze(folder_path):
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

    # Filter data based on criteria (e.g., age greater than 25)
    # filtered_data = combined_data[combined_data['age'] > 25]

    # Create a summary table (average age by hair color)
    summary_table = combined_data.groupby('Hair color')['Age'].mean().reset_index()

    # Create an Excel writer
    excel_writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')

    # Write the filtered data to Sheet 1
    combined_data.to_excel(excel_writer, sheet_name='Sheet1', index=False)

    # Write the summary table to Sheet 2
    summary_table.to_excel(excel_writer, sheet_name='Sheet2', index=False)

    # Save and close the Excel writer
    excel_writer.close()

    print("Data merged, filtered, and exported to 'output.xlsx'.")
    os.system('start excel output.xlsx')  # Open the Excel file

if __name__ == "__main__":
    # Prompt the user to input the folder path via command line
    folder_path = input("Enter the folder path containing CSV files: ").strip()

    # Validate the folder path
    if not os.path.exists(folder_path):
        print("Invalid folder path. Please provide a valid path.")
    else:
        # Call the function to merge and analyze the data
        merge_and_analyze(folder_path)
