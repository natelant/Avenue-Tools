# Avenue-Tools

Fire tools for Avenue project management and development.

## Description

Avenue-Tools is a collection of utilities and scripts designed to streamline the signal operations processes for Avenue projects. These tools aim to enhance productivity and simplify common tasks related to traffic analysis and signal timing.

## Features

- GPX Travel Time Calculator: Analyzes GPX files to calculate travel times between significant intersections.
- GPX Observations: Creates contour speed maps using GPX files from various vehicles.
- Turning Movement Count Reader: Processes and visualizes turning movement count data.


## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/Avenue-Tools.git
   ```
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### GPX Travel Time Calculator

Input the paths to the GPX folder and KML file when prompted.

### Turning Movement Count Reader

Open the `Sandbox/TurningMovementCountReader.ipynb` notebook in Jupyter to analyze turning movement count data.

## Dependencies

- pandas
- matplotlib
- plotly
- gpxpy
- folium
- pytz
- kml2geojson

## Contributing

Contributions to Avenue-Tools are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request


## Contact

For support or inquiries, please contact Nate Lant at [natelant@gmail.com].
