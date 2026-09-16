from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = (
    "BAAI/bge-small-en-v1.5"
)

EMBEDDING_DIMENSION = 384


embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)


def create_embedding(
    text: str
) -> list[float]:
    """
    Convert a single text string into
    a normalized embedding vector.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot create embedding for empty text."
        )

    embedding = embedding_model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def create_embeddings(
    texts: list[str]
) -> list[list[float]]:
    """
    Convert multiple text strings into
    normalized embedding vectors.
    """

    if not texts:
        return []

    cleaned_texts = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not cleaned_texts:
        return []

    embeddings = embedding_model.encode(
        cleaned_texts,
        normalize_embeddings=True
    )

    return embeddings.tolist()