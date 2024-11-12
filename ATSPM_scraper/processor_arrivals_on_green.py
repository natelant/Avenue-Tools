import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def get_data_from_db(query):
    with sqlite3.connect('data/purdue_coordination_diagram.db') as conn:
        return pd.read_sql_query(query, conn)

def get_plans_data():
    query = """
    SELECT DISTINCT p.*, ph.phase_number, ph.phase_description, ph.location_description
    FROM plans p
    LEFT JOIN phases ph ON p.phase_id = ph.phase_number AND p.location_identifier = ph.location_identifier
    """
    return get_data_from_db(query)

def get_volume_data():
    query = """
    SELECT v.phase_id,
           v.location_identifier,
           p.plan_description,
           p.start,
           SUM(v.value) / 4 as total_volume
    FROM volume_per_hour v
    JOIN plans p ON v.phase_id = p.phase_id 
                 AND v.location_identifier = p.location_identifier
                 AND v.timestamp >= p.start 
                 AND v.timestamp < p.end
    GROUP BY v.phase_id, v.location_identifier, p.plan_description, p.start
    """
    return get_data_from_db(query)

plans_df = get_plans_data()
volumes_df = get_volume_data()

# Combine data fetching and merging
the_df = pd.merge(plans_df, volumes_df, on=['phase_id', 'location_identifier', 'plan_description', 'start'], how='inner')

# Convert location_identifier to integer type
the_df['location_identifier'] = the_df['location_identifier'].astype(int)

# State St (6100 S to Williams) = [7147, 7474, 7148, 7642, 7149, 7150, 7073, 7152, 7153, 7154, 7641, 7155, 7156, 7157, 7158, 7159, 7657, 7160, 7401, 7161, 7162]
# Lower State St (11400 S to 9000 S) = [7174, 7643, 7175, 7640, 7176, 7352, 7177, 7178, 7179, 7353, 7351]
# SR 209 (9000 S) = [7522, 7521, 7386, 7423, 7422, 7421, 7067]
# SR 48 (7800 S) = [7066, 7354, 7012, 7011, 7010, 7116]
signals = [7147, 7474, 7148, 7642, 7149, 7150, 7073, 7152, 7153, 7154, 7641, 7155, 7156, 7157, 7158, 7159, 7657, 7160, 7401, 7161, 7162]
route_name = 'State St (6100 S to Williams)'
output_file = f'AoG_{route_name}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx'

# Create a dictionary mapping signal IDs to their order
signal_order = {signal: index for index, signal in enumerate(signals)}

# Define time windows
window1_start = datetime(2024, 8, 1, 0, 0)
window1_end = datetime(2024, 9, 11, 23, 59)
window2_start = datetime(2024, 10, 18, 0, 0)
window2_end = datetime(2024, 10, 28, 23, 59)

# Function to truncate milliseconds
def truncate_milliseconds(dt_string):
    return dt_string.split('.')[0]

# Optimize filtering
the_df['start'] = pd.to_datetime(the_df['start'].apply(truncate_milliseconds), format='%Y-%m-%dT%H:%M:%S')
the_df['end'] = pd.to_datetime(the_df['end'].apply(truncate_milliseconds), format='%Y-%m-%dT%H:%M:%S')

# Debugging prints
print("Data type of location_identifier:", the_df['location_identifier'].dtype)
print("Sample of location_identifier values:", the_df['location_identifier'].head())
print("Type of first signal in signals list:", type(signals[0]))
print("Number of unique location identifiers:", the_df['location_identifier'].nunique())
print("Unique location identifiers:", the_df['location_identifier'].unique())

# First, verify if percent_arrival_on_green exists in your DataFrame
print("Columns in the_df:", the_df.columns)

# remove weekends, dates outside of time windows, unknown plans, and 0 volume
mask = (
    (~the_df['start'].dt.dayofweek.isin([4, 5, 6])) & 
    (
        ((the_df['start'] >= window1_start) & (the_df['end'] <= window1_end)) |
        ((the_df['start'] >= window2_start) & (the_df['end'] <= window2_end))
    ) &
    (~the_df['plan_description'].isin(['Unknown', 'Free'])) &
    (the_df['total_volume'] > 0) &
    (the_df['percent_arrival_on_green'] > 0) &
    (the_df['location_identifier'].isin(signals))
)

# Add some debugging prints
filtered_df = the_df[mask].copy().reset_index(drop=True)
print("\nNumber of records in Window 1:", 
      filtered_df[filtered_df['start'] < window2_start].shape[0])
print("Number of records in Window 2:", 
      filtered_df[filtered_df['start'] >= window2_start].shape[0])

# Function to remove outliers using IQR method
def remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

# Remove outliers from percent_arrival_on_green and percent_green_time
filtered_df = remove_outliers(filtered_df, 'percent_arrival_on_green')
filtered_df = remove_outliers(filtered_df, 'percent_green_time')

print(f"Rows after filtering: {len(filtered_df)}")
print(filtered_df.head())

# Write the filtered DataFrame to an Excel file, first sheet is the original data, second sheet is the filtered data
with pd.ExcelWriter(output_file) as writer:
    the_df.to_excel(writer, sheet_name='Original Data', index=False)
    filtered_df.to_excel(writer, sheet_name='Filtered Data', index=False)

# Optimize time window assignment
filtered_df['time_window'] = np.where(
    filtered_df['start'] < window2_start,
    'Window 1',
    'Window 2'
)

# Group by location ID, plan description, phase, and time window
grouped = filtered_df.groupby(['location_description', 'plan_description', 'phase_description', 'time_window'])

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
avg_data['calculated_volumes_difference'] = avg_data['total_volume_Window 2'] * avg_data['percent_arrival_on_green_Difference'] /100

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

# Write results to sheet 3 of Excel file
with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:
    organized_results.to_excel(writer, sheet_name='Organized Results', index=False)

print(f"\nResults have been written to {output_file}")
print("The Excel is organized by location description, then ordered by plan description.")


# Create pivot table
pivot = organized_results.pivot_table(
    values='percent_arrival_on_green_Difference',
    index=['location_description', 'plan_description'],
    columns='phase_description',
    aggfunc='first'
)

volumes_pivot = organized_results.pivot_table(
    values='calculated_volumes_difference',
    index=['location_description', 'plan_description'],
    columns='phase_description',
    aggfunc='first'
)

# Add a Total column by summing across rows
volumes_pivot['Total'] = volumes_pivot.sum(axis=1)

# Reset the index to make location_description and plan_description regular columns
pivot = pivot.reset_index()
volumes_pivot = volumes_pivot.reset_index()

# write pivot to sheet 4 of Excel file
with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:
    pivot.to_excel(writer, sheet_name='Pivot Table', index=False)
    volumes_pivot.to_excel(writer, sheet_name='Volumes Pivot Table', index=False)
