import os
import json
import time
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from groq import Groq

GEMINI_CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))

# (provider, model_name) tuples - tried in order
MODEL_FALLBACKS = [
    ("gemini", "gemini-3.5-flash-lite"),
    ("gemini", "gemini-3.1-flash-lite"),
    ("groq",   "openai/gpt-oss-120b"),
    ("groq",   "openai/gpt-oss-20b"),
]

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "won_deals"
TOP_K = 3
TRACE_PATH = "logs/traces.jsonl"


def retrieve_similar(collection, model, lead, k=TOP_K):
    query = (
        f"Industry: {lead['industry']}. Company size: {lead['company_size']}. "
        f"Engagement: {lead['engagement_score']}. Notes: {lead['notes']}"
    )
    emb = model.encode([query]).tolist()
    results = collection.query(query_embeddings=emb, n_results=k)
    return results["ids"][0], results["documents"][0]


PROMPT = """You are scoring a B2B sales lead for likelihood to convert.

Lead data:
{lead_json}

Similar past won deals (retrieved from our CRM history):
{context}

Return ONLY valid JSON with this exact shape:
{{
  "score": <integer 0-100>,
  "reasoning": "<one or two sentences citing specific field values>",
  "cited_fields": ["<field1>", "<field2>", ...],
  "similar_deal_ids": ["<id1>", "<id2>"]
}}
"""


def score_one(lead, context_ids, context_docs, max_retries=3):
    context = "\n".join(
        f"- {did}: {doc}" for did, doc in zip(context_ids, context_docs)
    )
    prompt = PROMPT.format(
        lead_json=json.dumps(lead, default=str),
        context=context,
    )

    last_err = None
    for provider, model_name in MODEL_FALLBACKS:
        for attempt in range(max_retries):
            try:
                if provider == "gemini":
                    resp = GEMINI_CLIENT.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )
                    raw = resp.text.strip()
                else:
                    resp = GROQ_CLIENT.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        response_format={"type": "json_object"},
                    )
                    raw = resp.choices[0].message.content.strip()

                parsed = json.loads(raw)
                return parsed, prompt, raw, f"{provider}:{model_name}"
            except Exception as e:
                last_err = e
                msg = str(e)
                if any(k in msg for k in ["503", "429", "UNAVAILABLE", "rate", "overload", "quota"]):
                    wait = 5 * (attempt + 1)
                    print(f"  [{provider}:{model_name}] transient error, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    break
    raise RuntimeError(f"All providers failed. Last error: {last_err}")


def main(sample_n=None):
    df = pd.read_csv("data/leads_clean.csv")
    if sample_n:
        df = df.sample(sample_n, random_state=42).reset_index(drop=True)

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path="data/chroma")
    collection = client.get_collection(COLLECTION_NAME)

    results = []
    trace_f = open(TRACE_PATH, "a", encoding="utf-8")

    for i, row in df.iterrows():
        lead = row.to_dict()
        try:
            ctx_ids, ctx_docs = retrieve_similar(collection, model, lead)
            parsed, prompt, raw, model_used = score_one(lead, ctx_ids, ctx_docs)
            lead["score"] = parsed["score"]
            lead["reasoning"] = parsed["reasoning"]
            lead["cited_fields"] = ",".join(parsed.get("cited_fields", []))
            lead["similar_deal_ids"] = ",".join(parsed.get("similar_deal_ids", []))
            lead["model_used"] = model_used
            status = "ok"
        except Exception as e:
            lead["score"] = None
            lead["reasoning"] = f"ERROR: {e}"
            lead["cited_fields"] = ""
            lead["similar_deal_ids"] = ""
            lead["model_used"] = ""
            status = f"error: {e}"

        trace_f.write(json.dumps({
            "ts": time.time(),
            "lead_id": lead["lead_id"],
            "input": lead,
            "status": status,
        }, default=str) + "\n")

        results.append(lead)
        if i % 10 == 0:
            print(f"Scored {i}/{len(df)}")
        time.sleep(2.0)

    trace_f.close()
    out = pd.DataFrame(results).sort_values("score", ascending=False)
    out.to_csv("data/leads_scored.csv", index=False)
    print(f"Wrote data/leads_scored.csv ({len(out)} rows)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-n", type=int, default=10,
                        help="Score only N leads (default: 10 for testing). Omit to score all.")
    parser.add_argument("--all", action="store_true",
                        help="Score the entire cleaned dataset (may hit LLM rate limits).")
    args = parser.parse_args()
    main(sample_n=None if args.all else args.sample_n)