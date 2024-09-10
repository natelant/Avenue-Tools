import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_plans_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/purdue_coordination_diagram.db')

    # SQL query to join plans with phases
    query = """
    SELECT DISTINCT p.*, ph.phase_number, ph.phase_description, ph.location_description
    FROM plans p
    LEFT JOIN phases ph ON p.phase_id = ph.phase_number AND p.location_identifier = ph.location_identifier
    """

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

def get_volume_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/purdue_coordination_diagram.db')

    # SQL query to join volume_per_hour with plans, avoiding duplications
    query = """
    SELECT v.phase_id,
           v.location_identifier,
           (SELECT p.plan_description
            FROM plans p
            WHERE v.phase_id = p.phase_id 
              AND v.location_identifier = p.location_identifier
              AND v.timestamp >= p.start 
              AND v.timestamp < p.end
            LIMIT 1) as plan_description,
           (SELECT p.start
            FROM plans p
            WHERE v.phase_id = p.phase_id 
              AND v.location_identifier = p.location_identifier
              AND v.timestamp >= p.start 
              AND v.timestamp < p.end
            LIMIT 1) as start,
           SUM(v.value) / 4 as total_volume
    FROM volume_per_hour v
    GROUP BY v.phase_id, v.location_identifier, plan_description, start
    """

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

plans_df = get_plans_data()
volumes_df = get_volume_data()

the_df = pd.merge(plans_df, volumes_df, on=['phase_id', 'location_identifier', 'plan_description', 'start'], how='inner')

# Define the signals on State St (6100 S to Williams)
signals = [7147, 7474, 7148, 7642, 7149, 7150, 7073, 7152, 7153, 7154, 7641, 7155, 7156, 7157, 7158, 7159, 7657, 7160, 7401, 7161, 7162]

# Create a dictionary mapping signal IDs to their order
signal_order = {signal: index for index, signal in enumerate(signals)}

# Define time windows
window1_start = datetime(2024, 8, 1, 0, 0)
window1_end = datetime(2024, 8, 20, 23, 59)
window2_start = datetime(2024, 8, 26, 0, 0)
window2_end = datetime(2024, 9, 8, 23, 59)

# Convert 'start' and 'end' columns to datetime
the_df['start'] = pd.to_datetime(the_df['start'], format='ISO8601')
the_df['end'] = pd.to_datetime(the_df['end'], format='ISO8601')

# Filter out Fridays, Saturdays, and Sundays
the_df = the_df[~the_df['start'].dt.dayofweek.isin([4, 5, 6])]

# Filter data within the specified time windows
mask = ((the_df['start'] >= window1_start) & (the_df['end'] <= window1_end)) | \
       ((the_df['start'] >= window2_start) & (the_df['end'] <= window2_end))
the_df = the_df[mask]

# Filter out rows where Plan Description is Unknown or Free
the_df = the_df[~the_df['plan_description'].isin(['Unknown', 'Free'])]
# Filter out rows where volume is 0 and also where percent_arrival_on_green is 0 
the_df = the_df[the_df['total_volume'] > 0]
the_df = the_df[the_df['percent_arrival_on_green'] > 0]

# Function to remove outliers using IQR method
def remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

# Remove outliers from percent_arrival_on_green and percent_green_time
the_df = remove_outliers(the_df, 'percent_arrival_on_green')
the_df = remove_outliers(the_df, 'percent_green_time')

print(f"Rows after filtering: {len(the_df)}")
print(the_df.head())

# Define a function to assign time window
def assign_time_window(date):
    if window1_start <= date <= window1_end:
        return 'Window 1'
    elif window2_start <= date <= window2_end:
        return 'Window 2'
    else:
        return 'Other'

# Assign time window to each row
the_df['time_window'] = the_df['start'].apply(assign_time_window)

# Group by location ID, plan description, phase, and time window
grouped = the_df.groupby(['location_description', 'plan_description', 'phase_description', 'time_window'])

# Calculate average percent arrival on green and total volume for each group
avg_data = grouped.agg({
    'percent_arrival_on_green': 'mean',
    'total_volume': 'mean'
}).unstack(level='time_window')

# Flatten column names
avg_data.columns = [f'{col[0]}_{col[1]}' for col in avg_data.columns]

# Calculate the difference between Window 1 and Window 2 for both metrics
avg_data['percent_arrival_on_green_Difference'] = avg_data['percent_arrival_on_green_Window 2'] - avg_data['percent_arrival_on_green_Window 1']
avg_data['total_volume_Difference'] = avg_data['total_volume_Window 2'] - avg_data['total_volume_Window 1']

# Sort by the absolute difference in percent arrival on green in descending order
avg_data = avg_data.sort_values('percent_arrival_on_green_Difference', key=abs, ascending=False)

# Print the results
print("\nComparison of Average Percent Arrival on Green and Total Volume between Time Windows:")
print(avg_data)

# Identify significant changes (e.g., more than 5% difference in arrival on green)
significant_changes = avg_data[abs(avg_data['percent_arrival_on_green_Difference']) > 5]

print("\nSignificant Changes in Average Percent Arrival on Green (>5% difference):")
print(significant_changes)
print("--------------------------   --------------------------")

# Organize results by location description, then ordered by plan description
organized_results = avg_data.reset_index()
organized_results = organized_results.sort_values(['location_description', 'plan_description'])

# Extract signal ID from location_description and create a new column for sorting
organized_results['signal_id'] = organized_results['location_description'].str.extract('(\d+)').astype(int)

# Create a new column with the order based on the signal_order dictionary
organized_results['signal_order'] = organized_results['signal_id'].map(signal_order)

# Sort the DataFrame by signal_order and then by plan_description
organized_results = organized_results.sort_values(['signal_order', 'plan_description'])

# Drop the temporary columns used for sorting
organized_results = organized_results.drop(columns=['signal_id', 'signal_order'])

# Write results to CSV
csv_filename = 'state_analysis_aug_with_volume.csv'
organized_results.to_csv(csv_filename, index=False)

print(f"\nResults have been written to {csv_filename}")
print("The CSV is organized by location description, then ordered by plan description.")

