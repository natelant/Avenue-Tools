import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def calculate_avg_arrivals_on_green(start_time, end_time):
    conn = sqlite3.connect('purdue_coordination_diagram.db')
    
    query = """
    SELECT intersection_id, phase, 
           AVG(percent_arrivals_on_green) as avg_percent
    FROM plans
    WHERE timestamp BETWEEN ? AND ?
    GROUP BY intersection_id, phase
    """
    
    df = pd.read_sql_query(query, conn, params=(start_time, end_time))
    conn.close()
    
    return df

# Define time windows
window1_start = datetime(2023, 1, 1, 0, 0)
window1_end = datetime(2023, 1, 31, 23, 59)
window2_start = datetime(2023, 2, 1, 0, 0)
window2_end = datetime(2023, 2, 28, 23, 59)

# Calculate averages for both windows
df1 = calculate_avg_arrivals_on_green(window1_start, window1_end)
df2 = calculate_avg_arrivals_on_green(window2_start, window2_end)

# Compare results
comparison = pd.merge(df1, df2, on=['intersection_id', 'phase'], suffixes=('_w1', '_w2'))
comparison['difference'] = comparison['avg_percent_w2'] - comparison['avg_percent_w1']

print(comparison)