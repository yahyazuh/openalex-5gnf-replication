import os
import time
import pandas as pd
from neo4j import GraphDatabase

os.makedirs("experiment_results", exist_ok=True)

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4jPass123")
)

queries = {
    "language_en": 'MATCH (:MetadataValue {category:"language", value:"en"})<-[:HAS_METADATA_VALUE]-(w:Work) RETURN count(w) AS c',
    "is_oa_true": 'MATCH (:MetadataValue {category:"is_oa", value:"True"})<-[:HAS_METADATA_VALUE]-(w:Work) RETURN count(w) AS c',
    "work_type_article": 'MATCH (:MetadataValue {category:"work_type", value:"article"})<-[:HAS_METADATA_VALUE]-(w:Work) RETURN count(w) AS c',
    "oa_status_gold": 'MATCH (:MetadataValue {category:"oa_status", value:"gold"})<-[:HAS_METADATA_VALUE]-(w:Work) RETURN count(w) AS c',
    "license_cc_by": 'MATCH (:MetadataValue {category:"license", value:"cc-by"})<-[:HAS_METADATA_VALUE]-(w:Work) RETURN count(w) AS c'
}

rows = []

with driver.session() as session:
    for q in queries.values():
        session.run(q).consume()

    for name, q in queries.items():
        times = []
        count = None

        for i in range(10):
            start = time.perf_counter()
            record = session.run(q).single()
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
            count = record["c"]

        rows.append({
            "query": name,
            "result_count": count,
            "runs": 10,
            "avg_ms": round(sum(times) / len(times), 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3)
        })

driver.close()

out = pd.DataFrame(rows)
out.to_csv("experiment_results/query_performance_metadata_filtering.csv", index=False)
print(out.to_string(index=False))