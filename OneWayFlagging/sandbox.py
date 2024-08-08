import pandas as pd
import numpy as np

# Example DataFrame
data = {
    'Direction': ['EB', 'WB', 'EB', 'WB', 'EB', 'WB'],
    'VehicleType': ['Car', 'Car', 'Bus', 'Bus', 'Car', 'Bus'],
    'Headway': [10, 12, 15, 20, 18, 22]  # Example headway values
}

df = pd.DataFrame(data)

# Aggregate functions
agg_functions = {
    'Average': np.mean,
    '85th Percentile': lambda x: np.percentile(x, 85),
    'Max': np.max
}

# Group by Direction and VehicleType, apply aggregation functions
summary_table = df.groupby(['Direction', 'VehicleType'])['Headway'].agg(**agg_functions).reset_index()

# Display the summary table
print(summary_table)
