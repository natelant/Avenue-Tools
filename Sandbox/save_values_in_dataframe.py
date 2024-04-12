import pandas as pd

# Sample DataFrame
data = {
    'before_after': ['Redwood NB.csv', 'Redwood SB.csv'],
    'source_file': ['before', 'after'],
    'before': [7.549797, 6.556579],
    'after': [6.569061, 5.948889],
    'Difference (sec)': [-58.844164, -36.461427]
}

df = pd.DataFrame(data)

# Extract values from DataFrame and assign them to variables
before_after_1 = df.loc[0, 'before_after']
source_file_1 = df.loc[0, 'source_file']
before_1 = df.loc[0, 'before']
after_1 = df.loc[0, 'after']
difference_1 = df.loc[0, 'Difference (sec)']

before_after_2 = df.loc[1, 'before_after']
source_file_2 = df.loc[1, 'source_file']
before_2 = df.loc[1, 'before']
after_2 = df.loc[1, 'after']
difference_2 = df.loc[1, 'Difference (sec)']

# Print the values of the variables
print("Values for row 1:")
print("before_after:", before_after_1)
print("source_file:", source_file_1)
print("before:", before_1)
print("after:", after_1)
print("Difference:", difference_1)
print()
print("Values for row 2:")
print("before_after:", before_after_2)
print("source_file:", source_file_2)
print("before:", before_2)
print("after:", after_2)
print("Difference:", difference_2)
