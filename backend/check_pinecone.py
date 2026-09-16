from vectorstore import get_index


def main():

    index = get_index()

    stats = index.describe_index_stats()

    print("\nPinecone Index Statistics")
    print("=========================")

    print(stats)

    print("\nNamespaces")
    print("==========")

    for namespace, details in stats.get(
        "namespaces",
        {}
    ).items():

        print(
            f"{namespace}: "
            f"{details.get('vector_count', 0)} vectors"
        )


if __name__ == "__main__":
    main()