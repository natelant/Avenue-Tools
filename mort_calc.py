def mortgage_calculator(loan_amount, annual_interest_rate, loan_term_years):
    # Convert annual interest rate to monthly rate
    monthly_interest_rate = annual_interest_rate / 100 / 12

    # Convert loan term from years to months
    loan_term_months = loan_term_years * 12

    # Calculate monthly mortgage payment using the formula
    # M = P[r(1+r)^n]/[(1+r)^n-1]
    # where M is the monthly mortgage payment, P is the loan amount,
    # r is the monthly interest rate, and n is the total number of payments
    mortgage_payment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months) / \
                        ((1 + monthly_interest_rate) ** loan_term_months - 1)

    return mortgage_payment

# Get user input
loan_amount = float(input("Enter the loan amount: $"))
annual_interest_rate = float(input("Enter the annual interest rate (%): "))
loan_term_years = int(input("Enter the loan term in years: "))

# Calculate and display the monthly mortgage payment
monthly_payment = mortgage_calculator(loan_amount, annual_interest_rate, loan_term_years)
print(f"\nYour monthly mortgage payment is: ${monthly_payment:.2f}")
