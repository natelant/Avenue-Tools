from fastkml import kml

# Function to read KML content from a KML file
def read_kml(kml_path):
    with open(kml_path, 'rb') as file:
        kml_content = file.read()
    return kml_content

# Function to parse KML content and extract data
def parse_kml(kml_content):
    k = kml.KML()
    k.from_string(kml_content)
    
    # Iterate through the KML document to extract data
    for document in k.features():
        if isinstance(document, kml.Document):
            for folder in document.features():
                if isinstance(folder, kml.Folder):
                    extract_placemarks(folder)

# Function to extract placemark data from a folder
def extract_placemarks(folder):
    for feature in folder.features():
        if isinstance(feature, kml.Placemark):
            extract_feature_data(feature)
        elif isinstance(feature, kml.Folder):
            extract_placemarks(feature)

# Function to extract feature data from KML
def extract_feature_data(feature):
    if isinstance(feature, kml.Placemark):
        print(f"Name: {feature.name}")
        geometry = feature.geometry
        if geometry:
            if geometry.geom_type == 'Point':
                print("Point Coordinates:", list(geometry.coords))
            elif geometry.geom_type == 'LineString':
                print("LineString Coordinates:", list(geometry.coords))

# Main function
def main(file_path):
    kml_content = read_kml(file_path)
    if kml_content:
        parse_kml(kml_content)
    else:
        print("No KML content found in the file.")

# Example usage
file_path = 'Sandbox/data/Signal Map Simple.kml'  # Specify your KML file path
main(file_path)
