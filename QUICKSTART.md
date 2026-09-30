# Quickstart

Get the Lead Triage Copilot running in ~10 minutes.

## Prerequisites

- Python 3.10 (3.11 works; 3.12 may break `sentence-transformers`)
- Windows, macOS, or Linux
- Two free API keys (no credit card):
  - Gemini: https://aistudio.google.com/app/apikey
  - Groq:   https://console.groq.com/keys

## Steps

### 1. Clone and install

    git clone https://github.com/Harshal242005/lead-triage-copilot.git
    cd lead-triage-copilot

    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate

    pip install -r requirements.txt

### 2. Add your API keys

    cp .env.example .env     # Windows: copy .env.example .env

Open `.env` and paste your keys:

    GEMINI_API_KEY=AIza...
    GROQ_API_KEY=gsk_...

### 3. Run the pipeline

    python data/generate_synthetic_leads.py    # ~2 sec  -> 864 leads
    python pipeline/clean.py                   # ~1 sec  -> 781 leads
    python pipeline/embed_and_index.py         # ~30 sec (first run downloads the embedding model, ~90MB)
    python pipeline/score_leads.py --sample-n 10   # ~40 sec -> 10 leads scored
    python pipeline/draft_outreach.py              # ~30 sec -> drafts top 20

### 4. Launch the UI

    streamlit run app.py

Open http://localhost:8501 in a browser.

You should see a list of leads with scores, reasoning, and drafts. Click
Approve on any lead — the status persists to `data/leads_top.csv`.

### 5. (Optional) Reproduce the eval

    python eval/build_eval_set.py      # builds 120-lead labeled set
    python eval/score_eval_set.py      # scores them (~6 min)
    python eval/run_eval.py            # prints precision@k

Expected output:

    precision@10     1.0
    precision@20     1.0
    precision@30     1.0
    precision@50     1.0
    random baseline  0.55
    n_leads          120

## What success looks like

After step 4, the Streamlit UI shows a lead card like:

    #1 - Borde, Balasubramanian and Bedi  |  score 45  |  pending
    Industry: Logistics  |  Size: 200-500
    Engagement: 24  |  Stale: False
    Why the model ranked it here:
      "Although the lead matches the industry and size of past won deals
       (W014, W013) which had high engagement, its current engagement is
       low (40), and budget is tight, with 123 days since last contact."
    Cited fields: industry, company_size, engagement_score, notes, days_since_contact
    Similar past wins: W014, W013

## Troubleshooting

- **`API_KEY_INVALID`** — check `.env` has no quotes around the key value
- **`429` / rate limit** — free tier quota exhausted; wait an hour or reduce `--sample-n`
- **`sentence-transformers` install fails** — you are probably on Python 3.12; use 3.10 or 3.11
- **Model not found (e.g. `gemini-2.5-flash`)** — Google retires models frequently; check `pipeline/score_leads.py` `MODEL_FALLBACKS` for the current working list

## Cost

Zero. Every LLM call uses a free-tier key. Embeddings and vector search run
locally and make no network calls.
