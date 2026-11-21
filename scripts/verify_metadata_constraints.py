
"""
5GNF OpenAlex Metadata Constraint Verification

Additional post-submission verification for IEEE Access.

Checks:
1. Cardinality [0,1] per Work and metadata category.
2. Uniqueness of (category, value) pairs.
3. Consistency of metadata identifiers.
4. Consistency of relationship categories.
5. Conflicting metadata across duplicate OpenAlex Work records.

All database queries and source-file operations are read-only.

These tests verify the evaluated database instance.
They do not establish enforcement against arbitrary future updates.
"""

import json
import os
import sys
from collections import defaultdict
from getpass import getpass
from pathlib import Path

from neo4j import GraphDatabase


# --------------------------------------------------
# Configuration
# --------------------------------------------------

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

DATASET = (
    Path(__file__).resolve().parents[2]
    / "openalex_works_100k.jsonl"
)


# --------------------------------------------------
# Neo4j database verification
# --------------------------------------------------

CHECKS = {
    "Cardinality [0,1] per Work and category": """
        MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue)
        WITH w, m.category AS category, count(*) AS n
        WHERE n > 1
        RETURN count(*) AS violations
    """,

    "Unique (category, value) pairs": """
        MATCH (m:MetadataValue)
        WITH m.category AS category, m.value AS value,
             count(*) AS n
        WHERE n > 1
        RETURN count(*) AS violations
    """,

    "Consistent metadata identifiers": """
        MATCH (m:MetadataValue)
        WHERE m.metadata_id IS NULL
           OR m.category IS NULL
           OR m.value IS NULL
           OR m.metadata_id <>
              toLower(
                  m.category + ':' +
                  replace(toString(m.value), ' ', '_')
              )
        RETURN count(*) AS violations
    """,

    "Consistent relationship categories": """
        MATCH (:Work)-[r:HAS_METADATA_VALUE]->(m:MetadataValue)
        WHERE r.category IS NULL
           OR m.category IS NULL
           OR r.category <> m.category
        RETURN count(*) AS violations
    """,
}


def verify_database():
    print()
    print("PART A - Neo4j Database Verification")
    print("=" * 55)

    password = getpass("Neo4j password: ")

    driver = GraphDatabase.driver(
        URI,
        auth=(USER, password)
    )

    try:
        driver.verify_connectivity()

        failures = 0

        with driver.session(database=DATABASE) as session:

            for name, query in CHECKS.items():

                record = session.execute_read(
                    lambda tx, q=query: tx.run(q).single()
                )

                violations = record["violations"]
                status = "PASS" if violations == 0 else "FAIL"

                print(f"{status}: {name}")
                print(f"      Violations: {violations}")

                if violations != 0:
                    failures += 1

        return failures

    finally:
        driver.close()


# --------------------------------------------------
# OpenAlex source-data verification
# --------------------------------------------------

def get_license(work):
    primary = work.get("primary_location") or {}
    best = work.get("best_oa_location") or {}

    return (
        primary.get("license")
        or best.get("license")
        or ""
    )


def normalize_value(value):
    if value is None:
        return ""

    return (
        str(value)
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def verify_source_metadata():
    print()
    print("PART B - OpenAlex Source Metadata Verification")
    print("=" * 55)

    if not DATASET.is_file():
        print(f"FAIL: Dataset not found: {DATASET}")
        return 1

    seen = defaultdict(set)
    work_counts = defaultdict(int)

    records = 0
    skipped = 0

    with DATASET.open("r", encoding="utf-8") as f:

        for line in f:
            records += 1

            try:
                work = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            if not isinstance(work, dict):
                skipped += 1
                continue

            raw_id = work.get("id")

            if not raw_id:
                skipped += 1
                continue

            work_id = str(raw_id).rstrip("/").split("/")[-1]

            if not work_id:
                skipped += 1
                continue

            work_counts[work_id] += 1

            oa = work.get("open_access") or {}

            metadata = {
                "work_type": work.get("type"),
                "language": work.get("language"),
                "oa_status": oa.get("oa_status"),
                "is_oa": oa.get("is_oa"),
                "license": get_license(work),
            }

            for category, value in metadata.items():

                value = normalize_value(value)

                if value:
                    seen[(work_id, category)].add(value)

    conflicts = {
        key: values
        for key, values in seen.items()
        if len(values) > 1
    }

    duplicates = sum(
        count - 1
        for count in work_counts.values()
        if count > 1
    )

    print(f"Total source records: {records}")
    print(f"Unique Work IDs: {len(work_counts)}")
    print(f"Duplicate records: {duplicates}")
    print(f"Skipped records: {skipped}")
    print(f"Conflicting Work/category pairs: {len(conflicts)}")

    for (work_id, category), values in list(conflicts.items())[:10]:
        print(
            f"CONFLICT: {work_id}, {category}: "
            f"{sorted(values)}"
        )

    if conflicts or skipped:
        print("RESULT: FAIL - Source verification issues detected")
        return 1

    print("RESULT: PASS - No conflicting metadata detected")
    return 0


# --------------------------------------------------
# Main execution
# --------------------------------------------------

def main():
    print("=" * 55)
    print("5GNF - OpenAlex Metadata Constraint Verification")
    print("=" * 55)
    print("Additional post-submission verification")
    print("All tests are read-only.")
    print()

    database_failures = verify_database()
    source_failures = verify_source_metadata()

    total_failures = database_failures + source_failures

    print()
    print("=" * 55)
    print("FINAL VERIFICATION SUMMARY")
    print("=" * 55)

    print(f"Neo4j checks: {len(CHECKS)}")
    print("Source-data checks: 1")
    print(f"Failed checks: {total_failures}")

    if total_failures:
        print("FINAL RESULT: FAIL")
        return 1

    print("FINAL RESULT: ALL 5 CHECKS PASSED")
    print()
    print(
        "NOTE: Results establish consistency of the "
        "evaluated instance, not enforcement against "
        "arbitrary future database updates."
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())

    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(2)
