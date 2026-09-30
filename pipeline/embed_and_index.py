import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "won_deals"


def build_won_deal_text(row):
    return (
        f"Industry: {row['industry']}. "
        f"Company size: {row['company_size']}. "
        f"Engagement at win: {row['engagement_score_at_win']}. "
        f"Notes: {row['notes']}"
    )


def main():
    df = pd.read_csv("data/won_deals_reference.csv")
    texts = df.apply(build_won_deal_text, axis=1).tolist()

    print("Loading embedding model (first run downloads ~80MB)...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path="data/chroma")
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=df["deal_id"].tolist(),
        embeddings=embeddings,
        documents=texts,
        metadatas=df.to_dict(orient="records"),
    )
    print(f"Indexed {len(df)} won deals into Chroma at data/chroma")


if __name__ == "__main__":
    main()