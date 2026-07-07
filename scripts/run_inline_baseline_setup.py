import os
from neo4j import GraphDatabase

os.makedirs("baseline_inline_results", exist_ok=True)

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4jPass123")
)

queries = [
    """
    MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category:"language"})
    SET w.inline_language = m.value
    """,
    """
    MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category:"is_oa"})
    SET w.inline_is_oa = m.value
    """,
    """
    MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category:"work_type"})
    SET w.inline_work_type = m.value
    """,
    """
    MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category:"oa_status"})
    SET w.inline_oa_status = m.value
    """,
    """
    MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category:"license"})
    SET w.inline_license = m.value
    """
]

with driver.session() as session:
    for q in queries:
        session.run(q).consume()

driver.close()
print("inline_baseline_properties_created")