import csv
import os
from pathlib import Path

from neo4j import GraphDatabase


OUTPUT_DIR = Path("experiment_results/atomic_reconstruction")
SUMMARY_FILE = OUTPUT_DIR / "atomic_reconstruction_summary.csv"
CATEGORY_FILE = OUTPUT_DIR / "atomic_reconstruction_by_category.csv"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jPass123")


CATEGORIES = [
    {
        "category": "language",
        "inline_property": "inline_language",
        "inline_expression": "w.inline_language",
    },
    {
        "category": "is_oa",
        "inline_property": "inline_is_oa",
        "inline_expression": "w.inline_is_oa",
    },
    {
        "category": "work_type",
        "inline_property": "inline_work_type",
        "inline_expression": "w.inline_work_type",
    },
    {
        "category": "oa_status",
        "inline_property": "inline_oa_status",
        "inline_expression": "w.inline_oa_status",
    },
    {
        "category": "license",
        "inline_property": "inline_license",
        "inline_expression": "w.inline_license",
    },
]

def run_scalar(session, query: str, key: str) -> int:
    record = session.run(query).single()

    if record is None:
        raise RuntimeError(f"Query returned no record:\n{query}")

    return int(record[key])


def verify_category(session, item: dict) -> dict:
    category = item["category"]
    inline_property = item["inline_property"]
    inline_expression = item["inline_expression"]

    inline_count_query = f"""
    MATCH (w:Work)
    WHERE w.{inline_property} IS NOT NULL
    RETURN count(w) AS count
    """

    normalized_count_query = """
    MATCH (:Work)-[:HAS_METADATA_VALUE]->(
        m:MetadataValue {category: $category}
    )
    RETURN count(*) AS count
    """

    missing_query = f"""
    MATCH (w:Work)
    WHERE w.{inline_property} IS NOT NULL
      AND NOT EXISTS {{
        MATCH (w)-[:HAS_METADATA_VALUE]->(
            m:MetadataValue {{category: $category}}
        )
        WHERE m.value = {inline_expression}
      }}
    RETURN count(w) AS count
    """

    extra_query = f"""
    MATCH (w:Work)-[:HAS_METADATA_VALUE]->(
        m:MetadataValue {{category: $category}}
    )
    WHERE w.{inline_property} IS NULL
       OR m.value <> {inline_expression}
    RETURN count(*) AS count
    """

    duplicate_query = """
    MATCH (w:Work)-[r:HAS_METADATA_VALUE]->(
        m:MetadataValue {category: $category}
    )
    WITH w, m, count(r) AS relationship_count
    WHERE relationship_count > 1
    RETURN coalesce(
        sum(relationship_count - 1),
        0
    ) AS count
    """

    inline_assignments = run_scalar(
        session,
        inline_count_query,
        "count",
    )

    normalized_assignments = int(
        session.run(
            normalized_count_query,
            category=category,
        ).single()["count"]
    )

    missing_assignments = int(
        session.run(
            missing_query,
            category=category,
        ).single()["count"]
    )

    extra_or_mismatched_assignments = int(
        session.run(
            extra_query,
            category=category,
        ).single()["count"]
    )

    duplicate_assignments = int(
        session.run(
            duplicate_query,
            category=category,
        ).single()["count"]
    )

    reconstructed_assignments = (
        inline_assignments - missing_assignments
    )

    reconstruction_ratio = (
        reconstructed_assignments / inline_assignments
        if inline_assignments
        else 1.0
    )

    passed = (
        inline_assignments == normalized_assignments
        and missing_assignments == 0
        and extra_or_mismatched_assignments == 0
        and duplicate_assignments == 0
    )

    return {
        "category": category,
        "inline_property": inline_property,
        "inline_assignments": inline_assignments,
        "normalized_assignments": normalized_assignments,
        "reconstructed_assignments": reconstructed_assignments,
        "missing_assignments": missing_assignments,
        "extra_or_mismatched_assignments": (
            extra_or_mismatched_assignments
        ),
        "duplicate_assignments": duplicate_assignments,
        "reconstruction_ratio": f"{reconstruction_ratio:.6f}",
        "verification_passed": passed,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("No rows were supplied for CSV output.")

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )

    try:
        driver.verify_connectivity()

        with driver.session() as session:
            category_rows = [
                verify_category(session, item)
                for item in CATEGORIES
            ]

        total_inline = sum(
            row["inline_assignments"] for row in category_rows
        )
        total_normalized = sum(
            row["normalized_assignments"] for row in category_rows
        )
        total_reconstructed = sum(
            row["reconstructed_assignments"]
            for row in category_rows
        )
        total_missing = sum(
            row["missing_assignments"] for row in category_rows
        )
        total_extra_or_mismatched = sum(
            row["extra_or_mismatched_assignments"]
            for row in category_rows
        )
        total_duplicates = sum(
            row["duplicate_assignments"] for row in category_rows
        )

        reconstruction_ratio = (
            total_reconstructed / total_inline
            if total_inline
            else 1.0
        )

        verification_passed = (
            total_inline == total_normalized
            and total_missing == 0
            and total_extra_or_mismatched == 0
            and total_duplicates == 0
            and all(
                row["verification_passed"]
                for row in category_rows
            )
        )

        summary_rows = [
            {
                "declared_metadata_categories": len(CATEGORIES),
                "inline_assignments": total_inline,
                "normalized_assignments": total_normalized,
                "reconstructed_assignments": total_reconstructed,
                "missing_assignments": total_missing,
                "extra_or_mismatched_assignments": (
                    total_extra_or_mismatched
                ),
                "duplicate_assignments": total_duplicates,
                "reconstruction_ratio": (
                    f"{reconstruction_ratio:.6f}"
                ),
                "verification_passed": verification_passed,
            }
        ]

        write_csv(CATEGORY_FILE, category_rows)
        write_csv(SUMMARY_FILE, summary_rows)

        print("\nAtomic reconstruction verification")
        print("----------------------------------")

        for row in category_rows:
            print(
                f"{row['category']}: "
                f"inline={row['inline_assignments']}, "
                f"normalized={row['normalized_assignments']}, "
                f"missing={row['missing_assignments']}, "
                f"extra/mismatched="
                f"{row['extra_or_mismatched_assignments']}, "
                f"duplicates={row['duplicate_assignments']}, "
                f"passed={row['verification_passed']}"
            )

        print("\nOverall summary")
        print(f"Inline assignments: {total_inline}")
        print(f"Normalized assignments: {total_normalized}")
        print(f"Reconstructed assignments: {total_reconstructed}")
        print(f"Missing assignments: {total_missing}")
        print(
            "Extra or mismatched assignments: "
            f"{total_extra_or_mismatched}"
        )
        print(f"Duplicate assignments: {total_duplicates}")
        print(
            "Reconstruction ratio: "
            f"{reconstruction_ratio:.6f}"
        )
        print(f"Verification passed: {verification_passed}")
        print(f"\nSummary saved to: {SUMMARY_FILE}")
        print(f"Category details saved to: {CATEGORY_FILE}")

        if not verification_passed:
            raise SystemExit(
                "Atomic reconstruction verification failed."
            )

    finally:
        driver.close()


if __name__ == "__main__":
    main()