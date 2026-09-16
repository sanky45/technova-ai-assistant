from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_documents(
    documents
):
    """
    Split loaded documents into chunks
    with globally unique chunk IDs.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = []

    global_chunk_id = 1

    for document in documents:

        content = document.get(
            "content",
            ""
        )

        if not content or not content.strip():
            continue

        split_texts = splitter.split_text(
            content
        )

        for text in split_texts:

            metadata = document.get(
                "metadata",
                {}
            ).copy()

            metadata["chunk_id"] = (
                global_chunk_id
            )

            chunks.append(
                {
                    "content": text,
                    "metadata": metadata
                }
            )

            global_chunk_id += 1

    return chunks