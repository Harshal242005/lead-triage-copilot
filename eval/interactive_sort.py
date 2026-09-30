import pandas as pd
import time

df = pd.read_csv("eval/baseline_human.csv")

print()
print("=" * 60)
print("MANUAL LEAD SORT - type p to pick, s to skip, q to quit")
print("Goal: pick exactly 20 leads you would want a salesperson to call")
print("=" * 60)

picks = []
start = time.time()
for i, row in df.iterrows():
    print()
    print(f"[{i+1}/120]  {row['company_name']}")
    print(f"   Industry: {row['industry']}  |  Size: {row['company_size']}")
    print(f"   Engagement: {row['engagement_score']}  |  Last contacted: {row['last_contacted']}")
    print(f"   Stage: {row['deal_stage']}  |  Notes: {row['notes']}")
    ans = input("   p / s / q > ").strip().lower()
    if ans == "q":
        break
    if ans == "p":
        picks.append(row["lead_id"])
        print(f"   --> PICKED ({len(picks)}/20)")
    if len(picks) == 20:
        print()
        print("Reached 20 picks. Stopping.")
        break

elapsed = time.time() - start
df["pick"] = df["lead_id"].apply(lambda x: "pick" if x in picks else "")
df.to_csv("eval/baseline_human.csv", index=False)

print()
print("=" * 60)
print(f"Time:  {elapsed/60:.1f} minutes  ({elapsed:.0f} seconds)")
print(f"Picks: {len(picks)}")
print("Saved to eval/baseline_human.csv")
print("=" * 60)
