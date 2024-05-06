import csv
import math
import pandas as pd
from datetime import datetime
import gpxpy

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
# Assume gpx_data is a list of dictionaries where each dictionary represents a point with keys 'lat', 'lon', and 'time'
# Parse GPX file
gpx_file = open('GPXReader/data/2100_NL.gpx', 'r')
gpx = gpxpy.parse(gpx_file)

# Extract data from GPX
gpx_data = []
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            gpx_data.append({'lat': point.latitude, 'lon': point.longitude, 'time': point.time.strftime('%Y-%m-%dT%H:%M:%SZ')})

gpx_file.close()

# Parse CSV file containing significant intersections
intersections = []
with open('GPXReader/data/routes2100.csv', 'r') as csvfile:
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

# Save output DataFrame to CSV
output_df.to_csv('GPXReader/output/travel_times_testing.csv', index=False)
