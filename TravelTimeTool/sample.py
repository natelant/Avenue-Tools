import pandas as pd
from datetime import datetime

def calculate_average_travel(input_data, start_time, stop_time):
    # Read the input data into a DataFrame
    df = pd.read_csv(input_data, parse_dates=['local_datetime'])

    # Filter data based on peak hour range
    peak_hour_mask = (df['local_datetime'].dt.time >= start_time) & (df['local_datetime'].dt.time <= stop_time)
    peak_hour_data = df[peak_hour_mask]

    # Calculate the average travel time during the peak hour
    average_travel_time = peak_hour_data['avg_travel_time'].mean()

    print(f"Average travel time during peak hours ({start_time} to {stop_time}): {average_travel_time:.2f} {peak_hour_data['avg_travel_time_units'].iloc[0]}")

if __name__ == "__main__":
    # Provide the path to your input data file
    input_data_file = input("Enter the path to the input data file: ")
    
    # Prompt the user to enter the peak hour start time and stop time
    start_time_str = input("Enter peak hour start time (HH:MM): ")
    stop_time_str = input("Enter peak hour stop time (HH:MM): ")

    # Convert input times to datetime.time objects
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    stop_time = datetime.strptime(stop_time_str, "%H:%M").time()

    

    # Call the function to calculate average travel time
    calculate_average_travel(input_data_file, start_time, stop_time)
