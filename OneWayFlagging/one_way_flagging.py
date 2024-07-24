# This tool converts a folder with .xlsm, .gpx, and .kml files
# .xlsm should have the counts from one-way flagging
# .gpx comes directly from the GPX app
# .kml should have the two stop bars (i.e. EB and WB) and the estimated "end of queue" points = so there are 4 total points from the KML file

# --------------------------------------------------------------------------------------------------------------------------------------------
# Definitions
# --------------------------------------------------------------------------------------------------------------------------------------------
# Run - from start of EB to Start of WB (i.e. odd runs are EB and even runs are WB)
#     - runs connect the count data to GPX data. Migrate the Start Stop library into the GPX data and organize by direction and time stamp



# --------------------------------------------------------------------------------------------------------------------------------------------
# imports and directories
# --------------------------------------------------------------------------------------------------------------------------------------------
import pandas as pd
import os
from datetime import datetime, time
import plotly.express as px
import plotly.graph_objects as go

# Specify the directory containing the Excel files
directory = 'data'

# --------------------------------------------------------------------------------------------------------------------------------------------
# functions
# --------------------------------------------------------------------------------------------------------------------------------------------



# --------------------------------------------------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------------------------------------------------

# Read in and combine .xlsm -> count_data

# 

# Read in .gpx -> gpx_data



# --------------------------------------------------------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------------------------------------------------------

# Write excel ouptut file ---
# Sheet 1 - raw count data (Time Stamp, Vehicle, Direction)
# Sheet 2 - raw gpx data (Time Stamp, lat, lon, speed, grade)
# Sheet 3 - summary table (Direction: Volume, Arrival rate, classification, travel time, average speed, distance, average car headway, average truck headway...)
# Sheet 4 - headway data (Truck, Car) or (Truck following Truck, Truck following Car, Car Following Car, Car Following Truck) - for histograms and box plots
# Sheet 5 - raw travel times data (Run, Route, direction, avg speed, distance, travel time, stops)
# Sheet 6 - green time summary (Run, total run time, green time, red time, average travel time, )
# Sheet 7 - start up loss time?
# Sheet REGRESSION... master data, selective data?

