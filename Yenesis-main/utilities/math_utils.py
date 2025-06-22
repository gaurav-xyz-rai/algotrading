import numpy as np

# Compute z-score: how far latest value is from historical mean in std deviations
def calculate_z_score(latest_val, series, min_history=30):
    if len(series.dropna()) < min_history:
        return None
    std = series.std()
    if std == 0:
        return None
    mean = series.mean()
    return (latest_val - mean) / std

# Scale z-score into a 0-100 range using sigmoid transformation
def scale_score(z):
    if z is None:
        return 0
    return round(100 / (1 + np.exp(-z)), 2)

# Compute Rate of Change (ROC) over a given window
def calculate_roc(df, window):
    return df['Close'].pct_change(periods=window)