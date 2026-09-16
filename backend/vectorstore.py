from hashlib import sha256

from pinecone import Pinecone, ServerlessSpec

from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_DIMENSION
)


# --------------------------------------------------
# Pinecone configuration
# --------------------------------------------------

PINECONE_NAMESPACE = "technova"

UPSERT_BATCH_SIZE = 100
DELETE_BATCH_SIZE = 100


# --------------------------------------------------
# Pinecone client
# --------------------------------------------------

if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is not configured."
    )


pc = Pinecone(
    api_key=PINECONE_API_KEY
)


# --------------------------------------------------
# Create index
# --------------------------------------------------

def create_index():
    """
    Create Pinecone index if it does not already exist.
    """

    existing_indexes = [
        index.name
        for index in pc.list_indexes()
    ]

    if PINECONE_INDEX_NAME in existing_indexes:

        print(
            f"Index already exists: "
            f"{PINECONE_INDEX_NAME}"
        )

        return pc.Index(
            PINECONE_INDEX_NAME
        )

    print(
        f"Creating index: "
        f"{PINECONE_INDEX_NAME}"
    )

    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

    print(
        "Index created successfully."
    )

    return pc.Index(
        PINECONE_INDEX_NAME
    )


# --------------------------------------------------
# Get index
# --------------------------------------------------

def get_index():
    """
    Get the configured Pinecone index.

    If the index does not exist, create it first.
    """

    existing_indexes = [
        index.name
        for index in pc.list_indexes()
    ]

    if PINECONE_INDEX_NAME not in existing_indexes:

        print(
            f"Index not found: "
            f"{PINECONE_INDEX_NAME}"
        )

        print(
            "Creating Pinecone index..."
        )

        create_index()

    return pc.Index(
        PINECONE_INDEX_NAME
    )


# --------------------------------------------------
# Document key
# --------------------------------------------------

def create_document_key(
    file_name: str
) -> str:
    """
    Create a stable identifier for a document.

    The same file name produces the same
    document key.
    """

    if not file_name:

        raise ValueError(
            "file_name cannot be empty."
        )

    document_hash = sha256(
        file_name.encode("utf-8")
    ).hexdigest()

    return document_hash[:16]


# --------------------------------------------------
# Vector ID
# --------------------------------------------------

def create_vector_id(
    file_name: str,
    file_hash: str,
    chunk_id: int
) -> str:
    """
    Create a deterministic Pinecone vector ID.

    Vector identity consists of:

        document
        document version
        chunk

    Example:

        doc-a81c29f7e41a32bc
        -v-9f82ab31c72e8d11
        -chunk-1
    """

    if not file_name:

        raise ValueError(
            "file_name cannot be empty."
        )

    if not file_hash:

        raise ValueError(
            "file_hash cannot be empty."
        )

    if chunk_id is None:

        raise ValueError(
            "chunk_id cannot be None."
        )

    document_key = create_document_key(
        file_name
    )

    return (
        f"doc-{document_key}"
        f"-v-{file_hash[:16]}"
        f"-chunk-{chunk_id}"
    )


# --------------------------------------------------
# Build vector metadata
# --------------------------------------------------

def build_vector_metadata(
    chunk,
    file_hash
):
    """
    Build metadata stored alongside
    the Pinecone vector.
    """

    metadata = chunk.get(
        "metadata",
        {}
    ).copy()

    metadata["file_hash"] = file_hash

    # Store the actual chunk text.
    # This will be used later when
    # building the RAG context.
    metadata["content"] = chunk.get(
        "content",
        ""
    )

    return metadata


# --------------------------------------------------
# Build vectors
# --------------------------------------------------

def build_vectors(
    chunks,
    embeddings,
    file_hash
):
    """
    Combine chunks and embeddings into
    Pinecone vector records.
    """

    if not chunks:

        return []

    if not embeddings:

        raise ValueError(
            "Embeddings cannot be empty."
        )

    if len(chunks) != len(embeddings):

        raise ValueError(
            "Number of chunks and embeddings "
            "must be the same."
        )

    if not file_hash:

        raise ValueError(
            "file_hash cannot be empty."
        )

    vectors = []

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):

        metadata = chunk.get(
            "metadata",
            {}
        )

        file_name = metadata.get(
            "file_name"
        )

        chunk_id = metadata.get(
            "chunk_id"
        )

        # -----------------------------------------
        # Metadata validation
        # -----------------------------------------

        if not file_name:

            raise ValueError(
                "Chunk metadata is missing "
                "file_name."
            )

        if chunk_id is None:

            raise ValueError(
                "Chunk metadata is missing "
                "chunk_id."
            )

        # -----------------------------------------
        # Embedding validation
        # -----------------------------------------

        if len(embedding) != EMBEDDING_DIMENSION:

            raise ValueError(
                f"Invalid embedding dimension "
                f"for {file_name}, "
                f"chunk {chunk_id}. "
                f"Expected "
                f"{EMBEDDING_DIMENSION}, "
                f"got {len(embedding)}."
            )

        # -----------------------------------------
        # Vector ID
        # -----------------------------------------

        vector_id = create_vector_id(
            file_name,
            file_hash,
            chunk_id
        )

        # -----------------------------------------
        # Metadata
        # -----------------------------------------

        vector_metadata = (
            build_vector_metadata(
                chunk,
                file_hash
            )
        )

        # -----------------------------------------
        # Pinecone vector
        # -----------------------------------------

        vector = {
            "id": vector_id,
            "values": embedding,
            "metadata": vector_metadata
        }

        vectors.append(
            vector
        )

    return vectors


# --------------------------------------------------
# Upsert vectors
# --------------------------------------------------

def upsert_vectors(
    vectors
):
    """
    Upload vectors to Pinecone in batches.
    """

    if not vectors:

        return

    index = get_index()

    total_vectors = len(
        vectors
    )

    print(
        f"  → Uploading "
        f"{total_vectors} vectors to Pinecone..."
    )

    for start in range(
        0,
        total_vectors,
        UPSERT_BATCH_SIZE
    ):

        end = min(
            start + UPSERT_BATCH_SIZE,
            total_vectors
        )

        batch = vectors[
            start:end
        ]

        index.upsert(
            vectors=batch,
            namespace=PINECONE_NAMESPACE
        )

        print(
            f"  → Pinecone uploaded "
            f"{end}/{total_vectors}"
        )


# --------------------------------------------------
# Upsert documents
# --------------------------------------------------

def upsert_documents(
    chunks,
    embeddings,
    file_hash
):
    """
    Store document chunks and embeddings
    in Pinecone.
    """

    if not chunks:

        raise ValueError(
            "Cannot index a document "
            "with zero chunks."
        )

    vectors = build_vectors(
        chunks,
        embeddings,
        file_hash
    )

    upsert_vectors(
        vectors
    )

    print(
        f"\nSuccessfully uploaded "
        f"{len(vectors)} vectors to Pinecone."
    )

    return {
        "vector_count": len(vectors),
        "namespace": PINECONE_NAMESPACE
    }


# --------------------------------------------------
# Delete document version
# --------------------------------------------------

def delete_document_version(
    file_name,
    file_hash,
    chunk_count
):
    """
    Delete vectors belonging to a specific
    document version.

    Used after a new version has been
    successfully indexed.
    """

    if not file_name:

        raise ValueError(
            "file_name cannot be empty."
        )

    if not file_hash:

        return

    if chunk_count <= 0:

        return

    index = get_index()

    # -----------------------------------------
    # Build vector IDs
    # -----------------------------------------

    vector_ids = [
        create_vector_id(
            file_name,
            file_hash,
            chunk_id
        )
        for chunk_id in range(
            1,
            chunk_count + 1
        )
    ]

    total_vectors = len(
        vector_ids
    )

    print(
        f"  → Removing "
        f"{total_vectors} old vectors..."
    )

    # -----------------------------------------
    # Delete in batches
    # -----------------------------------------

    for start in range(
        0,
        total_vectors,
        DELETE_BATCH_SIZE
    ):

        end = min(
            start + DELETE_BATCH_SIZE,
            total_vectors
        )

        batch = vector_ids[
            start:end
        ]

        index.delete(
            ids=batch,
            namespace=PINECONE_NAMESPACE
        )

        print(
            f"  → Pinecone deleted "
            f"{end}/{total_vectors}"
        )


# --------------------------------------------------
# Search vectors
# --------------------------------------------------

def search_vectors(
    query_embedding,
    top_k=5
):
    """
    Search Pinecone for the most similar
    document chunks.

    Used by retrieval.py.
    """

    if not query_embedding:

        raise ValueError(
            "Query embedding cannot be empty."
        )

    if len(query_embedding) != EMBEDDING_DIMENSION:

        raise ValueError(
            f"Invalid query embedding dimension. "
            f"Expected "
            f"{EMBEDDING_DIMENSION}, "
            f"got {len(query_embedding)}."
        )

    if top_k <= 0:

        raise ValueError(
            "top_k must be greater than zero."
        )

    index = get_index()

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=PINECONE_NAMESPACE,
        include_metadata=True
    )

    return results