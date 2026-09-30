import pandas as pd
import random

df = pd.read_csv("eval/eval_scored.csv")

df = df.dropna(subset=["model_score"]).reset_index(drop=True)
df["model_score"] = df["model_score"].astype(int)

def precision_at_k(df, k):
    top = df.sort_values("model_score", ascending=False).head(k)
    return round((top["human_label"] == "good").mean(), 3)

results = {}
for k in [10, 20, 30, 50]:
    if k <= len(df):
        results[f"precision@{k}"] = precision_at_k(df, k)

random.seed(7)
random_top20 = df.sample(20)
results["precision@20_random_baseline"] = round((random_top20["human_label"] == "good").mean(), 3)

results["min_score"] = int(df["model_score"].min())
results["max_score"] = int(df["model_score"].max())
results["mean_score"] = round(df["model_score"].mean(), 1)
results["std_score"] = round(df["model_score"].std(), 1)
results["n_leads"] = len(df)

print("=" * 50)
print("EVAL RESULTS")
print("=" * 50)
for k, v in results.items():
    print(f"{k:35s} {v}")

pd.Series(results).to_csv("eval/results_summary.csv", header=["value"])
print("\nSaved to eval/results_summary.csv")
