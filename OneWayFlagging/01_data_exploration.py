import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
df = pd.read_csv('total_regression_table.csv')

# Convert 'Start' and 'Stop' columns to datetime
df['Start'] = pd.to_datetime(df['Start'])
df['Stop'] = pd.to_datetime(df['Stop'])

# Create the target variable (capacity)
df['capacity'] = df['green_time'] / df['avg_headway']

# Select features for the model
numeric_features = ['green_time', 'volume', 'Volume_Per_Hour', 'truck_percentage', 'avg_speed_segment', 'avg_grade_weighted', 'total_distance_segment']
categorical_features = ['route_name', 'Direction']

# Select only numeric columns
numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns

# Create a correlation matrix for numeric columns only
correlation_matrix = df[numeric_columns].corr()

# Plot the correlation heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.title('Correlation Heatmap')
plt.show()

# Pairplot for key variables
sns.pairplot(df[[
    'green_time', 
    'avg_headway', 
    'volume', 
    'truck_percentage', 
    'capacity', 
    'previous_red_time', 
    'previous_split_time', 
    'previous_red_clearance'
]])
plt.show()