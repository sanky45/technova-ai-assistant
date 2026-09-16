from sentence_transformers import CrossEncoder


# --------------------------------------------------
# Reranker configuration
# --------------------------------------------------

RERANKER_MODEL_NAME = (
    "cross-encoder/ms-marco-MiniLM-L6-v2"
)


# --------------------------------------------------
# Load reranker model
# --------------------------------------------------

reranker_model = CrossEncoder(
    RERANKER_MODEL_NAME
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
    using a Cross-Encoder.

    Pipeline:

        Pinecone candidates
              ↓
        Cross-Encoder
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
    # Create query-document pairs
    # --------------------------------------------------

    pairs = []

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

        pairs.append(
            (
                query,
                content
            )
        )

        valid_documents.append(
            document
        )

    # --------------------------------------------------
    # No valid documents
    # --------------------------------------------------

    if not pairs:

        return []

    # --------------------------------------------------
    # Generate Cross-Encoder scores
    # --------------------------------------------------

    scores = reranker_model.predict(
        pairs
    )

    # --------------------------------------------------
    # Build ranked documents
    # --------------------------------------------------

    ranked_documents = []

    for document, score in zip(
        valid_documents,
        scores
    ):

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
            # Cross-Encoder relevance score
            # ------------------------------------------

            "rerank_score": float(
                score
            ),

            # ------------------------------------------
            # Document metadata
            # ------------------------------------------

            "metadata": metadata
        }

        ranked_documents.append(
            ranked_document
        )

    # --------------------------------------------------
    # Sort by Cross-Encoder score
    # --------------------------------------------------

    ranked_documents.sort(
        key=lambda document:
            document["rerank_score"],
        reverse=True
    )

    # --------------------------------------------------
    # Return Top-K documents
    # --------------------------------------------------

    return ranked_documents[
        :top_k
    ]