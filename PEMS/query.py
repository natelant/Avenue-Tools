import pandas as pd

def process_traffic_data(raw_data_df):
    # Ensure ReadingDateTime is datetime type
    try:
        if not pd.api.types.is_datetime64_any_dtype(raw_data_df['ReadingDateTime']):
            raw_data_df['ReadingDateTime'] = pd.to_datetime(raw_data_df['ReadingDateTime'])
    except Exception as e:
        print("Error converting ReadingDateTime:", e)
        print("Sample of ReadingDateTime values:", raw_data_df['ReadingDateTime'].head())
        raise

    # Query 4 (bottom query) - Sum volumes and average speeds by station and datetime
    query1_df = (raw_data_df
        .groupby(['StationID', 'ReadingDateTime'])
        .agg({
            'Volume': 'sum',
            'Speed': 'mean'
        })
        .reset_index()
        .rename(columns={
            'Volume': 'SumOfVolume',
            'Speed': 'AvgOfSpeed'
        }))

    # Query 3 - Add date parts
    query2_df = query1_df.assign(
        DayDate=query1_df['ReadingDateTime'].dt.day,
        MonthDate=query1_df['ReadingDateTime'].dt.month,
        HourDate=query1_df['ReadingDateTime'].dt.hour,
        DOW=query1_df['ReadingDateTime'].dt.weekday + 2  # Adding 1 to match SQL's 1-based weekday and 1 to match SQL starting on Sunday
    )

    # Query 2 - Daily aggregation by station, month, and day
    query3_df = (query2_df
        .groupby(['StationID', 'MonthDate', 'DayDate', 'DOW'])
        .agg({
            'SumOfVolume': 'sum',
            'AvgOfSpeed': 'mean'
        })
        .reset_index()
        .assign(
            DOW=lambda x: x['DOW'].apply(lambda d: 1 if d == 8 else d)  # Now modify DOW to match SQL
        ))

    # Query 1 - Monthly aggregation
    query4_df = (query3_df
        .groupby(['StationID', 'MonthDate'])
        .agg({
            'SumOfVolume': 'mean',
            'AvgOfSpeed': 'mean'
        })
        .reset_index()
        .rename(columns={
            'SumOfVolume': 'AvgOfSumOfSumOfVolume',
            'AvgOfSpeed': 'AvgOfAvgOfAvgOfSpeed'
        }))

    return query1_df, query2_df, query3_df, query4_df


# def monthly_figure(MonthlyAve):
#     # Determine pair of stations with the highest volumes
#     # problem: the stations are not paired together...


#     return fig, table


# def daily_figure(SumofLaneswithDates):



#     return fig, schedule


# Example usage:
# Assuming you have your raw data in a pandas DataFrame with columns:
# StationID, ReadingDateTime, Volume, Speed

raw_df = pd.read_csv('data/RawData.csv')
try:
    # Try to convert with coerce to handle any invalid dates
    raw_df['ReadingDateTime'] = pd.to_datetime(
        raw_df['ReadingDateTime'], 
        format='mixed',  # Allow mixed formats
        errors='coerce'  # Replace invalid dates with NaT
    )
    
    # Check for and report any NaT (invalid) values
    invalid_dates = raw_df[raw_df['ReadingDateTime'].isna()]
    if len(invalid_dates) > 0:
        print(f"Found {len(invalid_dates)} invalid dates:")
        print(invalid_dates)
        
    # Remove any rows with invalid dates
    raw_df = raw_df.dropna(subset=['ReadingDateTime'])
    
except Exception as e:
    print("Error converting dates:", e)
    raise

print("DataFrame info:")
print(raw_df.info())
print("\nFirst few rows:")
print(raw_df.head())

q1, q2, q3, q4 = process_traffic_data(raw_df)


print("SumofLanes")
print(q1)
print("SumofLaneswithDates")
print(q2)
print("DailyVolumesbyMonth")
print(q3)
print("DailyVolumesbyMonthAve")
print(q4)



