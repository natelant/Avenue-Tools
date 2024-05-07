import os
import gpxpy
import csv
import math
import pandas as pd
from datetime import datetime

# Function to parse CSV file containing significant intersection information
def parse_csv(csv_file):
    intersections = []
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            intersections.append({'route_id': row['routeID'], 'segment_id': row['segmentID'], 'lat': float(row['x']), 'lon': float(row['y'])})
    return intersections

# Function to calculate distance between two points using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    # Haversine formula implementation
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

# Function to calculate travel time between two timestamps
def calculate_travel_time(start_time, end_time):
    start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
    return (end_datetime - start_datetime).total_seconds()

# Function to find closest significant intersection for a given point
def find_closest_intersection(point, intersections):
    # Iterate over each significant intersection to find the closest one
    ...

# Function to parse GPX file and calculate travel times
def parse_gpx_file(gpx_file, intersections):
    gpx_data = []
    # Parse the GPX file
    with open(gpx_file, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        # Extract data from GPX
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    gpx_data.append({'lat': point.latitude, 'lon': point.longitude, 'time': point.time.strftime('%Y-%m-%dT%H:%M:%SZ')})

    # Initialize variables
    output_data = []  # Initialize output data list
    prev_intersection = None  # Initialize previous intersection

    # Iterate through each point in GPX data
    for point in gpx_data:
        closest_intersection = None
        # Iterate through each significant intersection
        for intersection in intersections:
            # Calculate the distance between the current point and the intersection
            distance = haversine(point['lat'], point['lon'], intersection['lat'], intersection['lon'])
            # Check if the distance is within the threshold (50 feet)
            if distance <= 15:  # 50 feet in meters
                closest_intersection = intersection
                # Assign the time of the current point to the closest intersection
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

    # Convert output data to DataFrame
    output_df = pd.DataFrame(output_data)
    return output_df


# Parse CSV file to extract significant intersection information
csv_file = 'GPXReader/data/routes.csv'
intersections = parse_csv(csv_file)

# Iterate over each GPX file
folder_path = 'GPXReader/data/'
all_results = []
for filename in os.listdir(folder_path):
    if filename.endswith('.gpx'):  # Check if the file is a GPX file
        gpx_file = os.path.join(folder_path, filename)
        # Parse GPX file and calculate travel times
        result = parse_gpx_file(gpx_file, intersections)
        result['route'] = os.path.splitext(filename)[0]  # Extract route name from filename
        all_results.append(result)

# Concatenate all results together
final_result = pd.concat(all_results, ignore_index=True)

# Format into table
# Step 1: Filter out rows where segment_start equals segment_finish
filtered_df = final_result[final_result['segment_start'] != final_result['segment_finish']]
# Add a new column indicating the order of occurrence for each combination
filtered_df['route'] = filtered_df['segment_start'] + '_to_' + filtered_df['segment_finish']
filtered_df['run_number'] = filtered_df.groupby('route').cumcount() + 1

# Pivot the table based on the new column 'run_number'
pivoted_df = filtered_df.pivot_table(index='route', columns='run_number', values='travel_time', aggfunc='first')

# Calculate the average travel time across runs
pivoted_df['average'] = pivoted_df[[1, 2, 3, 4, 5]].mean(axis=1)

# Calculate the standard deviation of travel times across runs
pivoted_df['std_deviation'] = pivoted_df[[1, 2, 3, 4, 5]].std(axis=1)

# Output the total table of all calculated travel times
print(pivoted_df)
