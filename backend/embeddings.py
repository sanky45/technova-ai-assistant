
import requests

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
)

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not configured.")


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts using OpenRouter.
    The returned embeddings maintain the same order as the input texts.
    """

    if not texts:
        raise ValueError("Texts list cannot be empty.")

    cleaned_texts = []

    for text in texts:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Every text must be a non-empty string.")

        cleaned_texts.append(text.strip())

    url = f"{OPENROUTER_BASE_URL}/embeddings"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": EMBEDDING_MODEL,
        "input": cleaned_texts,
        "dimensions": EMBEDDING_DIMENSION,
        "encoding_format": "float",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        result = response.json()
        data = result["data"]

        # Restore the original input order using the API index.
        data = sorted(data, key=lambda item: item["index"])

        if len(data) != len(cleaned_texts):
            raise ValueError(
                f"Expected {len(cleaned_texts)} embeddings, "
                f"received {len(data)}."
            )

        embeddings = []

        for item in data:
            embedding = item["embedding"]

            if len(embedding) != EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Invalid embedding dimension. "
                    f"Expected {EMBEDDING_DIMENSION}, "
                    f"got {len(embedding)}."
                )

            embeddings.append(embedding)

        return embeddings

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"OpenRouter embedding API request failed: {exc}"
        ) from exc


def create_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a single text.
    Used for query embedding during retrieval.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text cannot be empty.")

    return create_embeddings([text])[0]
