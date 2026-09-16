from embeddings import create_embedding
from vectorstore import search_vectors
from reranker import rerank_documents


def retrieve_documents(
    query,
    top_k=5,
    candidate_k=10
):
    """
    Retrieve documents using a two-stage pipeline.

    Stage 1:
        Dense semantic retrieval using Pinecone.

    Stage 2:
        Cross-Encoder reranking.

    Parameters
    ----------
    query : str
        User's question.

    top_k : int
        Number of final documents returned.

    candidate_k : int
        Number of candidates retrieved from Pinecone
        before reranking.
    """

    # --------------------------------------------------
    # Stage 1 — Query embedding
    # --------------------------------------------------

    query_embedding = create_embedding(
        query
    )


    # --------------------------------------------------
    # Stage 2 — Dense retrieval
    # --------------------------------------------------

    results = search_vectors(
        query_embedding,
        top_k=candidate_k
    )

    candidates = results[
        "matches"
    ]


    # --------------------------------------------------
    # Stage 3 — Cross-Encoder reranking
    # --------------------------------------------------

    reranked_documents = rerank_documents(
        query,
        candidates,
        top_k=top_k
    )


    # --------------------------------------------------
    # Return final results
    # --------------------------------------------------

    return reranked_documents