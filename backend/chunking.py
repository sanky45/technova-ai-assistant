from langchain_text_splitters import RecursiveCharacterTextSplitter


# Initial chunking configuration.
# Keep these values consistent while establishing the first retrieval baseline.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


# Prefer boundaries that preserve paragraphs and sentences before falling
# back to smaller separators. LangChain uses these in the listed order.
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_documents(documents):
    """Split extracted documents into chunks and preserve source metadata.

    Each output chunk has:
      - content: text passed to the embedding model
      - metadata: original source metadata plus a globally unique chunk_id
        and a zero-based chunk_index within its source document

    Page and slide metadata supplied by document_loader.py are retained.
    """
    if not isinstance(documents, (list, tuple)):
        raise TypeError("documents must be a list or tuple of loaded documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        add_start_index=True,
    )

    chunks = []
    global_chunk_id = 1

    for document_number, document in enumerate(documents, start=1):
        if not isinstance(document, dict):
            print(
                f"Skipping invalid document at position {document_number}: "
                "expected a dictionary."
            )
            continue

        content = document.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue

        source_metadata = document.get("metadata", {})
        if not isinstance(source_metadata, dict):
            source_metadata = {}

        split_documents = splitter.create_documents(
            texts=[content],
            metadatas=[source_metadata.copy()],
        )

        for chunk_index, split_document in enumerate(split_documents):
            chunk_text = split_document.page_content.strip()
            if not chunk_text:
                continue

            metadata = split_document.metadata.copy()
            metadata["chunk_id"] = global_chunk_id
            metadata["chunk_index"] = chunk_index

            # Preserve the original page/slide/source fields. start_index is
            # useful for tracing a retrieved chunk back to its source text.
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": metadata,
                }
            )
            global_chunk_id += 1

    return chunks
