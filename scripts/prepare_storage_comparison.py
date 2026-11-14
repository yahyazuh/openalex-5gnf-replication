
"""Build isolated databases for the IEEE Access storage comparison.

Source (read only): bolt://localhost:7687
Inline target:      bolt://localhost:7690
5GNF target:        bolt://localhost:7691

Requires: neo4j Python driver 5.x
"""

import os
from neo4j import GraphDatabase

PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jPass123")
AUTH = ("neo4j", PASSWORD)
BATCH_SIZE = 1000

SOURCE = "bolt://localhost:7687"
TARGETS = {
    "inline": "bolt://localhost:7690",
    "5gnf": "bolt://localhost:7691",
}

ATOMIC_PROPERTIES = {
    "inline_language",
    "inline_is_oa",
    "inline_work_type",
    "inline_oa_status",
    "inline_license",
}


def write_batch(tx, query, rows):
    tx.run(query, rows=rows).consume()


def transfer(source, target, source_query, target_query, label):
    total = 0

    with source.session(database="neo4j") as reader:
        with target.session(database="neo4j") as writer:
            result = reader.run(source_query)
            batch = []

            for record in result:
                batch.append(dict(record))

                if len(batch) == BATCH_SIZE:
                    writer.execute_write(
                        write_batch, target_query, batch
                    )
                    total += len(batch)
                    batch = []

                    if total % 100000 == 0:
                        print(f"  {label}: {total:,}", flush=True)

            if batch:
                writer.execute_write(
                    write_batch, target_query, batch
                )
                total += len(batch)

    print(f"  {label}: {total:,} complete", flush=True)
    return total


def create_schema(target, mode):
    constraints = [
        "CREATE CONSTRAINT work_id_unique IF NOT EXISTS "
        "FOR (n:Work) REQUIRE n.work_id IS UNIQUE",

        "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS "
        "FOR (n:Concept) REQUIRE n.concept_id IS UNIQUE",

        "CREATE CONSTRAINT source_id_unique IF NOT EXISTS "
        "FOR (n:Source) REQUIRE n.source_id IS UNIQUE",
    ]

    if mode == "inline":
        for name in sorted(ATOMIC_PROPERTIES):
            constraints.append(
                f"CREATE INDEX work_{name} IF NOT EXISTS "
                f"FOR (n:Work) ON (n.{name})"
            )
    else:
        constraints.extend([
            "CREATE CONSTRAINT metadata_id_unique IF NOT EXISTS "
            "FOR (n:MetadataValue) "
            "REQUIRE n.metadata_id IS UNIQUE",

            "CREATE INDEX metadata_category_value IF NOT EXISTS "
            "FOR (n:MetadataValue) "
            "ON (n.category, n.value)",
        ])

    with target.session(database="neo4j") as session:
        for query in constraints:
            session.run(query).consume()

        session.run("CALL db.awaitIndexes(300)").consume()


def copy_nodes(source, target, mode):
    source_query = """
    MATCH (n:Work)
    RETURN properties(n) AS props
    """

    target_query = """
    UNWIND $rows AS row
    CREATE (n:Work)
    SET n += row.props
    """

    def work_rows():
        with source.session(database="neo4j") as session:
            for record in session.run(source_query):
                props = dict(record["props"])

                # Exclude the separate structured-license experiment.
                props.pop("inline_license_authority", None)

                if mode == "5gnf":
                    for key in ATOMIC_PROPERTIES:
                        props.pop(key, None)

                yield {"props": props}

    batch = []
    total = 0

    with target.session(database="neo4j") as writer:
        for row in work_rows():
            batch.append(row)

            if len(batch) == BATCH_SIZE:
                writer.execute_write(
                    write_batch, target_query, batch
                )
                total += len(batch)
                batch = []

        if batch:
            writer.execute_write(
                write_batch, target_query, batch
            )
            total += len(batch)

    print(f"  Work nodes: {total:,}", flush=True)

    for label in ("Concept", "Source"):
        transfer(
            source,
            target,
            f"MATCH (n:{label}) "
            "RETURN properties(n) AS props",
            f"UNWIND $rows AS row "
            f"CREATE (n:{label}) SET n += row.props",
            f"{label} nodes",
        )

    if mode == "5gnf":
        transfer(
            source,
            target,
            "MATCH (n:MetadataValue) "
            "RETURN properties(n) AS props",
            "UNWIND $rows AS row "
            "CREATE (n:MetadataValue) SET n += row.props",
            "MetadataValue nodes",
        )


def copy_relationships(source, target, mode):
    transfer(
        source,
        target,
        """
        MATCH (w:Work)-[r:HAS_CONCEPT]->(c:Concept)
        RETURN w.work_id AS source_id,
               c.concept_id AS target_id,
               r.score AS score
        """,
        """
        UNWIND $rows AS row
        MATCH (w:Work {work_id: row.source_id})
        MATCH (c:Concept {concept_id: row.target_id})
        CREATE (w)-[:HAS_CONCEPT {score: row.score}]->(c)
        """,
        "HAS_CONCEPT",
    )

    transfer(
        source,
        target,
        """
        MATCH (w:Work)-[:PUBLISHED_IN]->(s:Source)
        RETURN w.work_id AS source_id,
               s.source_id AS target_id
        """,
        """
        UNWIND $rows AS row
        MATCH (w:Work {work_id: row.source_id})
        MATCH (s:Source {source_id: row.target_id})
        CREATE (w)-[:PUBLISHED_IN]->(s)
        """,
        "PUBLISHED_IN",
    )

    if mode == "5gnf":
        transfer(
            source,
            target,
            """
            MATCH (w:Work)-[r:HAS_METADATA_VALUE]->
                  (m:MetadataValue)
            RETURN w.work_id AS source_id,
                   m.metadata_id AS target_id,
                   r.category AS category
            """,
            """
            UNWIND $rows AS row
            MATCH (w:Work {work_id: row.source_id})
            MATCH (m:MetadataValue {
                metadata_id: row.target_id
            })
            CREATE (w)-[:HAS_METADATA_VALUE {
                category: row.category
            }]->(m)
            """,
            "HAS_METADATA_VALUE",
        )


def main():
    with GraphDatabase.driver(SOURCE, auth=AUTH) as source:
        source.verify_connectivity()

        for mode, uri in TARGETS.items():
            print(f"\nPreparing {mode} database", flush=True)

            with GraphDatabase.driver(uri, auth=AUTH) as target:
                target.verify_connectivity()

                with target.session(database="neo4j") as session:
                    count = session.run(
                        "MATCH (n) RETURN count(n) AS total"
                    ).single()["total"]

                if count != 0:
                    raise RuntimeError(
                        f"{mode} target is not empty: "
                        f"{count:,} nodes. Aborting."
                    )

                create_schema(target, mode)
                copy_nodes(source, target, mode)
                copy_relationships(source, target, mode)

                with target.session(database="neo4j") as session:
                    result = session.run(
                        """
                        MATCH (n)
                        WITH count(n) AS nodes
                        MATCH ()-[r]->()
                        RETURN nodes,
                               count(r) AS relationships
                        """
                    ).single()

                    print(
                        f"{mode} complete: "
                        f"{result['nodes']:,} nodes, "
                        f"{result['relationships']:,} "
                        "relationships",
                        flush=True,
                    )

    print("\nStorage comparison imports complete.")


if __name__ == "__main__":
    main()
