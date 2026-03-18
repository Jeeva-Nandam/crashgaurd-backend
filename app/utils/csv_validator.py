import pandas as pd

REQUIRED_COLUMNS = ["month", "revenue", "expenses", "customers"]

def validate_csv(df: pd.DataFrame):
    errors = []

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    for col in ["revenue", "expenses", "churn_rate"]:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} must contain numeric values")

    return errors