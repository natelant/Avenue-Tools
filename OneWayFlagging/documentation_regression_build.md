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
* Identifying 'Start' and 'Stop' time stamps to separate them from the vehicle count data
* Calculating headway by subtracting the timestamp of the previous vehicle from the current vehicle's timestamp

## General Definitions
* **Split**: The time from start of green in one direction to start of green in the opposite direction.
* **Previous Split**: The time from start of green in the opposite direction to start of green in the current direction.
* **Green Time**: The time difference between the stop time and the start time of a split.
* **Red Time**: The time from red (stop) to green (start) in a single direction. This is the time that a single direction is waiting at red. 
* **Previous Red Time**: The time difference between the previous stop time to the current start time in a single direction.
* **Cycle Length**: In this context, Cycle Length is the sum of the Previous Red Time and Green Time for each split.
* **Previous Red Clearance Time**: The all red time from the previous stop in the opposite direction to the current start time in the current direction.
* **After Green All Red**: The all red clearance time from the stop of the current direction to the start of the opposite direction.

## Calculations
The script performs the following calculations:

* **Volume**: The total count of vehicles during each Green Time.
* **Truck Percentage**: The percentage of trucks in the total volume for each Green Time.
* **Average Headway**: The average time difference between vehicles during each Green Time.
* **Cycles Per Hour**: The number of cycles that occur in an hour, calculated as 3600 divided by the cycle length.
* **Green Time Per Hour**: The total green time in an hour, calculated as cycles per hour multiplied by green time.
* **Red Time Per Hour**: The total red time in an hour, calculated as cycles per hour multiplied by previous red time.
* **After Green All Red Per Hour**: The total all red time after green in an hour, calculated using an adjusted cycle length. The equation is (3600 / (green time + previous split + after green all red)) * After Green All Red.
* **Hourly Flow Rate Green**: The hourly flow rate during green time, calculated as 3600 divided by average headway.
* **Hourly Flow Rate Red**: The hourly flow rate during red time, calculated as volume multiplied by cycles per hour.
* **Total Volume**: The total count of vehicles for each direction over a specified time period.
* **Total Hours**: The total time spent collecting data for each direction.
* **Volume Per Hour**: The total volume divided by the total hours for each direction.

## Data Merging and Output
The script merges the preprocessed data with the segment information and intersection data. The final output includes:

* **Counts DataFrame**: A DataFrame containing volume, truck percentage, and average headway for each split ID, direction, and route name.
* **Splits DataFrame**: A DataFrame containing split ID, green time, red time, and start time for each split.
* **Hourly Summary DataFrame**: A DataFrame containing total volume, total hours, and volume per hour for each direction and route name.

The script outputs these DataFrames for further analysis and visualization.
