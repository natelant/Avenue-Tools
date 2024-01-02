import os
import pandas as pd
import xlsxwriter
from datetime import datetime

df = pd.read_csv('TravelTimesData/2100WB_July-Oct.csv')
df['local_datetime'] = pd.to_datetime(df['local_datetime'])


# Set 'datetime' column as the index
df.set_index('local_datetime', inplace=True)

# Extract the time component and create a new column 'hour'
df['hour'] = df.index.hour

# Calculate the hourly average travel time for each hour of the day
hourly_avg_travel_time = df.groupby(df.index.hour)['avg_travel_time'].mean().rename('hourly_average')

# Merge the hourly averages back to the original DataFrame
df_merged = pd.merge(df, hourly_avg_travel_time, left_on=df.index.hour, right_index=True, suffixes=('', '_hourly'))

# Calculate the z-score for each travel time based on the average for its respective hour
df_merged['z_score'] = (df_merged['avg_travel_time'] - df_merged['hourly_average']) / df_merged['hourly_average'].std()

# Set a threshold for outliers (e.g., z-score greater than 2 or less than -2)
outlier_threshold = 3
outliers = df_merged[(df_merged['z_score'] > outlier_threshold) | (df_merged['z_score'] < -outlier_threshold)]

# Display the outliers
print(outliers[['avg_travel_time', 'hourly_average', 'z_score']])
