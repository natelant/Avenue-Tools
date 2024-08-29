import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_plans_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/purdue_coordination_diagram.db')

    # SQL query to join plans with phases
    query = """
    SELECT p.*, ph.phase_number, ph.phase_description, ph.location_description
    FROM plans p
    LEFT JOIN phases ph ON p.phase_id = ph.phase_number AND p.location_identifier = ph.location_identifier
    """

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

the_df = get_plans_data()

# Define the signals to filter by
signals = [7147, 7474, 7148, 7642, 7149, 7150, 7073, 7152, 7153, 7154, 7641, 7155, 7156, 7157, 7158, 7159, 7657, 7160, 7401, 7161, 7162]

# Define time windows
window1_start = datetime(2024, 8, 1, 0, 0)
window1_end = datetime(2024, 8, 20, 23, 59)
window2_start = datetime(2024, 8, 26, 0, 0)
window2_end = datetime(2024, 8, 28, 23, 59)

# Convert 'start' and 'end' columns to datetime
the_df['start'] = pd.to_datetime(the_df['start'], format='ISO8601')
the_df['end'] = pd.to_datetime(the_df['end'], format='ISO8601')

# Filter out Fridays, Saturdays, and Sundays
the_df = the_df[~the_df['start'].dt.dayofweek.isin([4, 5, 6])]

# Filter data within the specified time windows
mask = ((the_df['start'] >= window1_start) & (the_df['end'] <= window1_end)) | \
       ((the_df['start'] >= window2_start) & (the_df['end'] <= window2_end))
the_df = the_df[mask]



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

# Calculate average percent arrival on green for each group
avg_arrival_on_green = grouped['percent_arrival_on_green'].mean().unstack(level='time_window')

# Calculate the difference between Window 1 and Window 2
avg_arrival_on_green['Difference'] = avg_arrival_on_green['Window 2'] - avg_arrival_on_green['Window 1']

# Sort by the absolute difference in descending order
avg_arrival_on_green = avg_arrival_on_green.sort_values('Difference', key=abs, ascending=False)

# Print the results
print("\nComparison of Average Percent Arrival on Green between Time Windows:")
print(avg_arrival_on_green)

# Identify significant changes (e.g., more than 5% difference)
significant_changes = avg_arrival_on_green[abs(avg_arrival_on_green['Difference']) > 5]

print("\nSignificant Changes in Average Percent Arrival on Green (>5% difference):")
print(significant_changes)
print("--------------------------   --------------------------")

# Organize results by location description, then ordered by plan description
organized_results = avg_arrival_on_green.reset_index()
organized_results = organized_results.sort_values(['location_description', 'plan_description'])

# Write results to CSV
csv_filename = 'state_analysis_aug.csv'
organized_results.to_csv(csv_filename, index=False)

print(f"\nResults have been written to {csv_filename}")
print("The CSV is organized by location description, then ordered by plan description.")




