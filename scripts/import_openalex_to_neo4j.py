#!/usr/bin/env python3
"""Import the CSV files produced by convert_openalex_jsonl_to_csv.py.

The importer is idempotent: nodes and relationships are matched by the
identifiers used in the experiment. It does not delete existing data.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Callable, Iterator

from neo4j import GraphDatabase


CONSTRAINTS = (
    "CREATE CONSTRAINT work_id_unique IF NOT EXISTS "
    "FOR (w:Work) REQUIRE w.work_id IS UNIQUE",
    "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS "
    "FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE",
    "CREATE CONSTRAINT source_id_unique IF NOT EXISTS "
    "FOR (s:Source) REQUIRE s.source_id IS UNIQUE",
    "CREATE CONSTRAINT metadata_id_unique IF NOT EXISTS "
    "FOR (m:MetadataValue) REQUIRE m.metadata_id IS UNIQUE",
    "CREATE CONSTRAINT license_trait_code_unique IF NOT EXISTS "
    "FOR (l:LicenseTrait) REQUIRE l.licenseCode IS UNIQUE",
)

INDEXES = (
    "CREATE INDEX metadata_category_value IF NOT EXISTS "
    "FOR (m:MetadataValue) ON (m.category, m.value)",
)


def integer(value: str):
    return int(value) if value else None


def floating(value: str):
    return float(value) if value else None


def boolean(value: str):
    if not value:
        return None
    return value.strip().lower() in {"true", "1", "yes"}


def text(value: str):
    return value if value != "" else None


def rows(path: Path, conversions: dict[str, Callable[[str], object]]) -> Iterator[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            yield {
                key: conversions.get(key, text)(value)
                for key, value in row.items()
            }


def batches(items: Iterator[dict], size: int) -> Iterator[list[dict]]:
    batch: list[dict] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def import_file(session, path: Path, query: str, conversions: dict, batch_size: int):
    processed = 0
    for batch in batches(rows(path, conversions), batch_size):
        session.execute_write(
            lambda tx, current=batch: tx.run(query, rows=current).consume()
        )
        processed += len(batch)
        print(f"{path.name}: {processed:,} rows", end="\r", flush=True)
    print(f"{path.name}: {processed:,} rows imported")


IMPORTS = (
    (
        "works.csv",
        """
        UNWIND $rows AS row
        MERGE (w:Work {work_id: row.work_id})
        SET w.openalex_id = row.openalex_id,
            w.doi = row.doi,
            w.title = row.title,
            w.publication_year = row.publication_year,
            w.cited_by_count = row.cited_by_count
        """,
        {"publication_year": integer, "cited_by_count": integer},
    ),
    (
        "concepts.csv",
        """
        UNWIND $rows AS row
        MERGE (c:Concept {concept_id: row.concept_id})
        SET c.openalex_id = row.openalex_id,
            c.display_name = row.display_name,
            c.level = row.level,
            c.score = row.score,
            c.wikidata = row.wikidata
        """,
        {"level": integer, "score": floating},
    ),
    (
        "sources.csv",
        """
        UNWIND $rows AS row
        MERGE (s:Source {source_id: row.source_id})
        SET s.openalex_id = row.openalex_id,
            s.display_name = row.display_name,
            s.type = row.type,
            s.issn_l = row.issn_l,
            s.is_oa = row.is_oa
        """,
        {"is_oa": boolean},
    ),
    (
        "metadata_values.csv",
        """
        UNWIND $rows AS row
        MERGE (m:MetadataValue {metadata_id: row.metadata_id})
        SET m.category = row.category, m.value = row.value
        """,
        {},
    ),
    (
        "work_concepts_edges.csv",
        """
        UNWIND $rows AS row
        MATCH (w:Work {work_id: row.work_id})
        MATCH (c:Concept {concept_id: row.concept_id})
        MERGE (w)-[r:HAS_CONCEPT]->(c)
        SET r.score = row.score
        """,
        {"score": floating},
    ),
    (
        "work_sources_edges.csv",
        """
        UNWIND $rows AS row
        MATCH (w:Work {work_id: row.work_id})
        MATCH (s:Source {source_id: row.source_id})
        MERGE (w)-[:PUBLISHED_IN]->(s)
        """,
        {},
    ),
    (
        "work_metadata_edges.csv",
        """
        UNWIND $rows AS row
        MATCH (w:Work {work_id: row.work_id})
        MATCH (m:MetadataValue {metadata_id: row.metadata_id})
        MERGE (w)-[r:HAS_METADATA_VALUE]->(m)
        SET r.category = row.category
        """,
        {},
    ),
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-dir", type=Path, required=True)
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--batch-size", type=int, default=5_000)
    args = parser.parse_args()
    if not args.password:
        parser.error("set NEO4J_PASSWORD or pass --password")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    return args


def main():
    args = parse_args()
    missing = [name for name, _, _ in IMPORTS if not (args.csv_dir / name).is_file()]
    if missing:
        raise SystemExit("Missing CSV files: " + ", ".join(missing))

    with GraphDatabase.driver(args.uri, auth=(args.user, args.password)) as driver:
        driver.verify_connectivity()
        with driver.session(database=args.database) as session:
            for statement in CONSTRAINTS + INDEXES:
                session.run(statement).consume()
            session.run("CALL db.awaitIndexes(300)").consume()

            for filename, query, conversions in IMPORTS:
                import_file(
                    session,
                    args.csv_dir / filename,
                    query,
                    conversions,
                    args.batch_size,
                )

            counts = session.run(
                """
                MATCH (w:Work) WITH count(w) AS works
                MATCH (c:Concept) WITH works, count(c) AS concepts
                MATCH (s:Source) WITH works, concepts, count(s) AS sources
                MATCH (m:MetadataValue)
                RETURN works, concepts, sources, count(m) AS metadata_values
                """
            ).single()
            print("Import complete:", dict(counts))


if __name__ == "__main__":
    main()
