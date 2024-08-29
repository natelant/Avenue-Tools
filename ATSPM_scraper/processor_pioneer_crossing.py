import sqlite3
import pandas as pd

def get_pioneer_crossing_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/Pioneer_Crossing_TMC.db')

    # SQL query to select all data from the detailed table
    query = "SELECT * FROM tmc_data_detailed"

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

# Get the data
pioneer_crossing_data = get_pioneer_crossing_data()

# Print the first 20 rows
print("First 20 rows:")
print(pioneer_crossing_data.head(20))

# Print the last 20 rows
print("\nLast 20 rows:")
print(pioneer_crossing_data.tail(20))
# Check for duplicates
duplicate_rows = pioneer_crossing_data.duplicated(subset=['intersection_id', 'date', 'time', 'direction', 'movement', 'volume'], keep=False)

# Print the duplicate rows
print("\nDuplicate rows:")
print(pioneer_crossing_data[duplicate_rows].sort_values(by=['intersection_id', 'date', 'time', 'direction', 'movement']))

# Count the number of duplicates
num_duplicates = duplicate_rows.sum()
print(f"\nTotal number of duplicate rows: {num_duplicates}")

# If there are duplicates, you might want to remove them
if num_duplicates > 0:
    print("\nRemoving duplicates...")
    pioneer_crossing_data_clean = pioneer_crossing_data.drop_duplicates(
        subset=['intersection_id', 'date', 'time', 'direction', 'movement', 'volume'],
        keep='first'
    )
    print(f"Rows before removing duplicates: {len(pioneer_crossing_data)}")
    print(f"Rows after removing duplicates: {len(pioneer_crossing_data_clean)}")

    # Write the filtered data to a CSV file
    output_file = 'data/pioneer_crossing_filtered.csv'
    pioneer_crossing_data_clean.to_csv(output_file, index=False)
    print(f"\nFiltered data has been written to {output_file}")
    print(f"Total rows in the filtered dataset: {len(pioneer_crossing_data_clean)}")
else:
    print("\nNo duplicates found in the dataset.")
    # Write the original data to a CSV file
    output_file = 'data/pioneer_crossing_filtered.csv'
    pioneer_crossing_data.to_csv(output_file, index=False)
    print(f"\nOriginal data has been written to {output_file}")
    print(f"Total rows in the dataset: {len(pioneer_crossing_data)}")

