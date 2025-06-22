import pandas as pd
import numpy as np
# Ensures downloaded DataFrame has single-level columns
def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# Extract scalar value safely from Series
def extract_scalar(val):
    if isinstance(val, pd.Series):
        if len(val) == 1:
            val = val.iloc[0]
        else:
            return None
    if isinstance(val, (np.float64, np.float32, np.float16, np.float_)):
        val = float(val)
    return None if pd.isna(val) else val

