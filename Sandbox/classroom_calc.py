# Import necessary libraries
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def read_csv(file_path):
    # Function to read CSV file and return a Pandas DataFrame
    df = pd.read_csv(file_path)
    return df

def analyze_outliers(data_frame):
    # Function to analyze and report outliers in the dataset
    # (You can modify this function based on your specific outlier detection logic)
    z_scores_height = (data_frame['Height'] - data_frame['Height'].mean()) / data_frame['Height'].std()
    z_scores_shoe_size = (data_frame['Shoe_Size'] - data_frame['Shoe_Size'].mean()) / data_frame['Shoe_Size'].std()

    height_outliers = data_frame[abs(z_scores_height) > 3]
    shoe_size_outliers = data_frame[abs(z_scores_shoe_size) > 3]

    outliers_report = f"Height outliers:\n{height_outliers}\n\nShoe Size outliers:\n{shoe_size_outliers}"
    return outliers_report

def plot_data(data_frame):
    # Function to plot the data using matplotlib
    plt.figure(figsize=(10, 6))
    plt.scatter(data_frame['Height'], data_frame['Shoe_Size'], color='blue', label='Data Points')
    plt.title('Height vs Shoe Size')
    plt.xlabel('Height')
    plt.ylabel('Shoe Size')
    plt.legend()
    plt.grid(True)
    plt.show()

def linear_regression(data_frame):
    # Function to perform linear regression to predict shoe size based on height
    X_train, X_test, y_train, y_test = train_test_split(data_frame[['Height']], data_frame['Shoe_Size'], test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    equation = f"Shoe_Size = {model.coef_[0]:.2f} * Height + {model.intercept_:.2f}"
    print(f"Linear Regression Equation: {equation}")

    mse = mean_squared_error(y_test, predictions)
    print(f"Mean Squared Error: {mse}")

def main():
    # Prompt the user to enter the file path to the data
    file_path = input("Enter the file path to your data here: ")

    # Read the CSV file
    df = read_csv(file_path)

    # Analyze and report outliers
    outliers_report = analyze_outliers(df)
    print(outliers_report)

    # Plot the data
    plot_data(df)

    # Perform linear regression
    linear_regression(df)

if __name__ == "__main__":
    main()
