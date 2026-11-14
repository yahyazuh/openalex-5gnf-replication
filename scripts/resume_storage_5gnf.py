
"""Safely recover an interrupted 5GNF storage comparison import.

Original database (read only): localhost:7687
Incomplete 5GNF database:     localhost:7691

The script compares relationships in small groups of Work nodes
and inserts only missing relationship occurrences.

It can be rerun after interruption.
"""

import os
from collections import Counter
from neo4j import GraphDatabase

AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD", "neo4jPass123"))
SOURCE_URI = "bolt://localhost:7687"
TARGET_URI = "bolt://localhost:7691"

WORK_BATCH = 100
WRITE_BATCH = 1000

RELATIONSHIPS = {
    "HAS_CONCEPT": {
        "label": "Concept",
        "id": "concept_id",
        "property": "score",
    },
    "PUBLISHED_IN": {
        "label": "Source",
        "id": "source_id",
        "property": None,
    },
    "HAS_METADATA_VALUE": {
        "label": "MetadataValue",
        "id": "metadata_id",
        "property": "category",
    },
}


def chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def relationship_query(rel_type, spec):
    detail = (
        f"r.{spec['property']} AS detail"
        if spec["property"] else
        "null AS detail"
    )

    return f"""
    MATCH (w:Work)-[r:{rel_type}]->(t:{spec['label']})
    WHERE w.work_id IN $work_ids
    RETURN w.work_id AS source_id,
           t.{spec['id']} AS target_id,
           {detail}
    """


def read_relationships(driver, query, work_ids):
    with driver.session(
        database="neo4j",
        default_access_mode="READ"
    ) as session:
        return Counter(
            (
                row["source_id"],
                row["target_id"],
                row["detail"],
            )
            for row in session.run(query, work_ids=work_ids)
        )


def insert_missing(driver, rel_type, spec, missing):
    detail = (
        f" {{{spec['property']}: row.detail}}"
        if spec["property"] else
        ""
    )

    query = f"""
    UNWIND $rows AS row
    MATCH (w:Work {{work_id: row.source_id}})
    MATCH (t:{spec['label']} {{
        {spec['id']}: row.target_id
    }})
    CREATE (w)-[:{rel_type}{detail}]->(t)
    """

    rows = []

    for (source_id, target_id, value), count in missing.items():
        for _ in range(count):
            rows.append({
                "source_id": source_id,
                "target_id": target_id,
                "detail": value,
            })

    with driver.session(database="neo4j") as session:
        for batch in chunks(rows, WRITE_BATCH):
            session.execute_write(
                lambda tx, data=batch:
                    tx.run(query, rows=data).consume()
            )

    return len(rows)


def main():
    with GraphDatabase.driver(SOURCE_URI, auth=AUTH) as source:
        with GraphDatabase.driver(TARGET_URI, auth=AUTH) as target:

            source.verify_connectivity()
            target.verify_connectivity()

            with source.session(
                database="neo4j",
                default_access_mode="READ"
            ) as session:
                work_ids = [
                    row["work_id"]
                    for row in session.run(
                        """
                        MATCH (w:Work)
                        RETURN w.work_id AS work_id
                        ORDER BY work_id
                        """
                    )
                ]

            with target.session(database="neo4j") as session:
                target_works = session.run(
                    "MATCH (w:Work) RETURN count(w) AS n"
                ).single()["n"]

            if len(work_ids) != 98783 or target_works != len(work_ids):
                raise RuntimeError(
                    "Work node counts do not match. "
                    "Recovery aborted."
                )

            print(
                f"Verified {len(work_ids):,} Work nodes",
                flush=True
            )

            for rel_type, spec in RELATIONSHIPS.items():

                print(f"\nRecovering {rel_type}", flush=True)

                query = relationship_query(rel_type, spec)
                inserted = 0

                for number, work_batch in enumerate(
                    chunks(work_ids, WORK_BATCH), start=1
                ):
                    original = read_relationships(
                        source, query, work_batch
                    )
                    existing = read_relationships(
                        target, query, work_batch
                    )

                    unexpected = existing - original

                    if unexpected:
                        raise RuntimeError(
                            f"Unexpected target relationships "
                            f"found in {rel_type}. "
                            f"Recovery stopped."
                        )

                    missing = original - existing

                    if missing:
                        inserted += insert_missing(
                            target, rel_type, spec, missing
                        )

                    if number % 100 == 0:
                        print(
                            f"  Processed {number * WORK_BATCH:,} "
                            f"Work nodes; inserted "
                            f"{inserted:,} relationships",
                            flush=True
                        )

                with target.session(database="neo4j") as session:
                    count = session.run(
                        f"MATCH ()-[r:{rel_type}]->() "
                        "RETURN count(r) AS n"
                    ).single()["n"]

                print(
                    f"{rel_type}: inserted {inserted:,}; "
                    f"final count {count:,}",
                    flush=True
                )

            print(
                "\nRecovery completed. "
                "All relationship groups were compared.",
                flush=True
            )


if __name__ == "__main__":
    main()
