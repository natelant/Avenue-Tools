def calculate_fuel_cost(cost_per_gallon_usd, exchange_rate):
    # Convert cost from dollars per gallon to euros per liter
    cost_per_liter_euros = (cost_per_gallon_usd / 3.78541) * exchange_rate
    return cost_per_liter_euros


def main():
    try:
        # Get user input
        cost_per_gallon_usd = float(input("Enter the cost per gallon in USD: "))
        exchange_rate = float(input("Enter the exchange rate (1 USD to Euros): "))

        # Validate inputs
        if cost_per_gallon_usd <= 0 or exchange_rate <= 0:
            raise ValueError("Please enter positive values for cost and exchange rate.")

        # Calculate fuel cost
        cost_per_liter_euros = calculate_fuel_cost(cost_per_gallon_usd, exchange_rate)

        # Display the result
        print(f"Cost per Liter (Euros): {cost_per_liter_euros:.2f}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
