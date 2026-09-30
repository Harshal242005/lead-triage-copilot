import pandas as pd

# Use the SAME 120 leads that the eval set uses
df = pd.read_csv("eval/labeled_eval_set.csv")
small = df[["lead_id", "company_name", "industry", "company_size",
            "engagement_score", "last_contacted", "deal_stage", "notes"]].copy()
small.to_csv("eval/baseline_leads.csv", index=False)
print(f"Wrote {len(small)} leads to eval/baseline_leads.csv")
print("These are the SAME 120 leads the eval used — your picks will now be comparable.")
