import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

# The ORIGINAL (buggy) v1 prompt - no strict rules
V1_PROMPT = """Draft a short, specific first-touch outreach email for this B2B lead.

Lead:
{lead_json}

Why we think they're a fit (our scoring reasoning):
{reasoning}

Rules:
- Max 90 words
- Reference one specific detail from the lead's data
- No fake claims, no invented case studies
- End with a soft ask (15-min call)
- Output only the email body, no subject line
"""

def draft_one(lead, reasoning):
    prompt = V1_PROMPT.format(
        lead_json=json.dumps(lead, default=str),
        reasoning=reasoning,
    )
    resp = CLIENT.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.4),
    )
    return resp.text.strip()

df = pd.read_csv("data/leads_scored.csv").head(10)
drafts = []
for i, row in df.iterrows():
    try:
        drafts.append(draft_one(row.to_dict(), row["reasoning"]))
    except Exception as e:
        drafts.append(f"ERROR: {e}")
    if i % 5 == 0:
        print(f"Drafted {i}/{len(df)}")
    time.sleep(2.0)

df["draft_message"] = drafts
df["status"] = "pending"
df.to_csv("data/leads_top_v1_with_hallucination.csv", index=False)
print(f"Wrote data/leads_top_v1_with_hallucination.csv ({len(df)} rows)")
print()
print("=== Draft 2 (the one we'll show on video) ===")
print(df.iloc[1]["draft_message"])
