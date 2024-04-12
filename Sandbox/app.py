from dash import Dash, html
import pandas as pd

# incorporate data
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')

app = Dash(__name__)

app.layout = html.Div([
    html.Div(children='Hello World')
    dash_table.DataTable(data=df.to_dict('records'), page_size=10)
])

#run the app
if __name__ == '__main__':
    app.run(debug=True)
