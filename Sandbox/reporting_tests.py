import folium
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
import io
from PIL import Image as PILImage
import imgkit

# Create a sample graph using matplotlib
def create_graph():
    plt.figure()
    x = [1, 2, 3, 4, 5]
    y = [2, 3, 5, 7, 11]
    plt.plot(x, y, marker='o')
    plt.title('Sample Graph')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.grid(True)
    plt.savefig('sample_graph.png')
    plt.close()

# Create a map with a marker at a defined location
def create_map():
    location = [37.7749, -122.4194]  # San Francisco, CA
    map_ = folium.Map(location=location, zoom_start=13)
    folium.Marker(location, popup="San Francisco").add_to(map_)
    map_.save('map.html')

    # Convert the map to an image
    
    imgkit.from_file('map.html', 'map.png')

# Create a PDF report with title, headings, graphs, and footnotes
def generate_report():
    create_graph()
    create_map()

    # Set up the PDF
    pdf_filename = 'report.pdf'
    document = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom style for code
    code_style = ParagraphStyle(name='Code', fontName='Courier', fontSize=10, leading=12)

    flowables = []

    # Title
    title = Paragraph('Sample Report Title', styles['Title'])
    flowables.append(title)
    flowables.append(Spacer(1, 0.5 * inch))

    # Introduction Section
    introduction = Paragraph('This report provides an overview of the sample data and visualizations.', styles['Normal'])
    flowables.append(introduction)
    flowables.append(Spacer(1, 0.5 * inch))

    # Heading
    heading = Paragraph('Section Heading', styles['Heading1'])
    flowables.append(heading)
    flowables.append(Spacer(1, 0.5 * inch))

    # Sample Code
    code = """
def hello_world():
    print("Hello, world!")

hello_world()
"""
    code_paragraph = Paragraph(f'<pre>{code}</pre>', code_style)
    flowables.append(code_paragraph)
    flowables.append(Spacer(1, 0.5 * inch))

    # Description of the Graph
    graph_description = Paragraph('The following graph shows a sample plot of data points.', styles['Normal'])
    flowables.append(graph_description)
    flowables.append(Spacer(1, 0.5 * inch))

    # Graph
    graph_image = Image('sample_graph.png', width=4 * inch, height=3 * inch)
    flowables.append(graph_image)
    flowables.append(Spacer(1, 0.5 * inch))

    # Map
    map_heading = Paragraph('Map Section', styles['Heading1'])
    map_description = Paragraph('The following map shows a marker at a defined location (San Francisco).', styles['Normal'])
    map_image = Image('map.png', width=4 * inch, height=3 * inch)
    flowables.append(map_heading)
    flowables.append(Spacer(1, 0.25 * inch))
    flowables.append(map_description)
    flowables.append(Spacer(1, 0.25 * inch))
    flowables.append(map_image)
    flowables.append(Spacer(1, 0.5 * inch))

    # Additional Section
    additional_section_heading = Paragraph('Additional Section', styles['Heading1'])
    additional_section_content = Paragraph('This is an additional section to provide more information.', styles['Normal'])
    flowables.append(additional_section_heading)
    flowables.append(Spacer(1, 0.25 * inch))
    flowables.append(additional_section_content)
    flowables.append(Spacer(1, 0.5 * inch))

    # Footnotes
    footnotes = Paragraph('Footnotes: <br/>1. This is a sample footnote.', styles['Normal'])
    flowables.append(footnotes)

    # Build the PDF
    document.build(flowables)

if __name__ == "__main__":
    generate_report()
