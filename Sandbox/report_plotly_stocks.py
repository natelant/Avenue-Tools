import pandas as pd
import plotly.express as px

# Create a simple dataset
data = {
    'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    'Sales': [1000, 1200, 900, 1500, 1800]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Perform a simple analysis
total_sales = df['Sales'].sum()
average_sales = df['Sales'].mean()

# Create an interactive plot
fig = px.bar(df, x='Month', y='Sales', title='Monthly Sales')

# Generate HTML components
# Generate HTML for the table with a title
table_html = f"""
<div class="table-container">
    <h3>Monthly Sales Data</h3>
    {df.to_html(index=False, classes='data-table')}
</div>
"""
plot_html = fig.to_html(full_html=False)

# Create a description of the bar chart
chart_description = """
<p>The bar chart above illustrates the monthly sales data for the first five months of the year. 
Each bar represents the total sales for a specific month, with the height of the bar corresponding 
to the sales amount. The x-axis shows the months from January to May, while the y-axis represents 
the sales figures in dollars. This visualization allows for quick comparison of sales performance 
across different months, making it easy to identify trends or anomalies in the data.</p>
<p>Interactivity: You can hover over each bar to see the exact sales figure for that month. 
The chart also allows zooming and panning for a closer look at specific data points.</p>
"""

# Create the full HTML report
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0 auto; max-width: 800px; padding: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
        .chart-description {{ background-color: #e6f3ff; padding: 10px; border-radius: 5px; margin-top: 20px; }}
        .table-container {{ margin-top: 20px; }}
        .data-table {{ width: 100%; border-collapse: collapse; }}
        .data-table th {{ background-color: #f2f2f2; }}
        .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    </style>
</head>
<body>
    <h1>Sales Analysis Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Sales: ${total_sales}</p>
        <p>Average Monthly Sales: ${average_sales:.2f}</p>
    </div>
    <h2>Monthly Sales Data</h2>
    {table_html}
    <h2>Sales Chart</h2>
    {plot_html}
    <div class="chart-description">
        <h3>Chart Description</h3>
        {chart_description}
    </div>
</body>
</html>
"""

# Save the HTML report
with open('sales_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Report generated: sales_report.html")

