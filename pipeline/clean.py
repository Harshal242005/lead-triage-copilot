import pandas as pd
from datetime import datetime

STALE_DAYS = 180


def load_and_clean(path="data/leads.csv"):
    df = pd.read_csv(path)
    raw_count = len(df)

    # 1. Dedupe by normalized company name
    df["company_key"] = (
        df["company_name"]
        .str.lower()
        .str.replace(r"\b(pvt|private|ltd|limited|inc|llc)\b", "", regex=True)
        .str.replace(r"[^a-z0-9 ]", "", regex=True)
        .str.strip()
    )
    df = df.sort_values("engagement_score", ascending=False)
    df = df.drop_duplicates(subset="company_key", keep="first")
    dedup_count = len(df)

    # 2. Fill blanks
    df["last_contacted"] = df["last_contacted"].fillna("")
    df["notes"] = df["notes"].fillna("")
    df["past_deal_value"] = pd.to_numeric(df["past_deal_value"], errors="coerce").fillna(0)

    # 3. Add staleness flag
    today = datetime.today()

    def days_since(s):
        if not s:
            return None
        try:
            return (today - datetime.strptime(s, "%Y-%m-%d")).days
        except (ValueError, TypeError):
            return None

    df["days_since_contact"] = df["last_contacted"].apply(days_since)
    df["is_stale"] = df["days_since_contact"].apply(lambda d: d is None or d > STALE_DAYS)

    df = df.drop(columns=["company_key"])
    df.to_csv("data/leads_clean.csv", index=False)

    print(f"Raw: {raw_count} | After dedupe: {dedup_count} | Removed: {raw_count - dedup_count}")
    print(f"Stale leads: {df['is_stale'].sum()}")
    return df


if __name__ == "__main__":
    load_and_clean()