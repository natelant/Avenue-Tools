import pandas as pd
import plotly.express as px
from jinja2 import Environment, FileSystemLoader
import plotly.io as pio

# Sample DataFrame
data = {
    'Category': ['A', 'B', 'C', 'D'],
    'Values': [23, 45, 56, 78]
}
df = pd.DataFrame(data)

# Create a plot using Plotly
fig = px.bar(df, x='Category', y='Values', title='Sample Bar Chart')
plot_html = pio.to_html(fig, full_html=False)

# Load Jinja2 template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('report_html_template.html')

# Render the template with dynamic content
html_out = template.render(title="Pandas Analysis Report", plot=plot_html)

# Save the rendered HTML to a file with UTF-8 encoding
with open("report_from_jinja2.html", "w", encoding='utf-8') as f:
    f.write(html_out)

print("HTML report generated successfully!")
