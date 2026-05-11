import pandas as pd


# ============================================================
# DATA LOADING (clean version for inspection)
# ============================================================

def load_data_for_inspection():
    """
    Load BTC data exactly like the app, but without Streamlit caching.
    Only return btc because that's what compute_returns() uses.
    """
    try:
        print("Loading: data/btc_clean.csv ...")
        btc = pd.read_csv('data/btc_clean.csv')

        # normalize columns
        btc.columns = btc.columns.str.lower().str.strip()

        # fix date/timestamp
        if 'date' in btc.columns:
            btc['date'] = pd.to_datetime(btc['date'])
        elif 'timestamp' in btc.columns:
            btc['date'] = pd.to_datetime(btc['timestamp'])

        print("Loaded BTC data successfully.\n")
        return btc

    except Exception as e:
        print(f"[ERROR] Could not load BTC data: {e}")
        return None


# ============================================================
# INSPECTION TOOL
# ============================================================

def inspect_df(df: pd.DataFrame):
    print("\n" + "=" * 70)
    print("                   DATA INSPECTION REPORT")
    print("=" * 70)

    # 1) Basic info
    print("\n[1] BASIC INFO")
    print("Shape:", df.shape)
    print("Is empty:", df.empty)

    # 2) Columns
    print("\n[2] COLUMNS")
    print(df.columns.tolist())

    print("\nColumn dtypes:")
    print(df.dtypes)

    # 3) Head
    print("\n[3] HEAD (first 5 rows)")
    print(df.head())

    # 4) Tail
    print("\n[4] TAIL (last 5 rows)")
    print(df.tail())

    # 5) Nulls
    print("\n[5] NULL VALUES")
    print(df.isna().sum())

    # 6) Duplicates
    print("\n[6] DUPLICATED ROWS")
    print(df.duplicated().sum())

    # 7) Index info
    print("\n[7] INDEX INFO")
    print("Index type:", type(df.index))
    print("Index preview:", df.index[:5])

    # 8) MultiIndex check
    print("\n[8] MULTI-INDEX CHECK")
    print("Columns are MultiIndex:", isinstance(df.columns, pd.MultiIndex))

    # 9) Close column check
    print("\n[9] CLOSE COLUMN CHECK (case-insensitive)")
    cols_lower = [c.lower() for c in df.columns.astype(str)]
    print("Contains 'close':", "close" in cols_lower)

    # 10) Possible candidates
    print("\n[10] POSSIBLE 'CLOSE' CANDIDATES")
    for c in df.columns:
        name = str(c).lower()
        if "close" in name or "price" in name or "adj" in name:
            print("  ->", c)

    print("\nInspection completed.")
    print("=" * 70 + "\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    df = load_data_for_inspection()

    if df is None:
        print("❌ Data could not be loaded. Fix the CSV path or file.")
    else:
        inspect_df(df)
