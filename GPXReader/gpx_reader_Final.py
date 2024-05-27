# this script is a copy paste from gpx_command_line_calculator
# It includes an addition of kml functionality
# It includes the option to read in csv or kml or kmz for intersection dictionary

# this script will read in gpx files and a significant intersection file (csv or kml) and find travel times on segments between significant intersections

import os
import gpxpy
import csv
import math
import pandas as pd
from datetime import datetime
from fastkml import kml
import zipfile

# Function to parse CSV file containing significant intersection information
def parse_csv(csv_file):
    intersections = []
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            intersections.append({
                'route_id': row['routeID'], 
                'segment_id': row['segmentID'], 
                'lat': float(row['x']), 
                'lon': float(row['y'])})
    return intersections

# Function to convert KMZ to KML and return the path to the KML file
def convert_kmz_to_kml(kmz_file):
    with zipfile.ZipFile(kmz_file, 'r') as kmz:
        for file_name in kmz.namelist():
            if file_name.endswith('.kml'):
                kmz.extract(file_name, os.path.dirname(kmz_file))
                return os.path.join(os.path.dirname(kmz_file), file_name)
    return None

# function to parse KML file containing significant intersection information
# ------------------
def parse_kml(kml_file):
    intersections = []
    
    with open(kml_file, 'rb') as file:
        doc = file.read()
        k = kml.KML()
        k.from_string(doc)
        
        # Assuming the KML has a single document
        for document in k.features():
            for folder in document.features():
                for feature in folder.features():
                    if isinstance(feature, kml.Placemark):
                        geometry = feature.geometry
                        if geometry:
                            if geometry.geom_type == 'Point':
                                coordinates = list(geometry.coords)[0]
                                intersections.append({
                                    'route_id': feature.name,
                                    'segment_id': feature.name,
                                    #'description': feature.description if feature.description else '',
                                    'lat': coordinates[1],
                                    'lon': coordinates[0]
                                })
                            """
                            elif geometry.geom_type == 'LineString':
                                for coord in geometry.coords:
                                    intersections.append({
                                        'route_id': feature.name,
                                        'segment_id': feature.name,
                                        'lat': coord[1],
                                        'lon': coord[0]
                                    })
                            """
    return intersections
#-------------------

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
                output_data.append({'route_ID': prev_intersection['route_id'] + ' / ' + closest_intersection['route_id'], 'segment_start': prev_intersection['segment_id'], 'segment_finish': closest_intersection['segment_id'], 'travel_time': travel_time})
            prev_intersection = closest_intersection

    # Convert output data to DataFrame
    output_df = pd.DataFrame(output_data)
    return output_df


def main():
    # Branding and instructions:

    
    # Prompt the user to input file paths
    intersection_file = "GPXReader/data/Signal Map.kmz" # input("Enter the file path to the significant intersections CSV or KML file: ") 
    folder_path = "GPXReader/data" #input("Enter the folder path to the GPX files: ")
    output_file = "GPXReader/output/memorialday_kmz_tests1.csv" #input("Enter the name of the output CSV file (i.e. output/AM_before.csv): ")

    # Determine if file path to significant intersections is CSV or KML
    file_extension = os.path.splitext(intersection_file)[1].lower()
    intersections = None

    if file_extension == '.csv':
        # Parse CSV file to extract significant intersection information
        intersections = parse_csv(intersection_file)
    elif file_extension == '.kml':
        # parse KML file to extract significant intersection information
        intersections = parse_kml(intersection_file)
    elif file_extension == '.kmz':
        # convert KMZ to KML 
        new_kml_file = convert_kmz_to_kml(intersection_file)
        # parse KML to extract significant intersection information
        intersections = parse_kml(new_kml_file)
    else:
        print("No KML content found in the file.")

    # Iterate over each GPX file
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
    filtered_df.loc[:,'route'] = filtered_df['segment_start'] + '_to_' + filtered_df['segment_finish']
    filtered_df['run_number'] = filtered_df.groupby('route').cumcount() + 1

    # Pivot the table based on the new column 'run_number'
    pivoted_df = filtered_df.pivot_table(index=['route_ID', 'route'], columns='run_number', values='travel_time', aggfunc='first')

    # Get the maximum run number
    max_run_number = pivoted_df.columns.max()

    # Calculate the average travel time across runs
    pivoted_df['average'] = pivoted_df.iloc[:, 1:max_run_number + 1].mean(axis=1)


    # Calculate the standard deviation of travel times across runs
    pivoted_df['std_deviation'] = pivoted_df.iloc[:, 1:max_run_number + 1].std(axis=1)

    # Output the total table of all calculated travel times
    print(pivoted_df)

    # Write the output table to a CSV file
    
    pivoted_df.to_csv(output_file)
    print(f"Output table has been written to {output_file}")


if __name__ == "__main__":
    main()
