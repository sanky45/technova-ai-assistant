from retrieval import retrieve_documents


# --------------------------------------------------
# Ground-truth test cases
# --------------------------------------------------

TEST_CASES = [

    {
        "question": "How many casual leaves does TechNova provide?",
        "expected_files": [
            "TechNova_HR_Policy.pdf"
        ]
    },

    {
        "question": "What is the standard notice period?",
        "expected_files": [
            "TechNova_HR_Policy.pdf"
        ]
    },

    {
        "question": "What approval is required for VPN access?",
        "expected_files": [
            "TechNova_IT_SOP.pdf"
        ]
    },

    {
        "question": "What technology is used for file storage?",
        "expected_files": [
            "TechNova_Azure_Deployment_Guide.docx"
        ]
    }
]


# --------------------------------------------------
# Evaluate one query
# --------------------------------------------------

def evaluate_query(
    question,
    expected_files,
    top_k=5
):
    """
    Retrieve documents and calculate
    file-level precision and recall.
    """

    results = retrieve_documents(
        question,
        top_k=top_k
    )

    retrieved_files = set()

    for match in results["matches"]:

        metadata = match.get(
            "metadata",
            {}
        )

        file_name = metadata.get(
            "file_name"
        )

        if file_name:
            retrieved_files.add(
                file_name
            )

    expected_files = set(
        expected_files
    )

    # Relevant retrieved files
    true_positives = (
        retrieved_files
        & expected_files
    )

    # Retrieved but not expected
    false_positives = (
        retrieved_files
        - expected_files
    )

    # Expected but not retrieved
    false_negatives = (
        expected_files
        - retrieved_files
    )

    # Precision
    if retrieved_files:
        precision = (
            len(true_positives)
            / len(retrieved_files)
        )
    else:
        precision = 0.0

    # Recall
    if expected_files:
        recall = (
            len(true_positives)
            / len(expected_files)
        )
    else:
        recall = 0.0

    return {
        "question": question,
        "retrieved_files": retrieved_files,
        "expected_files": expected_files,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall
    }


# --------------------------------------------------
# Run complete evaluation
# --------------------------------------------------

def run_evaluation():

    all_results = []

    for test_case in TEST_CASES:

        result = evaluate_query(
            question=test_case["question"],
            expected_files=test_case["expected_files"],
            top_k=5
        )

        all_results.append(result)

    return all_results


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    results = run_evaluation()

    print("\n")
    print("=" * 70)
    print("RETRIEVAL EVALUATION")
    print("=" * 70)

    total_precision = 0
    total_recall = 0

    for number, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nTest Case {number}"
        )

        print(
            f"Question: "
            f"{result['question']}"
        )

        print(
            f"\nExpected:"
        )

        for file_name in result[
            "expected_files"
        ]:
            print(
                f"  ✓ {file_name}"
            )

        print(
            f"\nRetrieved:"
        )

        for file_name in result[
            "retrieved_files"
        ]:
            print(
                f"  → {file_name}"
            )

        print(
            f"\nPrecision: "
            f"{result['precision']:.2f}"
        )

        print(
            f"Recall: "
            f"{result['recall']:.2f}"
        )

        total_precision += (
            result["precision"]
        )

        total_recall += (
            result["recall"]
        )

    # --------------------------------------------------
    # Average metrics
    # --------------------------------------------------

    test_count = len(results)

    average_precision = (
        total_precision / test_count
    )

    average_recall = (
        total_recall / test_count
    )

    print("\n")
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    print(
        f"\nAverage Precision: "
        f"{average_precision:.2%}"
    )

    print(
        f"Average Recall: "
        f"{average_recall:.2%}"
    )