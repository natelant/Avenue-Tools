# GPX Travel Times Tool

## File Requirements

- A folder of GPX files
- A CSV or KML file containing significant intersection information

## Installation

Make sure you have Python installed. Then, install the required packages 
using the following command: `pip install -r requirements.txt`.


## Running the Script

To run the gpx_travel_times.py file in the command line, follow these steps:

1. Open your command line interface (right click and select "Open in Terminal").
2. Navigate to the directory where the gpx_travel_times.py file is located.
3. Run the following command: `python gpx_travel_times.py [options]` or answer the prompts in the command line.
4. Note that your file path can be a relative path, for example `data/` or `.`. If your files are in a parent folder, 
your relative path may look like `../GPX/` or something like that. The `../` means go up one directory.
5. The output file will be saved to the `output` folder as a CSV.
