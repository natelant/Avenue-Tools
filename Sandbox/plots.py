import matplotlib.pyplot as plt
import pandas as pd

# Sample data
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'gender': ['Female', 'Male', 'Male', 'Male', 'Female'],
    'height': [165, 180, 175, 170, 160],
    'shoe_size': [7, 10, 9, 8, 6]
}

# Create a DataFrame
df = pd.DataFrame(data)
print(df)

# Plotting
fig, ax = plt.subplots()

# Bar chart for height
ax.bar(df['name'], df['height'], label='Height')

# Bar chart for shoe size
ax.bar(df['name'], df['shoe_size'], label='Shoe Size', alpha=0.5)

# Adding labels and title
ax.set_xlabel('Name')
ax.set_ylabel('Height and Shoe Size')
ax.set_title('Height and Shoe Size Comparison')

# Display the legend
ax.legend()

# Show the plot
plt.show()
