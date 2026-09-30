import os
import json
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from groq import Groq

CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

PROMPT = """Draft a short, specific first-touch outreach email for this B2B lead.

Lead:
{lead_json}

Why we think they're a fit (our scoring reasoning):
{reasoning}

STRICT RULES — violating any of these makes the draft unusable:
- Max 90 words
- NEVER invent facts. Only reference values that appear in the Lead data above.
- Do NOT claim we have worked with this company, or delivered any project for them.
- The field past_deal_value is how much THIS lead spent in the past (often 0); it is NOT a case study we can cite.
- Do NOT use placeholders like [Your Company], [Your Name], {{first_name}}.
  Sign off as "Best, The Team".
- Reference exactly one specific detail from the lead's own data (industry, engagement score, or a phrase from notes).
- End with a soft ask for a 15-minute call.
- Output only the email body, no subject line, no markdown.
"""

def draft_one(lead, reasoning):
    prompt = PROMPT.format(
        lead_json=json.dumps(lead, default=str),
        reasoning=reasoning,
    )
    resp = CLIENT.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


def main(top_n=20):
    df = pd.read_csv("data/leads_scored.csv").head(top_n)
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
    df.to_csv("data/leads_top.csv", index=False)
    print(f"Wrote data/leads_top.csv with {len(df)} drafted messages")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-n", type=int, default=20,
                        help="How many top-scored leads to draft for (default: 20)")
    args = parser.parse_args()
    main(top_n=args.top_n)