import csv
import math
import pandas as pd
from datetime import datetime
import gpxpy
import os

# Function to calculate distance between two points using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

# Function to find the closest significant intersection for a given point
def find_closest_intersection(point, intersections):
    min_distance = float('inf')
    closest_intersection = None
    for intersection in intersections:
        distance = haversine(point['lat'], point['lon'], intersection['lat'], intersection['lon'])
        if distance < min_distance:
            min_distance = distance
            closest_intersection = intersection
    return closest_intersection

# Function to calculate travel time between two timestamps
def calculate_travel_time(start_time, end_time):
    start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
    return (end_datetime - start_datetime).total_seconds()

# Parse GPX file


# Function to parse GPX files in a folder
def parse_gpx_files(folder_path):
    gpx_data = []
    # Iterate over each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.gpx'):  # Check if the file is a GPX file
            file_path = os.path.join(folder_path, filename)
            # Parse the GPX file
            with open(file_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                # Extract data from GPX
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            gpx_data.append({'lat': point.latitude, 'lon': point.longitude, 'time': point.time.strftime('%Y-%m-%dT%H:%M:%SZ')})
    return gpx_data

# Example usage
folder_path = 'GPXReader/data/'
gpx_data = parse_gpx_files(folder_path)


# Parse CSV file containing significant intersections
intersections = []
with open('GPXReader/data/routes.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        intersections.append({'route_id': row['routeID'], 'segment_id': row['segmentID'], 'lat': float(row['x']), 'lon': float(row['y'])})

# Initialize variables
prev_intersection = None
output_data = []

# Iterate through each point in GPX data
for point in gpx_data:
    closest_intersection = None
    # Iterate through each significant intersection
    for intersection in intersections:
        # Calculate the distance between the current point and the intersection
        distance = haversine(point['lat'], point['lon'], intersection['lat'], intersection['lon'])
        # Check if the distance is within the threshold (100 feet)
        if distance <= 15:  # 50 feet in meters
            closest_intersection = intersection
            # assign the time of the current point to the closest intersection
            closest_intersection['time'] = point['time']
            break  # Exit the loop if a significant intersection is found within the threshold
    # If a closest intersection is found within the threshold, process it
    if closest_intersection:
        if prev_intersection:
            # Calculate travel time between the previous intersection and the current closest intersection
            travel_time = calculate_travel_time(prev_intersection['time'], point['time'])
            # Store the segment start, segment finish, and travel time in the output data
            output_data.append({'segment_start': prev_intersection['segment_id'], 'segment_finish': closest_intersection['segment_id'], 'travel_time': travel_time})
        prev_intersection = closest_intersection
    else:
        # If no significant intersection is found within the threshold, skip to the next point
        continue



# Convert output data to DataFrame
output_df = pd.DataFrame(output_data)

print(output_df)

# Format into table
# Step 1: Filter out rows where segment_start equals segment_finish
filtered_df = output_df[output_df['segment_start'] != output_df['segment_finish']]
# Add a new column indicating the order of occurrence for each combination
filtered_df['route'] = filtered_df['segment_start'] + '_to_' + filtered_df['segment_finish']
filtered_df['run_number'] = filtered_df.groupby('route').cumcount() + 1

# Pivot the table based on the new column 'run_number'
pivoted_df = filtered_df.pivot_table(index='route', columns='run_number', values='travel_time', aggfunc='first')

# Calculate the average travel time across runs
pivoted_df['average'] = pivoted_df[[1, 2, 3, 4, 5]].mean(axis=1)

# Calculate the standard deviation of travel times across runs
pivoted_df['std_deviation'] = pivoted_df[[1, 2, 3, 4, 5]].std(axis=1)


print(pivoted_df)

# Save output DataFrame to CSV
# output_df.to_csv('GPXReader/output/travel_times_testing.csv', index=False)


