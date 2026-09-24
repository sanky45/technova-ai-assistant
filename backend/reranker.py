import os

import requests
from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# OpenRouter configuration
# --------------------------------------------------

OPENROUTER_API_URL = (
    "https://openrouter.ai/api/v1/rerank"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

RERANKER_MODEL_NAME = os.getenv(
    "OPENROUTER_RERANK_MODEL",
    "cohere/rerank-v3.5"
)


# --------------------------------------------------
# Configuration validation
# --------------------------------------------------

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not configured."
    )


# --------------------------------------------------
# Rerank retrieved documents
# --------------------------------------------------

def rerank_documents(
    query,
    documents,
    top_k=5
):
    """
    Re-rank documents retrieved from Pinecone
    using the OpenRouter Rerank API.

    Pipeline:

        Pinecone candidates
              ↓
        OpenRouter Reranker
              ↓
        Ranked documents
              ↓
             Top-K

    Parameters
    ----------
    query : str
        User's question.

    documents : list
        Documents returned by Pinecone.

    top_k : int
        Number of final documents to return.

    Returns
    -------
    list
        Re-ranked documents containing:

        - id
        - pinecone_score
        - rerank_score
        - metadata
    """

    # --------------------------------------------------
    # Validate query
    # --------------------------------------------------

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    # --------------------------------------------------
    # Validate top_k
    # --------------------------------------------------

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    # --------------------------------------------------
    # No documents
    # --------------------------------------------------

    if not documents:
        return []

    # --------------------------------------------------
    # Create document list
    # --------------------------------------------------

    rerank_documents_list = []
    valid_documents = []

    for document in documents:

        metadata = document.get(
            "metadata",
            {}
        )

        content = metadata.get(
            "content",
            ""
        )

        # ----------------------------------------------
        # Ignore documents without content
        # ----------------------------------------------

        if not content or not content.strip():
            continue

        rerank_documents_list.append(
            content
        )

        valid_documents.append(
            document
        )

    # --------------------------------------------------
    # No valid documents
    # --------------------------------------------------

    if not rerank_documents_list:
        return []

    # --------------------------------------------------
    # OpenRouter request
    # --------------------------------------------------

    response = requests.post(
        OPENROUTER_API_URL,
        headers={
            "Authorization": (
                f"Bearer {OPENROUTER_API_KEY}"
            ),
            "Content-Type": "application/json",
        },
        json={
            "model": RERANKER_MODEL_NAME,
            "query": query.strip(),
            "documents": rerank_documents_list,
            "top_n": min(
                top_k,
                len(rerank_documents_list)
            ),
        },
        timeout=60,
    )

    # --------------------------------------------------
    # Handle API errors
    # --------------------------------------------------

    if response.status_code != 200:

        raise RuntimeError(
            "OpenRouter reranking failed. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

    # --------------------------------------------------
    # Parse response
    # --------------------------------------------------

    result = response.json()

    results = result.get(
        "results",
        []
    )

    # --------------------------------------------------
    # Build ranked documents
    # --------------------------------------------------

    ranked_documents = []

    for result_item in results:

        index = result_item.get(
            "index"
        )

        if index is None:
            continue

        if index >= len(valid_documents):
            continue

        document = valid_documents[index]

        metadata = document.get(
            "metadata",
            {}
        ).copy()

        ranked_document = {

            # ------------------------------------------
            # Pinecone vector ID
            # ------------------------------------------

            "id": document.get(
                "id"
            ),

            # ------------------------------------------
            # Original Pinecone similarity score
            # ------------------------------------------

            "pinecone_score": float(
                document.get(
                    "score",
                    0.0
                )
            ),

            # ------------------------------------------
            # OpenRouter reranker score
            # ------------------------------------------

            "rerank_score": float(
                result_item.get(
                    "relevance_score",
                    0.0
                )
            ),

            # ------------------------------------------
            # Document metadata
            # ------------------------------------------

            "metadata": metadata
        }

        ranked_documents.append(
            ranked_document
        )

    return ranked_documents