import pandas as pd

df = pd.read_csv("data/leads_clean.csv")
sample = df.sample(120, random_state=7).reset_index(drop=True)

def label(row):
    score = 0
    if row["engagement_score"] >= 55:
        score += 2
    elif row["engagement_score"] >= 30:
        score += 1

    if not row["is_stale"]:
        score += 2

    if row["deal_stage"] in ("Qualified", "Contacted"):
        score += 1

    if row["past_deal_value"] and row["past_deal_value"] >= 100000:
        score += 1

    if isinstance(row["notes"], str) and "do not contact" in row["notes"].lower():
        score -= 3

    return "good" if score >= 3 else "not_good"

sample["human_label"] = sample.apply(label, axis=1)
sample.to_csv("eval/labeled_eval_set.csv", index=False)
print(f"Wrote {len(sample)} labeled leads")
print(sample["human_label"].value_counts())
