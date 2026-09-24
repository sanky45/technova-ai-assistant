import os

import numpy as np
from huggingface_hub import InferenceClient

from config import EMBEDDING_DIMENSION


HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN is not configured.")

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN
)


def create_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    result = client.feature_extraction(
        text.strip(),
        model=EMBEDDING_MODEL
    )

    embedding = np.asarray(result)

    # HF may return token-level embeddings.
    # Convert them to a single sentence embedding if necessary.
    if embedding.ndim == 2:
        embedding = embedding.mean(axis=0)

    embedding = embedding.tolist()

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Invalid embedding dimension. "
            f"Expected {EMBEDDING_DIMENSION}, "
            f"got {len(embedding)}."
        )

    return embedding