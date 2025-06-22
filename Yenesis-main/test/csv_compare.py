import pandas as pd

# Load both CSV files
df1 = pd.read_csv("file1.csv")
df2 = pd.read_csv("file2.csv")

# Ensure the column exists in both files
if "ticker" not in df1.columns or "ticker" not in df2.columns:
    raise ValueError("Both CSVs must contain a 'ticker' column.")

# Find common values in the 'ticker' column
common_values = pd.merge(df1[['ticker']], df2[['ticker']], on='ticker')

# Save or print the results
common_values.to_csv("common_tickers.csv", index=False)
print("Common tickers:")
print(common_values)
