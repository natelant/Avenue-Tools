import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import sqlite3

def fetch_split_monitor_data(location_id, start_date, end_date, percentile_split="85"):
    """
    Fetch split monitor data from the API
    
    Args:
        location_id (str): Location identifier
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        percentile_split (str, optional): Percentile split value. Defaults to "85"
    
    Returns:
        dict: JSON response from the API
    """
    url = "https://report-api-bdppc3riba-wm.a.run.app/v1/SplitMonitor/GetReportData"
    
    # Prepare the payload
    payload = {
        "locationIdentifier": str(location_id),
        "start": start_date,
        "end": end_date,
        "percentileSplit": percentile_split
    }
    
    # Headers based on the provided information
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def process_split_monitor_data(data):
    """
    Process the split monitor response data
    
    Args:
        data (dict): JSON response from the API
    
    Returns:
        tuple: Processed DataFrames for plans and splits
    """
    all_plans = []
    all_splits = []
    
    for intersection in data:
        if "plans" in intersection:
            for plan in intersection["plans"]:
                plan_data = {
                    "locationIdentifier": intersection.get("locationIdentifier"),
                    "phaseNumber": intersection.get("phaseNumber"),
                    "phaseDescription": intersection.get("phaseDescription"),
                    "planNumber": plan.get("planNumber"),
                    "planDescription": plan.get("planDescription"),
                    "start": plan.get("start"),
                    "end": plan.get("end"),
                    "percentSkips": plan.get("percentSkips"),
                    "percentGapOuts": plan.get("percentGapOuts"),
                    "percentMaxOuts": plan.get("percentMaxOuts"),
                    "percentForceOffs": plan.get("percentForceOffs"),
                    "averageSplit": plan.get("averageSplit"),
                    "programmedSplit": plan.get("programmedSplit"),
                    "percentileSplit50th": plan.get("percentileSplit50th"),
                    "percentileSplit85th": plan.get("percentileSplit85th")
                }
                all_plans.append(plan_data)
        
        # Programmed Splits, Gap Outs, Max Outs, Force Offs
        # but as of right now it only has programmedSplits -- trying to figure out how to loop through all of them
        if "programmedSplits" in intersection:
            for split in intersection["programmedSplits"]:
                split_data = {
                    "locationIdentifier": intersection.get("locationIdentifier"),
                    "phaseNumber": intersection.get("phaseNumber"),
                    "phaseDescription": intersection.get("phaseDescription"),
                    "type": "programmedSplits",
                    "value": split.get("value"),
                    "timestamp": split.get("timestamp")
                }
                all_splits.append(split_data)
    
    plans_df = pd.DataFrame(all_plans)
    splits_df = pd.DataFrame(all_splits)
    
    # Convert timestamp columns to datetime
    if not plans_df.empty:
        plans_df['start'] = plans_df['start'].str.split('.').str[0]  # Remove milliseconds
        plans_df['end'] = plans_df['end'].str.split('.').str[0]      # Remove milliseconds
        plans_df['start'] = pd.to_datetime(plans_df['start'])
        plans_df['end'] = pd.to_datetime(plans_df['end'])
    
    if not splits_df.empty:
        splits_df['timestamp'] = splits_df['timestamp'].str.split('.').str[0]  # Remove milliseconds
        splits_df['timestamp'] = pd.to_datetime(splits_df['timestamp'])
    
    return plans_df, splits_df

def create_database():
    """Create SQLite database and tables if they don't exist"""
    conn = sqlite3.connect('data/split_monitor.db')
    cursor = conn.cursor()
    
    # Create plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            locationIdentifier TEXT,
            phaseNumber TEXT,
            phaseDescription TEXT,
            planNumber TEXT,
            planDescription TEXT,
            start TIMESTAMP,
            end TIMESTAMP,
            percentSkips REAL,
            percentGapOuts REAL,
            percentMaxOuts REAL,
            percentForceOffs REAL,
            averageSplit REAL,
            programmedSplit REAL,
            percentileSplit50th REAL,
            percentileSplit85th REAL
        )
    ''')
    
    # Create splits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS splits (
            locationIdentifier TEXT,
            phaseNumber TEXT,
            phaseDescription TEXT,
            type TEXT,
            value REAL,
            timestamp TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_to_database(plans_df, splits_df):
    """Save DataFrames to SQLite database"""
    conn = sqlite3.connect('data/split_monitor.db')
    
    # Save to database
    plans_df.to_sql('plans', conn, if_exists='append', index=False)
    splits_df.to_sql('splits', conn, if_exists='append', index=False)
    
    conn.close()

def main():
    # Read location IDs from signals.csv
    signals_df = pd.read_csv('data/signals.csv')
    
    # Create database and tables
    create_database()
    
    # Define date range
    start = datetime(2024, 10, 29)  # Starting from January 1, 2024
    end = datetime(2024, 11, 10)    # Until January 8, 2024 (one week)
    current_date = start
    
    while current_date < end:
        # Format dates for API payload
        start_date = current_date.strftime('%Y-%m-%dT00:00:00')
        end_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')
        
        print(f"\nProcessing date: {start_date[:10]}")  # Print just the date part for clarity
        
        # Loop through each location ID
        for location_id in signals_df['Signal_ID']:
            print(f"  Location ID: {location_id}", end='')
            
            # Fetch data
            data = fetch_split_monitor_data(str(location_id), start_date, end_date)
            
            if data:
                # Process data
                plans_df, splits_df = process_split_monitor_data(data)
                
                # Save to database
                save_to_database(plans_df, splits_df)
                print(" ✓")  # Checkmark for success
            else:
                print(" ✗")  # X mark for failure
        
        # Move to next day
        current_date += timedelta(days=1)

if __name__ == "__main__":
    main()
