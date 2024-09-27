# Regression Table Build Documentation
This document outlines the process and calculations used in the `regression_table_build.py` file to generate regression tables for traffic analysis.

## Data Preparation
The script begins by reading files from a specified folder path. The files include:

* `gpx` file for GPS data
* `kml` file for intersection data
* `xlsm` files for traffic count data

The script then parses the `gpx` file to extract segment information, including segment ID, average speed, average grade, and total distance. The `kml` file is parsed to extract intersection data.

## Data Cleaning and Preprocessing
The script cleans and preprocesses the traffic count data from the `xlsm` files. This includes:

* Converting 'Vehicle' column to lowercase for consistency
* Changing 'Probe' or 'probe' to 'Car' in the 'Vehicle' column
* Identifying 'Start' and 'Stop' vehicles to separate them from other vehicles
* Calculating headway by subtracting the timestamp of the previous vehicle from the current vehicle's timestamp

## Calculations
The script performs the following calculations:

* **Volume**: The total count of vehicles for each split ID, direction, and route name.
* **Truck Percentage**: The percentage of trucks in the total volume for each split ID, direction, and route name.
* **Average Headway**: The average time difference between vehicles for each split ID, direction, and route name.
* **Split Time**: The time difference between the start time of the opposite direction and the start time of the current direction.
* **Previous Split Time**: The time difference between the start time of the current split and the start time of the previous split.
* **Green Time**: The time difference between the stop time and the start time of a split.
* **Previous Red Time**: The time difference between the start time and the stop time of the previous split.
* **Previous Red Clearance Time**: The time difference between the start time of the current split and the stop time of the previous split.
* **Total Volume**: The total count of vehicles for each direction and route name over a specified time period.
* **Total Hours**: The total time in hours for each direction and route name over a specified time period.
* **Volume Per Hour**: The total volume divided by the total hours for each direction and route name.

## Data Merging and Output
The script merges the preprocessed data with the segment information and intersection data. The final output includes:

* **Counts DataFrame**: A DataFrame containing volume, truck percentage, and average headway for each split ID, direction, and route name.
* **Splits DataFrame**: A DataFrame containing split ID, green time, red time, and start time for each split.
* **Hourly Summary DataFrame**: A DataFrame containing total volume, total hours, and volume per hour for each direction and route name.

The script outputs these DataFrames for further analysis and visualization.
