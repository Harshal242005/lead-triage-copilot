import sys
import os
sys.path.insert(0, os.path.abspath("."))

import pandas as pd
from pipeline.score_leads import (
    retrieve_similar, score_one,
    MODEL_NAME, COLLECTION_NAME,
)
from sentence_transformers import SentenceTransformer
import chromadb
import json
import time


OUT = "eval/eval_scored.csv"


def run():
    df = pd.read_csv("eval/labeled_eval_set.csv")
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path="data/chroma")
    collection = client.get_collection(COLLECTION_NAME)

    done_ids = set()
    existing_rows = []
    if os.path.exists(OUT):
        prev = pd.read_csv(OUT)
        prev["model_score"] = pd.to_numeric(prev["model_score"], errors="coerce")
        prev_ok = prev[prev["model_score"].notna()]
        done_ids = set(prev_ok["lead_id"].tolist())
        existing_rows = prev_ok.to_dict("records")
        print(f"Resuming: {len(done_ids)} leads already scored")

    rows = list(existing_rows)
    todo = df[~df["lead_id"].isin(done_ids)]
    print(f"Leads remaining: {len(todo)}")

    trace_f = open("eval/eval_traces.jsonl", "a", encoding="utf-8")

    for i, row in todo.iterrows():
        lead = row.to_dict()
        try:
            ctx_ids, ctx_docs = retrieve_similar(collection, model, lead)
            parsed, prompt, raw, model_used = score_one(lead, ctx_ids, ctx_docs)
            lead["model_score"] = parsed["score"]
            lead["model_reasoning"] = parsed["reasoning"]
            lead["model_used"] = model_used
        except Exception as e:
            print(f"  lead {lead['lead_id']} failed: {e}")
            continue

        trace_f.write(json.dumps({
            "ts": time.time(),
            "lead_id": lead["lead_id"],
            "input": {k: str(v) for k, v in lead.items()},
        }) + "\n")

        rows.append(lead)
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(f"Scored {lead['lead_id']} | total: {len(rows)}/{len(df)}")
        time.sleep(2.0)

    trace_f.close()
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Done. {len(rows)} rows in {OUT}")


if __name__ == "__main__":
    run()
