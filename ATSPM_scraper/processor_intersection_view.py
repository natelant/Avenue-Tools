import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def get_intersection_plan_data(intersection_id: int, plan_id: int) -> pd.DataFrame:
    """
    Retrieve plan data for a specific intersection and plan from split_monitor.db
    
    Args:
        intersection_id: The ID of the intersection
        plan_id: The ID of the plan to query
        
    Returns:
        DataFrame containing the plan data
    """
    # Connect to the database
    conn = sqlite3.connect('data/split_monitor.db')
    
    # SQL query to get plan data for specific intersection and plan
    query = """
    SELECT *
    FROM plans
    WHERE locationIdentifier = ? AND planNumber = ?
    ORDER BY start
    """
    
    try:
        # Read data into pandas DataFrame
        df = pd.read_sql_query(query, conn, params=(intersection_id, plan_id))
        return df
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return pd.DataFrame()
        
    finally:
        conn.close()

def get_split_failure_data(intersection_id: int, plan_id: int) -> pd.DataFrame:
    """
    Retrieve split failure data for a specific intersection and plan from split_monitor.db
    """

    # Connect to the database
    conn = sqlite3.connect('data/split_failure.db')
    
    # SQL query to get plan data for specific intersection and plan
    query = """
    SELECT *
    FROM plans
    WHERE locationIdentifier = ? AND planNumber = ?
    ORDER BY start
    """
    
    try:
        # Read data into pandas DataFrame
        df = pd.read_sql_query(query, conn, params=(intersection_id, plan_id))
        return df
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return pd.DataFrame()
        
    finally:
        conn.close()

if __name__ == "__main__":
    # Example usage
    locationIdentifier = 7351  # Replace with your intersection ID
    planNumber = 1         # Replace with your plan ID
    
    df = get_intersection_plan_data(locationIdentifier, planNumber)
    
    if not df.empty:
        print(f"Found {len(df)} records")
        print("\nFirst few records:")
        print(df)
    else:
        print("No data found for the specified intersection and plan")

    

    # Calculate the time of day for the given plan
    df['startTime'] = pd.to_datetime(df['start'])
    df['endTime'] = pd.to_datetime(df['end'])
    
    # Extract just the time as strings in HH:MM format
    df['start_time_str'] = df['startTime'].dt.strftime('%H:%M')
    df['end_time_str'] = df['endTime'].dt.strftime('%H:%M')
    
    # Create time range strings and get unique values
    df['time_range'] = df['start_time_str'] + ' - ' + df['end_time_str']
    time_of_day = df['time_range'].unique()
    
    print("\nTime of Day:")
    print(time_of_day)

    # average only the numeric columns for each plan and phase
    numeric_columns = ['programmedSplit', 'averageSplit', 'percentileSplit50th', 'percentileSplit85th', 'percentSkips', 'percentGapOuts', 'percentForceOffs']
    df = df.groupby(['locationIdentifier', 'planNumber', 'phaseNumber'])[numeric_columns].mean().reset_index()

    split_failure_data = get_split_failure_data(locationIdentifier, planNumber)
    split_failure_data = split_failure_data.groupby(['locationIdentifier', 'planNumber', 'phaseNumber', 'approachDescription'])['percentFails'].mean().reset_index()

    # filter out the phases that have "Ov" or "(" in the approachDescription
    split_failure_data = split_failure_data[~split_failure_data['approachDescription'].str.contains(r'Ov|\(', regex=True)]

    # merge the split failure data with the intersection plan data
    df = pd.merge(df, split_failure_data, on=['locationIdentifier', 'planNumber', 'phaseNumber'], how='left')

    # Calculate cycle length by summing programmed splits
    cycle_length = df.groupby(['locationIdentifier', 'planNumber'])['programmedSplit'].sum().iloc[0] / 2
    print("\nCycle Length:")
    print(cycle_length)

    # Calculate percentages using the scalar cycle_length value
    df['perc_avg_split'] = df['averageSplit'] / cycle_length * 100
    df['perc_prog_split'] = df['programmedSplit'] / cycle_length * 100
    df['perc_50th_split'] = df['percentileSplit50th'] / cycle_length * 100
    df['perc_85th_split'] = df['percentileSplit85th'] / cycle_length * 100

    print(df)

    # Create the plot
    ax = df.plot(kind='bar', x='phaseNumber', 
                 y=['percentFails', 'perc_prog_split', 'perc_avg_split', 'perc_50th_split', 'perc_85th_split', 
                    'percentGapOuts', 'percentForceOffs', 'percentSkips'], 
                 figsize=(10, 5))
    
    # Add titles and labels
    plt.title(f'Split Analysis for Intersection {locationIdentifier}, Plan {planNumber}', 
             fontsize=12, pad=15)
    plt.suptitle(f'Cycle Length: {cycle_length}, Time of Day: {time_of_day[0]}', 
                 fontsize=10, y=0.95)
    plt.xlabel('Phase Number', fontsize=10)
    plt.ylabel('Percentage (%)', fontsize=10)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    plt.show()
