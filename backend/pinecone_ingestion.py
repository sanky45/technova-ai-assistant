from vectorstore import (
    upsert_documents,
    delete_document_version
)


def index_document(
    chunks: list[dict],
    embeddings: list[list[float]],
    file_hash: str,
    previous_file_hash: str | None = None,
    previous_chunk_count: int = 0
):
    """
    Index a document into Pinecone.

    New vectors are uploaded first.

    Previous vectors are removed only after
    the new document version has been
    successfully uploaded.
    """

    # --------------------------------------------------
    # Validate input
    # --------------------------------------------------

    if not chunks:
        raise ValueError(
            "Cannot index a document with zero chunks."
        )

    if not embeddings:
        raise ValueError(
            "Cannot index a document with zero embeddings."
        )

    if not file_hash:
        raise ValueError(
            "file_hash cannot be empty."
        )

    # --------------------------------------------------
    # Upload new document version
    # --------------------------------------------------

    print(
        "  → Uploading new document version..."
    )

    result = upsert_documents(
        chunks=chunks,
        embeddings=embeddings,
        file_hash=file_hash
    )

    print(
        "  → New document version indexed successfully"
    )

    # --------------------------------------------------
    # Remove previous document version
    # --------------------------------------------------

    if (
        previous_file_hash
        and previous_file_hash != file_hash
        and previous_chunk_count > 0
    ):

        file_name = chunks[0].get(
            "metadata",
            {}
        ).get(
            "file_name"
        )

        if not file_name:
            raise ValueError(
                "Chunk metadata is missing file_name."
            )

        print(
            "  → Removing previous "
            "document version..."
        )

        delete_document_version(
            file_name=file_name,
            file_hash=previous_file_hash,
            chunk_count=previous_chunk_count
        )

        print(
            "  → Previous document version "
            "removed successfully"
        )

    # --------------------------------------------------
    # Return result
    # --------------------------------------------------

    return result