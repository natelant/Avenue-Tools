# This analysis will clean and process all one-way flagging (OWF) data
# Build analysis before building the report.
# play with data, run the calculations

import pandas as pd
import os
from datetime import datetime, time
import plotly.express as px
import plotly.graph_objects as go

# Specify the directory containing the Excel files
directory = 'data'

# write fucntion to convert Time Stamp to a datetime variable
def time_to_datetime(t):
    return datetime.combine(datetime.today(), t)

# function that cleans the excel files
def clean_xlsm(file_path):
    file_path = os.path.join(directory, filename)
        # Read the Excel file into a dataframe
    df = pd.read_excel(file_path)
    
    # Filter out invalid segments between multiple 'Start's without an intervening 'Stop'
    segments = []
    start_idx = None
    valid_segment = True

    for i, row in df.iterrows():
        if row['Vehicle'] == 'Start':
            if start_idx is not None:
                # Exclude the segment if 'Start' is immediately followed by 'Stop'
                if i == start_idx + 1 and df.loc[i, 'Vehicle'] == 'Stop':
                    start_idx = None
                    valid_segment = False
                    continue
            start_idx = i
            valid_segment = True
        elif row['Vehicle'] == 'Stop':
            if start_idx is not None:
                # Include only segments with valid data between 'Start' and 'Stop'
                if valid_segment:
                    segments.append(df.loc[start_idx:i])
            start_idx = None
            valid_segment = False

    # Concatenate valid segments into a single DataFrame
    if segments:
        cleaned = pd.concat(segments)
    else:
        cleaned = pd.DataFrame(columns=file_path.columns)

    return cleaned 


# List to hold dataframes
df_list = []

# Iterate over all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".xlsm"):
        # run clean function
        clean_df = clean_xlsm(filename)
        # Append the dataframe to the list
        df_list.append(clean_df)

# Concatenate all dataframes in the list into a single dataframe
combined_df = pd.concat(df_list, ignore_index=True)
columns = ['Time Stamp', 'Vehicle', 'Direction']
df = combined_df[columns]

# !!!!!!!!!!!!! I may need to order by time stamp... frick maybe I want to clean each one before combining. or analyze one at a time. or group by Direction and solves that issue...
# Sort the DataFrame by timestamp and Remove rows with NA values in the 'time stamp' column
filtered_df = df.sort_values('Time Stamp').dropna(subset=['Time Stamp'])

# Convert 'time stamp' to datetime for continuous axis plotting
filtered_df['Timestamp'] = filtered_df['Time Stamp'].apply(time_to_datetime)

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

# Create the 'route number' column
run = 0
runs = []

for i, row in filtered_df.iterrows():
    if row['Vehicle'] == 'Start':
        run += 1
    runs.append(run)

filtered_df['Run'] = runs




# --------------------------------------------
# Now see the average time from start to stop (run time). Visualize histogram to ensure data is clean

def time_to_seconds(t):
    return t.hour * 3600 + t.minute * 60 + t.second



# Calculate the 'Headway' column
filtered_df['Headway'] = filtered_df['Time Stamp'].apply(time_to_seconds).diff()
# Create the 'Following' column by shifting the 'classification' column
filtered_df['Following'] = filtered_df['Vehicle'].shift(1).apply(lambda x: 'Car' if x == 'Probe' else x)

# Define a function to determine the 'Group' value based on conditions
def determine_group(row):
    if row['Vehicle'] == 'Truck' and row['Following'] == 'Truck':
        return 'Truck Following Truck'
    elif row['Vehicle'] == 'Car' and row['Following'] == 'Truck':
        return 'Car Following Truck'
    elif row['Vehicle'] == 'Truck' and row['Following'] == 'Car':
        return 'Truck Following Car'
    elif row['Vehicle'] == 'Car' and row['Following'] == 'Car':
        return 'Car Following Car'
    else:
        return None

# Create the 'Group' column using the determine_group function
filtered_df['Group'] = filtered_df.apply(determine_group, axis=1)

# Assign Nan to 'Headway' for rows where classification is 'stop' or 'start'
filtered_df.loc[filtered_df['Vehicle'] == 'Stop', 'Headway'] = float('nan')
filtered_df.loc[filtered_df['Vehicle'] == 'Start', 'Headway'] = float('nan')

print(filtered_df.head(60))

# Create a bar chart using Plotly
fig = px.bar(filtered_df, x='Timestamp', y='Headway', 
             title='Headway Over Time - Visualize the Data Collection',
             # labels={'Time Stamp': 'Time Stamp', 'Headway': 'Headway (seconds)'},
             hover_data={'Time Stamp': True, 'Headway': True, 'Group': True, 'Timestamp': False},
             color='Direction',  # Color bars by vehicle classification
             color_discrete_map={'EB': 'purple', 'WB': 'pink', 'NB': 'Orange', 'SB': 'blue'})  # Example color mapping

# Add vertical lines for 'start' and 'stop'
for _, row in filtered_df.iterrows():
    if row['Vehicle'] == 'Start':
        fig.add_vline(x=row['Timestamp'], line=dict(color='green', width=2))
    elif row['Vehicle'] == 'Stop':
        fig.add_vline(x=row['Timestamp'], line=dict(color='red', width=2))

# this solves the problem of looking faded. Something to do with the lines in between the bars. Going to be rough when I introduce a second direction
# fig.update_traces(marker_color='blue',
#                   marker_line_color='blue',
#                   selector=dict(type="bar"))

# Show the plot - this shows the quality of the data
fig.show()


# --------------------------------------------------------------
# --------------------------------------------------------------
# tables and data analysis

## HEADWAY ---------------------

# drop NA values out of headway

# Create a histogram to compare different types in Classification with Headway
hist_fig = go.Figure()

# Add a histogram trace for each classification type
for vehicle in filtered_df['Vehicle'].unique():
    filtered_data = filtered_df[filtered_df['Vehicle'] == vehicle]
    hist_fig.add_trace(go.Histogram(
        x=filtered_data['Headway'],
        name=vehicle,
        opacity=0.75,
        nbinsx=10  # Adjust the number of bins as needed
    ))

# Update layout to add titles and legends
hist_fig.update_layout(
    title='Histogram of Headway Times by Classification',
    xaxis_title='Headway (seconds)',
    yaxis_title='Count',
    barmode='overlay',  # Overlay histograms to compare distributions
    legend_title='Classification',
    template='plotly_white'
)

# Show the plot
hist_fig.show()

