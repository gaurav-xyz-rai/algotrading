import pandas as pd

def ensure_bo_suffix(csv_path, output_path=None):
    df = pd.read_csv(csv_path)

    if 'ticker' not in df.columns:
        raise ValueError("CSV must contain a 'ticker' column")

    # Ensure all tickers end with '.BO'
    df['ticker'] = df['ticker'].astype(str).apply(lambda x: x if x.endswith('.BO') else f"{x}.BO")

    # Save to a new file if output_path is provided
    if output_path:
        df.to_csv(output_path, index=False)
        print(f"Updated tickers saved to {output_path}")
    else:
        print(df)

# Example usage
ensure_bo_suffix('./test/file1.csv', './test/file3.csv')
