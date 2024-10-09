from sklearn.metrics import mean_squared_error, r2_score

for name, model in models.items():
    y_pred = model.predict(X_test_scaled)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"{name}:")
    print(f"  Mean Squared Error: {mse}")
    print(f"  R-squared Score: {r2}")
    print()

# Plot actual vs predicted for the best model
best_model = max(models.items(), key=lambda x: r2_score(y_test, x[1].predict(X_test_scaled)))
y_pred_best = best_model[1].predict(X_test_scaled)

plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred_best)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual Capacity')
plt.ylabel('Predicted Capacity')
plt.title(f'Actual vs Predicted Capacity ({best_model[0]})')
plt.show()