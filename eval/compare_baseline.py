import pandas as pd

df = pd.read_csv("eval/baseline_leads.csv")

# find the pick column
pick_col = None
for c in df.columns:
    if df[c].astype(str).str.lower().str.contains("pick").any():
        pick_col = c
        break

if pick_col is None:
    print("No 'pick' column found. Did you save the CSV with your picks?")
    raise SystemExit(1)

picks = df[df[pick_col].astype(str).str.lower() == "pick"]
print(f"Your picks: {len(picks)}")

# load ground truth from the labeled eval set
truth = pd.read_csv("eval/labeled_eval_set.csv")[["lead_id", "human_label"]]
merged = df.merge(truth, on="lead_id", how="left")

picked_ids = set(picks["lead_id"])
merged["picked"] = merged["lead_id"].isin(picked_ids)

top_picks = merged[merged["picked"]]
hit = (top_picks["human_label"] == "good").sum()
total = len(top_picks)
if total:
    print(f"Human precision@{total}: {hit/total:.3f}  ({hit}/{total} match ground truth)")
else:
    print("No picks detected.")
