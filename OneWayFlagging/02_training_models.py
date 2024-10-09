from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler

# Prepare the data
X = df[['green_time', 'volume', 'truck_percentage', 'avg_speed_segment', 'avg_grade_weighted', 'total_distance_segment']]
y = df['green_time'] / df['avg_headway']  # Capacity

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train models
models = {
    'Linear Regression': LinearRegression(),
    'Ridge': Ridge(alpha=1.0),
    'Lasso': Lasso(alpha=1.0),
    'ElasticNet': ElasticNet(alpha=1.0, l1_ratio=0.5)
}

for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    print(f"{name} trained.")