# Lead Triage Copilot

**Problem Statement:** PS-04 — AI Decision Engine for Business Data

**One-liner:** An AI decision engine that takes a messy B2B CRM export, ranks leads
by likelihood to convert with cited reasoning, drafts first-touch outreach, and
requires a human to approve every action before anything is sent.

---

## What it does

Given a CSV of ~860 messy leads (duplicates, stale contacts, blank fields,
contradictory notes), the system:

1. **Cleans and deduplicates** the records (normalizes company names, flags stale
   contacts, fills blank fields).
2. **Retrieves** the most similar past won deals for each lead using local
   embeddings + a vector store.
3. **Scores** each lead 0-100 with an LLM, producing a plain-English reason that
   cites the exact fields it used.
4. **Drafts** a personalized first-touch outreach message per lead.
5. **Requires human approval** — nothing is ever sent automatically.

Every LLM call is logged to `logs/traces.jsonl` for full traceability.

---

## Architecture

    CSV (synthetic CRM, ~860 rows)
          ↓
    [Cleaning / Dedup]           pipeline/clean.py
          ↓
    [Embeddings]                 sentence-transformers (all-MiniLM-L6-v2, local)
          ↓
    [Vector store]               Chroma (local, persistent)
          ↓
    [Scoring agent]              Gemini 3.5 Flash Lite (primary)
                                 + Groq GPT-OSS-120B (fallback)
                                 + RAG over 25 past won deals
          ↓
    [Ranked list + trace]        every score cites specific source fields
          ↓
    [Outreach drafter]           LLM-drafted message per top lead
          ↓
    [Human approval gate]        Streamlit UI: Approve / Reject / Edit
          ↓
    [Action log]                 approved leads marked "ready to contact"

---

## Free stack (zero cost)

| Layer | Tool |
|---|---|
| LLM (primary) | Google Gemini 3.5 Flash Lite (free tier, 1500 req/day) |
| LLM (fallback) | Groq GPT-OSS-120B (free tier) |
| Embeddings | `sentence-transformers` — runs locally, no API |
| Vector DB | Chroma — local, persistent |
| Backend / UI | Streamlit |
| Data | Synthetic CRM rows generated with Faker |

---


---



## Evaluation

**Eval set:** 120 leads sampled from the 781-row cleaned dataset.
Each lead is hand-labeled `good` / `not_good` by independent rule-based
criteria (NOT by the LLM). Rules combine engagement score, staleness,
deal stage, past deal value, and "do-not-contact" notes.
See `eval/build_eval_set.py`.

All numbers below are from runs against the **current** eval files
(`eval/labeled_eval_set.csv`, `eval/eval_scored.csv`), so they are
reproducible by re-running the scripts in `eval/`.

**System results (n=120):**

| Metric | Value |
|---|---|
| Precision@10 | **1.00** |
| Precision@20 | **1.00** |
| Precision@30 | **1.00** |
| Precision@50 | **1.00** |
| Random baseline precision@20 | 0.55 |
| Score range | 5 - 88 |
| Score mean | 39.0 |
| Score std | 22.0 |

**Human baselines on the same 120 leads (2 trials):**

| Trial | Time | Precision@20 |
|---|---|---|
| Deliberate mode | 3.9 min | **0.95** (19/20) |
| System (Gemini 3.5 Flash Lite + RAG) | ~6 min, no human attention | **1.00** (20/20) |

**Reading these numbers honestly:**

The system and a careful human both score near-perfectly on this set.
A human trial scored 0.95 in 3.9 minutes.
The system scored 1.00 with no human attention required at all.

The value proposition is therefore **not** "the model beats humans." It is:

1. **Consistency.** The system produced 1.00 on the first run and every
   subsequent run. Human precision varied by 15 points across two trials
   of the same person on the same data.
2. **No attention cost.** A human must sit and read 120 rows for ~4 minutes.
   The system does the same work in the background.
3. **Traceable output.** The system returns reasoning, cited fields,
   similar past wins, a drafted message, and a persisted approval
   workflow. A human sort returns a list.

We caution against over-reading the 1.00. Our ground-truth labels are
rule-based, and the LLM - prompted against past won-deal profiles -
naturally recovers the same signals. A stronger evaluation would use
labels from an independent sales team. See Known Failures below.

---

---

## Human approval gate

The system never contacts a lead. The UI (`app.py`) exposes three actions per lead:

- **Approve** — moves status to `ready to contact`
- **Reject** — marks the lead as not worth pursuing
- **Reset** — returns to `pending`

Approvals persist to `data/leads_top.csv`. This is the human-in-the-loop
control required by PS-04's objective.

---

## Traceability

Every scoring call is logged to `logs/traces.jsonl`. Each scored lead carries:

- `reasoning` — plain-English explanation citing specific field values
- `cited_fields` — comma-separated list of the fields the model used
- `similar_deal_ids` — the past won deals retrieved from the vector store
- `model_used` — which provider and model actually served the request

Example (real, from the run):

> L0237 — score 45 — *"Although the lead matches the industry and size of past
> won deals (W014, W013) which had high engagement, its current engagement is
> low (40) and budget is tight, with 123 days since last contact, reducing
> conversion likelihood."*
>
> Cited fields: `industry, company_size, engagement_score, notes, days_since_contact`
> Similar past wins: `W014, W013`

---

## Known failures / honest limitations

1. **Ground-truth labels are not fully independent of the model.**
   The label rules and the LLM scoring both weight engagement and recency.
   Precision@20 = 1.00 likely reflects this convergence rather than a hard
   test. A stronger eval would use labels from a real sales team.

2. **LLM conservatism.** The model clusters mid-quality leads around score 45.
   Ranking still works, but the score signal is narrow in that band.

3. **Provider model deprecations during build.** Gemini 1.5 and 2.5 Flash
   models were retired mid-build (2.5 gave "not available to new users").
   Groq's Llama 3.1/3.3 models were also retired mid-build. The scoring
   call is isolated behind `score_one()` with a `MODEL_FALLBACKS` list, so
   each swap was a 2-line fix — but it's real production pain.

4. **Hallucinated case studies in v1 outreach drafts.** The first version of
   the outreach prompt caused the model to interpret the `past_deal_value`
   field as "a deal we closed for them", producing false "$250K project"
   claims. Fixed with a stricter prompt. The old drafts are preserved in
   `data/leads_top_v1_with_hallucination.csv` as a documented failure case.

5. **Notes are not normalized.** The cleaning layer normalizes company names
   but not free-text notes: `"noresponse"` and `"no response"` are treated
   differently. A proper normalization pass would strip punctuation and fix
   common typos.

6. **Eval on a single provider.** The precision numbers are from Gemini runs.
   A stronger eval would cross-check scoring consistency across providers
   (Gemini vs. Groq) to catch any provider-specific bias.

---

## Folder layout

    lead-triage-copilot/
    ├── data/
    │   ├── generate_synthetic_leads.py
    │   ├── leads.csv
    │   ├── leads_clean.csv
    │   ├── leads_scored.csv
    │   ├── leads_top.csv
    │   ├── leads_top_v1_with_hallucination.csv
    │   └── won_deals_reference.csv
    ├── pipeline/
    │   ├── clean.py
    │   ├── embed_and_index.py
    │   ├── score_leads.py
    │   └── draft_outreach.py
    ├── eval/
    │   ├── build_eval_set.py
    │   ├── labeled_eval_set.csv
    │   ├── score_eval_set.py
    │   ├── eval_scored.csv
    │   ├── run_eval.py
    │   ├── compare_baseline.py
    │   ├── baseline_leads.csv
    │   └── results_summary.csv
    ├── app.py
    ├── logs/traces.jsonl
    └── README.md

---

## How to run

    # Activate environment
    .\venv\Scripts\Activate.ps1

    # 1. Generate synthetic data (~860 leads)
    python data\generate_synthetic_leads.py

    # 2. Clean and dedupe (864 → 781 after dedupe)
    python pipeline\clean.py

    # 3. Build the vector index from past won deals
    python pipeline\embed_and_index.py

    # 4. Score leads (test with sample_n=10, or remove for full run)
    python pipeline\score_leads.py

    # 5. Draft outreach for the top 20
    python pipeline\draft_outreach.py

    # 6. Launch the approval UI
    streamlit run app.py

    # 7. Reproduce the eval
    python eval\build_eval_set.py
    python eval\score_eval_set.py
    python eval\run_eval.py
    python eval\compare_baseline.py

---

## Environment

- Python 3.10.11
- Free-tier API keys required in `.env`:
  - `GEMINI_API_KEY` (primary — https://aistudio.google.com/app/apikey)
  - `GROQ_API_KEY` (fallback — https://console.groq.com/keys)
- No external services required beyond the LLM API calls
- All embeddings and vector storage run locally

