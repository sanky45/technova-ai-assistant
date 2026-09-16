from retrieval import retrieve_documents
from context_builder import build_context
from prompt import build_rag_prompt
from llm import generate_answer
from query_rewriter import rewrite_query


# ==================================================
# RAG CONFIGURATION
# ==================================================

DEFAULT_CANDIDATE_K = 10
DEFAULT_TOP_K = 5


# ==================================================
# COMPLETE RAG PIPELINE
# ==================================================

def answer_question(
    question,
    candidate_k=DEFAULT_CANDIDATE_K,
    top_k=DEFAULT_TOP_K,
    conversation_history=None
):
    """
    Execute the complete KStore-AI RAG pipeline.

    Flow:

        User Question
             ↓
        Conversation Memory
             ↓
        Query Rewriting
             ↓
        Dense Retrieval
             ↓
        Cross-Encoder Reranking
             ↓
        Context Building
             ↓
        RAG Prompt
             ↓
        Gemini
             ↓
        Final Answer

    Parameters
    ----------
    question : str
        User's original question.

    candidate_k : int
        Number of candidates retrieved from
        Pinecone before reranking.

    top_k : int
        Number of documents returned after
        reranking.

    conversation_history : list
        Previous messages from Redis.

    Returns
    -------
    dict
        Complete RAG result.
    """

    # --------------------------------------------------
    # STEP 0 — Validate question
    # --------------------------------------------------

    if not question or not question.strip():

        raise ValueError(
            "Question cannot be empty."
        )

    question = question.strip()

    # --------------------------------------------------
    # STEP 0.1 — Validate retrieval configuration
    # --------------------------------------------------

    if candidate_k <= 0:

        raise ValueError(
            "candidate_k must be greater than zero."
        )

    if top_k <= 0:

        raise ValueError(
            "top_k must be greater than zero."
        )

    if top_k > candidate_k:

        raise ValueError(
            "top_k cannot be greater than candidate_k."
        )

    # --------------------------------------------------
    # STEP 0.2 — Conversation Memory
    # --------------------------------------------------

    if conversation_history is None:

        conversation_history = []

    # --------------------------------------------------
    # STEP 1 — Rewrite Query
    # --------------------------------------------------
    #
    # IMPORTANT:
    #
    # search_query is ONLY used for retrieval.
    #
    # The original question remains unchanged
    # and is later sent to the final RAG prompt.
    #
    # --------------------------------------------------

    search_query = rewrite_query(
        question,
        conversation_history
    )

    # --------------------------------------------------
    # STEP 2 — Dense Retrieval + Reranking
    # --------------------------------------------------

    documents = retrieve_documents(
        search_query,
        candidate_k=candidate_k,
        top_k=top_k
    )

    # --------------------------------------------------
    # STEP 3 — Build Context
    # --------------------------------------------------

    context = build_context(
        documents
    )

    # --------------------------------------------------
    # STEP 4 — Build Final RAG Prompt
    # --------------------------------------------------

    prompt = build_rag_prompt(
        question=question,
        context=context,
        conversation_history=conversation_history
    )

    # --------------------------------------------------
    # STEP 5 — Generate Final Answer
    # --------------------------------------------------

    answer = generate_answer(
        prompt
    )

    # --------------------------------------------------
    # STEP 6 — Return Complete Result
    # --------------------------------------------------

    return {
        "question": question,
        "search_query": search_query,
        "answer": answer,
        "documents": documents,
        "context": context
    }