import pandas as pd
from pathlib import Path
import re
import os
import platform

def read_err_files(base_folder):
    data = []
    
    # Construct the full path to the .results folder
    results_folder = Path(base_folder) / f"{Path(base_folder).name}.results"
    
    # Iterate through all .err files in the specified folder
    for file_path in results_folder.glob('*.err'):
        with open(file_path, 'r') as file:
            content = file.read().strip()
            data.append({
                'filename': file_path.name,
                'content': content
            })
    
    return pd.DataFrame(data)

def parse_error_content(df):
    parsed_data = []
    vehicle_input_warnings = []
    
    for _, row in df.iterrows():
        # Extract simulation_id from filename
        simulation_id = row['filename'][-7:-4]
        
        for line in row['content'].split('\n'):
            if line.strip().startswith('Warning'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    warning_text = parts[1]
                    
                    if "Vehicle input" in warning_text:
                        # Parse vehicle input warning
                        try:
                            input_id = int(warning_text.split('Vehicle input')[1].split('could')[0].strip())
                            remaining = int(warning_text.split('remain:')[1].split('vehicles')[0].strip())
                            vehicle_input_warnings.append({
                                'filename': row['filename'],
                                'simulation_id': simulation_id,
                                'input_id': input_id,
                                'remaining_vehicles': remaining
                            })
                        except (ValueError, IndexError):
                            pass
                    else:
                        # Only parse warnings that contain "lane change"
                        if "lane change" in warning_text.lower():
                            # Parse other warnings as before
                            try:
                                simulation_second = float(warning_text.split('Simulation second')[1].split(':')[0].strip())
                            except (ValueError, IndexError):
                                simulation_second = None
                            
                            try:
                                wait_time = float(warning_text.split('After')[1].split('seconds')[0].strip())
                            except (ValueError, IndexError):
                                wait_time = None
                            
                            try:
                                vehicle_id = warning_text.split('vehicle')[1].split('(')[0].strip()
                            except IndexError:
                                vehicle_id = None
                            
                            try:
                                route = warning_text.split('(on')[1].split(')')[0].strip()
                                # Extract origin and destination numbers from route
                                match = re.search(r'"(\d+)\s*-\s*(\d+)"', route)
                                if match:
                                    origin, destination = map(int, match.groups())
                                else:
                                    origin = destination = None
                            except IndexError:
                                route = None
                                origin = None
                                destination = None
                            
                            try:
                                link_full = warning_text.split('from link')[1].split('at')[0].strip().strip('"')
                                # Extract link_id and link_name
                                match = re.match(r'(\d+):\s*(.*)', link_full)
                                if match:
                                    link_id = int(match.group(1))
                                    link_name = match.group(2).strip()
                                else:
                                    link_id = None
                                    link_name = link_full
                            except IndexError:
                                link_full = None
                                link_id = None
                                link_name = None
                            
                            try:
                                position = float(warning_text.split('at position')[1].split('ft')[0].strip())
                            except (ValueError, IndexError):
                                position = None
                            
                            parsed_data.append({
                                'filename': row['filename'],
                                'simulation_id': simulation_id,
                                'simulation_second': simulation_second,
                                'wait_time': wait_time,
                                'vehicle_id': vehicle_id,
                                'route': route,
                                'origin': origin,
                                'destination': destination,
                                'link': link_full,
                                'link_id': link_id,
                                'link_name': link_name,
                                'position': position
                            })
    
    return pd.DataFrame(parsed_data), pd.DataFrame(vehicle_input_warnings)



# Create summary for Sheet 1
def create_summary_sheet1(df):
    # Group by link, position, and simulation_id, then count the occurrences
    grouped_df = df.groupby(['link_id', 'link_name', 'position', 'simulation_id']).size().reset_index(name='count')

    # Pivot the table
    pivoted_df = grouped_df.pivot(index=['link_id', 'link_name', 'position'], columns='simulation_id', values='count')

    # Add a total column
    pivoted_df['Total'] = pivoted_df.sum(axis=1)

    # Sort the dataframe by Total in descending order
    pivoted_df = pivoted_df.sort_values('Total', ascending=False)

    return pivoted_df

# Create summary for Sheet 2
def create_summary_sheet2(df):
    # Group by link, origin, destination, and position, then count the occurrences
    grouped_df = df.groupby(['link_id', 'link_name', 'origin', 'destination', 'position']).size().reset_index(name='Total')

    # Sort the dataframe by link_id in ascending order
    grouped_df = grouped_df.sort_values(['link_id', 'position'], ascending=True)

    return grouped_df

# Create summary for Sheet 3
def create_summary_sheet3(df):
    # Check if the DataFrame is empty or missing required columns
    if df.empty or not all(col in df.columns for col in ['input_id', 'simulation_id', 'remaining_vehicles']):
        return pd.DataFrame(columns=['input_id', 'Average'])  # Return empty DataFrame with expected columns
    
    # Group by input_id and simulation_id, then sum the remaining_vehicles
    grouped_df = df.groupby(['input_id', 'simulation_id'])['remaining_vehicles'].sum().reset_index()

    # Pivot the table
    pivoted_df = grouped_df.pivot(index='input_id', columns='simulation_id', values='remaining_vehicles')

    # Add an average column
    pivoted_df['Average'] = pivoted_df.mean(axis=1)

    # Sort the dataframe by Average in descending order
    pivoted_df = pivoted_df.sort_values('Average', ascending=False)

    return pivoted_df

def create_excel_summary(parsed_df, vehicle_input_df, output_file='error_summary.xlsx'):
    with pd.ExcelWriter(output_file) as writer:
        # Write Sheet 1
        sheet1_df = create_summary_sheet1(parsed_df)
        sheet1_df.to_excel(writer, sheet_name='Lane Change')

        # Write Sheet 2
        sheet2_df = create_summary_sheet2(parsed_df)
        sheet2_df.to_excel(writer, sheet_name='Routing', index=False)

        # Write Sheet 3
        sheet3_df = create_summary_sheet3(vehicle_input_df)
        sheet3_df.to_excel(writer, sheet_name='Vehicle Input')

    print(f"Excel file '{output_file}' has been created with Lane Change, Routing, and Vehicle Input sheets.")

def open_file(filename):
    if platform.system() == 'Darwin':       # macOS
        os.system(f'open "{filename}"')
    elif platform.system() == 'Windows':    # Windows
        os.system(f'start excel "{filename}"')
    else:                                   # linux variants
        os.system(f'xdg-open "{filename}"')

def print_ascii_art():
    Fire = [
        r'                       )                       )     )  (    (     ',
        r'   (                ( /(              *   ) ( /(  ( /(  )\ ) )\ )  ',
        r'   )\    (   (  (   )\())   (  (    ` )  /( )\()) )\())(()/((()/(  ',
        r'((((_)(  )\  )\ )\ ((_)\    )\ )\    ( )(_)|(_)\ ((_)\  /(_))/(_)) ',
        r' )\ _ )\((_)((_|(_) _((_)_ ((_|(_)  (_(_())  ((_)  ((_)(_)) (_))   ',
        r' (_)_\(_) \ / /| __| \| | | | | __| |_   _| / _ \ / _ \| |  / __|  ',
        r'  / _ \  \ V / | _|| .` | |_| | _|    | |  | (_) | (_) | |__\__ \  ',
        r' /_/ \_\  \_/  |___|_|\_|\___/|___|   |_|   \___/ \___/|____|___/  '
    ]

    for line in Fire:
        print(line)

if __name__ == "__main__":
    print_ascii_art()
    # Prompt for the base folder
    base_folder = input("Enter the path to the base folder containing the .results folder: ").strip()
    # Check if the folder exists
    if not os.path.exists(base_folder):
        print(f"Error: The folder '{base_folder}' does not exist.")
        print("Please check the path and try again.")
        exit(1)

    output_file='error_summary_'+Path(base_folder).name+'.xlsx'

    

    # Read the .err files and create a DataFrame
    df = read_err_files(base_folder)

    # Parse the error content
    parsed_df, vehicle_input_df = parse_error_content(df)

    # Create the Excel summary
    create_excel_summary(parsed_df, vehicle_input_df, output_file)


    # Open the Excel file
    open_file(output_file)
    print(f"Excel file has successfully been created.")
