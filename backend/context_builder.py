# --------------------------------------------------
# Build RAG Context
# --------------------------------------------------

def build_context(
    documents
):
    """
    Convert reranked documents into a single
    structured context string for the LLM.

    Parameters
    ----------
    documents : list
        Reranked documents returned by retrieval.

    Returns
    -------
    str
        Formatted context containing document
        content and source information.
    """

    # --------------------------------------------------
    # No documents
    # --------------------------------------------------

    if not documents:
        return ""

    context_parts = []

    # --------------------------------------------------
    # Process documents in reranked order
    # --------------------------------------------------

    for rank, document in enumerate(
        documents,
        start=1
    ):

        metadata = document.get(
            "metadata",
            {}
        )

        # --------------------------------------------------
        # Extract content
        # --------------------------------------------------

        content = metadata.get(
            "content",
            ""
        )

        if not content:
            continue

        content = content.strip()

        if not content:
            continue

        # --------------------------------------------------
        # Extract source information
        # --------------------------------------------------

        file_name = metadata.get(
            "file_name",
            "Unknown"
        )

        page = metadata.get(
            "page"
        )

        slide = metadata.get(
            "slide"
        )

        # --------------------------------------------------
        # Build source label
        # --------------------------------------------------

        source = file_name

        if page is not None:

            source += (
                f" | Page {page}"
            )

        if slide is not None:

            source += (
                f" | Slide {slide}"
            )

        # --------------------------------------------------
        # Build context block
        # --------------------------------------------------

        context_block = (
            f"[Document {rank}]\n"
            f"Source: {source}\n"
            f"Content:\n"
            f"{content}"
        )

        context_parts.append(
            context_block
        )

    # --------------------------------------------------
    # No valid content
    # --------------------------------------------------

    if not context_parts:
        return ""

    # --------------------------------------------------
    # Combine context blocks
    # --------------------------------------------------

    return "\n\n".join(
        context_parts
    )