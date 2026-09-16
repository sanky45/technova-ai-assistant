from retrieval import retrieve_documents


# ==================================================
# TEST DATA
# ==================================================

TEST_CASES = [

    {
        "question": "How many casual leaves does TechNova provide?",
        "expected": [
            "TechNova_HR_Policy.pdf"
        ]
    },

    {
        "question": "What is the standard notice period?",
        "expected": [
            "TechNova_HR_Policy.pdf"
        ]
    },

    {
        "question": "What approval is required for VPN access?",
        "expected": [
            "TechNova_IT_SOP.pdf"
        ]
    },

    {
        "question": "What technology is used for file storage?",
        "expected": [
            "TechNova_Azure_Deployment_Guide.docx"
        ]
    }
]


# ==================================================
# CONFIGURATION
# ==================================================

FINAL_TOP_K = 5
CANDIDATE_TOP_K = 10


# ==================================================
# PRECISION
# ==================================================

def calculate_precision(
    retrieved_files,
    expected_files
):
    """
    Precision:

        Relevant retrieved documents
        -----------------------------
        Total retrieved documents
    """

    if not retrieved_files:
        return 0.0

    relevant = sum(
        1
        for file_name in retrieved_files
        if file_name in expected_files
    )

    return relevant / len(
        retrieved_files
    )


# ==================================================
# RECALL
# ==================================================

def calculate_recall(
    retrieved_files,
    expected_files
):
    """
    Recall:

        Relevant retrieved documents
        -----------------------------
        Total expected documents
    """

    if not expected_files:
        return 0.0

    relevant = sum(
        1
        for file_name in retrieved_files
        if file_name in expected_files
    )

    return relevant / len(
        expected_files
    )


# ==================================================
# MAIN EVALUATION
# ==================================================

def main():

    print("=" * 70)
    print("KStore-AI RETRIEVAL EVALUATION")
    print("Pinecone + Cross-Encoder Reranker")
    print("=" * 70)

    print(
        f"\nCandidate Top-K : {CANDIDATE_TOP_K}"
    )

    print(
        f"Final Top-K     : {FINAL_TOP_K}"
    )


    total_precision = 0.0
    total_recall = 0.0


    # ==================================================
    # RUN TEST CASES
    # ==================================================

    for case_number, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        question = test_case[
            "question"
        ]

        expected_files = test_case[
            "expected"
        ]


        print("\n")
        print("=" * 70)

        print(
            f"Test Case {case_number}"
        )

        print("=" * 70)

        print(
            f"Question: {question}"
        )


        print("\nExpected:")

        for file_name in expected_files:

            print(
                f"  ✓ {file_name}"
            )


        # --------------------------------------------------
        # Retrieve using the complete pipeline
        # --------------------------------------------------

        results = retrieve_documents(
            question,
            top_k=FINAL_TOP_K,
            candidate_k=CANDIDATE_TOP_K
        )


        # --------------------------------------------------
        # Extract file names
        # --------------------------------------------------

        retrieved_files = []

        for result in results:

            metadata = result.get(
                "metadata",
                {}
            )

            file_name = metadata.get(
                "file_name"
            )

            if file_name:
                retrieved_files.append(
                    file_name
                )


        # --------------------------------------------------
        # Display retrieved documents
        # --------------------------------------------------

        print("\nRetrieved:")

        for result in results:

            metadata = result.get(
                "metadata",
                {}
            )

            print(
                f"  → "
                f"{metadata.get('file_name')}"
            )

            print(
                f"     Pinecone score: "
                f"{result.get('pinecone_score')}"
            )

            print(
                f"     Reranker score: "
                f"{result.get('rerank_score')}"
            )


        # --------------------------------------------------
        # Calculate metrics
        # --------------------------------------------------

        precision = calculate_precision(
            retrieved_files,
            expected_files
        )

        recall = calculate_recall(
            retrieved_files,
            expected_files
        )


        total_precision += precision
        total_recall += recall


        print(
            f"\nPrecision: "
            f"{precision:.2f}"
        )

        print(
            f"Recall: "
            f"{recall:.2f}"
        )


    # ==================================================
    # FINAL RESULTS
    # ==================================================

    number_of_tests = len(
        TEST_CASES
    )

    average_precision = (
        total_precision /
        number_of_tests
    )

    average_recall = (
        total_recall /
        number_of_tests
    )


    print("\n")
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    print(
        f"\nAverage Precision: "
        f"{average_precision * 100:.2f}%"
    )

    print(
        f"Average Recall: "
        f"{average_recall * 100:.2f}%"
    )


    # ==================================================
    # BASELINE COMPARISON
    # ==================================================

    print("\n")
    print("=" * 70)
    print("BASELINE COMPARISON")
    print("=" * 70)

    print(
        "\nPrevious Pinecone-only baseline:"
    )

    print(
        "  Precision: 25.83%"
    )

    print(
        "  Recall:    100.00%"
    )

    print(
        "\nCurrent Pinecone + Reranker:"
    )

    print(
        f"  Precision: "
        f"{average_precision * 100:.2f}%"
    )

    print(
        f"  Recall:    "
        f"{average_recall * 100:.2f}%"
    )


    precision_change = (
        average_precision * 100
    ) - 25.83

    recall_change = (
        average_recall * 100
    ) - 100.00


    print("\nChange:")

    print(
        f"  Precision: "
        f"{precision_change:+.2f}%"
    )

    print(
        f"  Recall:    "
        f"{recall_change:+.2f}%"
    )


    print("\n")
    print("=" * 70)
    print("EVALUATION COMPLETED")
    print("=" * 70)


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()