import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

# Sample DataFrame
data = {
    'Category': ['A', 'B', 'C', 'D'],
    'Values': [23, 45, 56, 78]
}
df = pd.DataFrame(data)

# Creating a plot
plt.figure(figsize=(10, 5))
plt.bar(df['Category'], df['Values'], color='skyblue')
plt.title('Sample Bar Chart')
plt.xlabel('Category')
plt.ylabel('Values')
plt.savefig('bar_chart.png')


# Create instance of FPDF class
pdf = FPDF()

# Add a page
pdf.add_page()

# Set font for the title (bold and larger size)
pdf.set_font("Arial", style='B', size=16)

# Add a title
pdf.cell(200, 10, txt = "Pandas Analysis Report", ln = True, align = 'C')

# Set font for the subtitle (bold and slightly larger size)
pdf.set_font("Arial", style='I', size=14)

# Add a subtitle
pdf.cell(200, 10, txt = "Sample DataFrame Analysis", ln = True, align = 'C')

# Insert a line break
pdf.ln(10)

# Set font for the table content (regular size)
pdf.set_font("Arial", size=10)

# Add DataFrame content as a table
col_width = pdf.w / 4.5
row_height = pdf.font_size * 1.5

for row in df.itertuples():
    pdf.cell(col_width, row_height, txt = str(row.Index), border = 1)
    pdf.cell(col_width, row_height, txt = str(row.Category), border = 1)
    pdf.cell(col_width, row_height, txt = str(row.Values), border = 1)
    pdf.ln(row_height)

# Insert another line break
pdf.ln(10)

# Set font for the chart title (bold and regular size)
pdf.set_font("Arial", style='B', size=12)

# Add a chart title
pdf.cell(200, 10, txt = "Bar Chart", ln = True, align = 'C')

# Add a chart image
pdf.image("bar_chart.png", x = 10, y = None, w = 100)

# Save the PDF with name .pdf
pdf.output("pandas_analysis_report.pdf")
