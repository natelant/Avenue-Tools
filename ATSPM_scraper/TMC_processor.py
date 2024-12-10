import pandas as pd
import plotly.express as px
import sqlite3

# Connect to the database
conn = sqlite3.connect('data/PaysonMOT_6226_TMC.db')

# Select both date and time columns
query = "SELECT date, time, direction, movement, volume FROM tmc_data_detailed"
df = pd.read_sql_query(query, conn)

# Clean the direction column and handle movement conditions
df['direction'] = df['direction'].replace({
    'Eastbound': 'Westbound',
    'Westbound': 'Northbound',
    'Northbound': 'Southbound'
})

# Update movements based on conditions
mask_westbound_R = (df['direction'] == 'Westbound') & (df['movement'] == 'T')
mask_northbound_T = (df['direction'] == 'Northbound') & (df['movement'] == 'L')
mask_northbound_R = (df['direction'] == 'Northbound') & (df['movement'] == 'T')

df.loc[mask_westbound_R, 'movement'] = 'R'
df.loc[mask_northbound_T, 'movement'] = 'T'
df.loc[mask_northbound_R, 'movement'] = 'R'

# Combine date and time columns into a single datetime column
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])


# ------------------------------------------------------------
# Visualize the raw TMC data
# Create interactive scatter plot with plotly
# fig = px.scatter(df, 
#                  x='datetime', 
#                  y='volume',
#                  color='direction',
#                  title='Traffic Volume Over Time',
#                  labels={'datetime': 'Date/Time', 'volume': 'Volume'},
#                  template='plotly_white')  # Clean white template

# # Update layout for better readability
# fig.update_layout(
#     xaxis_title="Date/Time",
#     yaxis_title="Volume",
#     xaxis=dict(showgrid=True),  # Correct way to show grid for x-axis
#     yaxis=dict(showgrid=True)   # Correct way to show grid for y-axis
# )

# # Show the plot
# fig.show()

# ------------------------------------------------------------
# put into PeMS format
# Create separate dataframes for south and north directions
south_df = df[df['direction'] == 'Southbound'].groupby(['datetime'])['volume'].sum().reset_index()
south_df['direction'] = 'South'

north_movements = df[
    ((df['direction'] == 'Northbound') & (df['movement'] == 'T')) |
    ((df['direction'] == 'Westbound') & (df['movement'].isin(['R'])))]
north_df = north_movements.groupby(['datetime'])['volume'].sum().reset_index()
north_df['direction'] = 'North'

# Combine north and south dataframes
pems_format = pd.concat([north_df, south_df], ignore_index=True)

print(pems_format)

# Filter out data before 2023-08-06 
pems_format = pems_format[(pems_format['datetime'] >= '2023-08-06')] # & (pems_format['datetime'] <= '2023-12-12')]

# create new columns to match PeMS format
pems_format['StationID'] = '6226' + '_' + pems_format['direction']
pems_format['ReadingDateTime'] = pems_format['datetime']
pems_format['SumOfVolume'] = pems_format['volume']
pems_format['DayDate'] = pems_format['datetime'].dt.day # this should be an integer of the date
pems_format['MonthDate'] = pems_format['datetime'].dt.month # this should be an integer of the month
pems_format['HourDate'] = pems_format['datetime'].dt.hour # this should be an integer of the hour
pems_format['DOW'] = (pems_format['datetime'].dt.dayofweek + 1) % 7 + 1

# Create daily volumes by month (equivalent to first query)
daily_volumes = pems_format.groupby(['StationID', 'MonthDate', 'DayDate', 'DOW'])['SumOfVolume'].sum().reset_index()
daily_volumes = daily_volumes.rename(columns={'SumOfVolume': 'SumOfSumOfVolume'})

# Create monthly averages (equivalent to second query)
monthly_format = daily_volumes.groupby(['StationID', 'MonthDate'])['SumOfSumOfVolume'].mean().reset_index()
monthly_format = monthly_format.rename(columns={'SumOfSumOfVolume': 'AvgOfSumOfSumOfVolume'})

# write df and pems_format to excel
with pd.ExcelWriter('data/6226_TMC.xlsx') as writer:
    df.to_excel(writer, sheet_name='TMC_data', index=False)
    pems_format.to_excel(writer, sheet_name='Daily_format', index=False)
    monthly_format.to_excel(writer, sheet_name='Monthly_format', index=False)

# Create interactive scatter plot with plotly
fig = px.scatter(pems_format, 
                 x='datetime', 
                 y='volume',
                 color='direction',
                 title='Traffic Volume Over Time',
                 labels={'datetime': 'Date/Time', 'volume': 'Volume'},
                 template='plotly_white')  # Clean white template

# Update layout for better readability
fig.update_layout(
    xaxis_title="Date/Time",
    yaxis_title="Volume",
    xaxis=dict(showgrid=True),  # Correct way to show grid for x-axis
    yaxis=dict(showgrid=True)   # Correct way to show grid for y-axis
)

# Show the plot
fig.show()

# Close database connection
conn.close()
