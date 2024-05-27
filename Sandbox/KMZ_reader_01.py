import zipfile
import os
from fastkml import kml
from lxml import etree

def read_kmz(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as kmz:
        # Find the KML file within the KMZ archive
        for name in kmz.namelist():
            if name.endswith('.kml'):
                with kmz.open(name) as kml_file:
                    kml_content = kml_file.read()
                    return kml_content
    return None

# Function to read KML content from a KML file
def read_kml(kml_path):
    with open(kml_path, 'rb') as file:
        kml_content = file.read()
    return kml_content

# Function to pretty print KML content
def pretty_print_kml(kml_content):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.XML(kml_content, parser)
    return etree.tostring(tree, pretty_print=True, encoding='unicode')

# Function to parse KML content and extract data
def parse_kml(kml_content):
    k = kml.KML()
    k.from_string(kml_content)

    # Iterate through the KML document to extract data
    for document in k.features():
        for feature in document.features():
            extract_feature_data(feature)

# Function to extract feature data from KML
def extract_feature_data(feature):
    if isinstance(feature, kml.Placemark):
        print(f"Name: {feature.name}")
        geometry = feature.geometry
        if geometry:
            if isinstance(geometry, kml.Point):
                print("Point Coordinates:", list(geometry.coords))
            elif isinstance(geometry, kml.LineString):
                print("LineString Coordinates:", list(geometry.coords))

# Main function to handle different file types (KMZ/KML)
def main(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    kml_content = None
    
    if file_extension == '.kmz':
        kml_content = read_kmz(file_path)
    elif file_extension == '.kml':
        kml_content = read_kml(file_path)
    else:
        print("Unsupported file format. Please provide a KML or KMZ file.")
        return
    
    if kml_content:
        parse_kml(kml_content)
    else:
        print("No KML content found in the file.")

# Example usage
file_path = 'Sandbox/data/Signal Map Simple.kml'  # or 'your_file.kml'
main(file_path)
