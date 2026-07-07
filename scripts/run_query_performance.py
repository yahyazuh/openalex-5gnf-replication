import os
import time
import math
import statistics
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

summary_rows = []
raw_rows = []

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

            raw_rows.append({
                "query": name,
                "run": i + 1,
                "elapsed_ms": round(elapsed_ms, 3),
                "result_count": count
            })

        mean_ms = statistics.mean(times)
        median_ms = statistics.median(times)
        sd_ms = statistics.stdev(times)
        ci95_ms = 1.96 * sd_ms / math.sqrt(len(times))

        summary_rows.append({
            "query": name,
            "result_count": count,
            "runs": len(times),
            "mean_ms": round(mean_ms, 3),
            "median_ms": round(median_ms, 3),
            "sd_ms": round(sd_ms, 3),
            "ci95_ms": round(ci95_ms, 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3)
        })

driver.close()

summary = pd.DataFrame(summary_rows)
raw = pd.DataFrame(raw_rows)

summary.to_csv("experiment_results/query_performance_metadata_filtering_summary.csv", index=False)
raw.to_csv("experiment_results/query_performance_metadata_filtering_raw_runs.csv", index=False)

print(summary.to_string(index=False))