from embeddings import create_embedding
from vectorstore import search_vectors


def main():

    query = "What is TechNova's leave policy?"

    embedding = create_embedding(query)

    results = search_vectors(
        embedding,
        top_k=1
    )

    matches = results.get(
        "matches",
        []
    )

    if not matches:
        print("No matches found.")
        return

    match = matches[0]

    print("\nFull Pinecone Match")
    print("===================")

    print(match)

    print("\nMetadata")
    print("========")

    print(
        match.get(
            "metadata",
            {}
        )
    )


if __name__ == "__main__":
    main()