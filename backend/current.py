from document_loader import load_documents
from chunking import chunk_documents
from embeddings import create_embedding
from vectorstore import search_vectors


# ==================================================
# LOAD DOCUMENTS
# ==================================================

print("=" * 70)
print("KStore-AI CURRENT SYSTEM TEST")
print("=" * 70)

documents = load_documents()

print(
    f"\nDocuments loaded: {len(documents)}"
)


# ==================================================
# CREATE CHUNKS
# ==================================================

chunks = chunk_documents(
    documents
)

print(
    f"Chunks created: {len(chunks)}"
)


# ==================================================
# TEST QUESTIONS
# ==================================================

test_questions = [

    "How many casual leaves does TechNova provide?",

    "What is the standard notice period?",

    "What approval is required for VPN access?",

    "What technology is used for file storage?"
]


# ==================================================
# RETRIEVAL TEST
# ==================================================

for question_number, question in enumerate(
    test_questions,
    start=1
):

    print("\n")
    print("=" * 70)

    print(
        f"TEST CASE {question_number}"
    )

    print("=" * 70)

    print(
        f"\nQuestion:\n{question}"
    )


    # --------------------------------------------------
    # Create query embedding
    # --------------------------------------------------

    query_embedding = create_embedding(
        question
    )


    # --------------------------------------------------
    # Pinecone retrieval
    # --------------------------------------------------

    results = search_vectors(
        query_embedding,
        top_k=5
    )


    matches = results[
        "matches"
    ]


    # --------------------------------------------------
    # Display results
    # --------------------------------------------------

    print("\nRetrieved Results:")
    print("-" * 70)


    for rank, match in enumerate(
        matches,
        start=1
    ):

        metadata = match.get(
            "metadata",
            {}
        )


        print(
            f"\nRank {rank}"
        )

        print(
            f"Score: "
            f"{match.get('score')}"
        )

        print(
            f"File: "
            f"{metadata.get('file_name')}"
        )

        print(
            f"Page: "
            f"{metadata.get('page', 'N/A')}"
        )

        print(
            f"Slide: "
            f"{metadata.get('slide', 'N/A')}"
        )

        print(
            f"Chunk ID: "
            f"{metadata.get('chunk_id', 'N/A')}"
        )

        print(
            "\nContent:"
        )

        print(
            metadata.get(
                "content",
                ""
            )[:500]
        )


# ==================================================
# END
# ==================================================

print("\n")
print("=" * 70)

print(
    "CURRENT SYSTEM TEST COMPLETED"
)

print("=" * 70)