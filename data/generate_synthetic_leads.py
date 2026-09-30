import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("en_IN")
random.seed(42)

INDUSTRIES = ["Retail", "SaaS", "Manufacturing", "Healthcare", "Logistics"]
STAGES = ["New", "Contacted", "Qualified"]
SIZES = ["10-50", "50-200", "200-500", "500-2000", "2000-5000"]


def make_lead(i):
    industry = random.choice(INDUSTRIES)
    size = random.choice(SIZES)
    engagement = random.randint(0, 100)
    days_ago = random.randint(0, 400)
    last_contacted = datetime.today() - timedelta(days=days_ago)

    last_contacted_str = "" if random.random() < 0.10 else last_contacted.strftime("%Y-%m-%d")
    past_deal_value = "" if random.random() < 0.15 else random.choice([50000, 120000, 250000, 500000])

    notes = random.choice([
        "Interested in demo, follow up next week.",
        "Said budget is tight this quarter.",
        "Met at conference, warm intro.",
        "Requested pricing sheet, no response since.",
        "Currently evaluating competitors.",
        "",
        "Do not contact until Q3.",
    ])

    return {
        "lead_id": f"L{i:04d}",
        "company_name": fake.company(),
        "industry": industry,
        "company_size": size,
        "last_contacted": last_contacted_str,
        "engagement_score": engagement,
        "deal_stage": random.choice(STAGES),
        "notes": notes,
        "past_deal_value": past_deal_value,
    }


def generate(n=800):
    leads = [make_lead(i) for i in range(1, n + 1)]
    df = pd.DataFrame(leads)

    dupes = df.sample(frac=0.08).copy()
    dupes["lead_id"] = [f"L{9000+i}" for i in range(len(dupes))]
    dupes["company_name"] = dupes["company_name"].apply(lambda x: x + " Pvt Ltd")
    df = pd.concat([df, dupes], ignore_index=True)

    df.to_csv("data/leads.csv", index=False)
    print(f"Wrote {len(df)} leads to data/leads.csv")


def generate_won_deals(n=25):
    rows = []
    for i in range(n):
        rows.append({
            "deal_id": f"W{i:03d}",
            "industry": random.choice(INDUSTRIES),
            "company_size": random.choice(SIZES),
            "engagement_score_at_win": random.randint(70, 100),
            "deal_value": random.choice([100000, 250000, 500000, 1000000]),
            "notes": random.choice([
                "Champion was VP of Ops. Fast decision cycle.",
                "Came inbound after a webinar. High intent.",
                "Referred by existing customer.",
                "Evaluated 3 vendors, chose us on integrations.",
            ]),
        })
    pd.DataFrame(rows).to_csv("data/won_deals_reference.csv", index=False)
    print(f"Wrote {len(rows)} won deals to data/won_deals_reference.csv")


if __name__ == "__main__":
    generate()
    generate_won_deals()