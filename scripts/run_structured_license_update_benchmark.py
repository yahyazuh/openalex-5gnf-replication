import os
import random
import time
import statistics

import numpy as np
import pandas as pd
from neo4j import GraphDatabase
from scipy.stats import rankdata, wilcoxon

OUTPUT_DIR = "experiment_results/structured_license"
MEASURED_RUNS = 30
BOOTSTRAP_SAMPLES = 10000
RANDOM_SEED = 20260714
ALPHA = 0.05

os.makedirs(OUTPUT_DIR, exist_ok=True)

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "neo4jPass123"),
    ),
)

ORIGINAL_AUTHORITY = "Creative Commons"
TEMP_INLINE_AUTHORITY = "Creative Commons TEMP INLINE"
TEMP_TRAIT_AUTHORITY = "Creative Commons TEMP TRAIT"
TARGET_LICENSE_CODE = "cc-by"

INLINE_UPDATE_QUERY = """
MATCH (w:Work {inline_license: $license_code})
SET w.inline_license_authority = $temporary_authority
RETURN count(w) AS nodes_affected
"""

STRUCTURED_UPDATE_QUERY = """
MATCH (l:LicenseTrait {licenseCode: $license_code})
SET l.licenseAuthority = $temporary_authority
RETURN count(l) AS nodes_affected
"""

INLINE_RESTORE_QUERY = """
MATCH (w:Work {inline_license: $license_code})
SET w.inline_license_authority = $original_authority
RETURN count(w) AS nodes_restored
"""

STRUCTURED_RESTORE_QUERY = """
MATCH (l:LicenseTrait {licenseCode: $license_code})
SET l.licenseAuthority = $original_authority
RETURN count(l) AS nodes_restored
"""

INLINE_VERIFY_QUERY = """
MATCH (w:Work {inline_license: $license_code})
RETURN count(w) AS total,
       count(CASE WHEN w.inline_license_authority = $original_authority THEN 1 END) AS restored
"""

STRUCTURED_VERIFY_QUERY = """
MATCH (l:LicenseTrait {licenseCode: $license_code})
RETURN count(l) AS total,
       count(CASE WHEN l.licenseAuthority = $original_authority THEN 1 END) AS restored
"""

def execute_committed_update(session, query, parameters):
    def work(tx):
        result = tx.run(query, **parameters)
        record = result.single()
        summary = result.consume()
        if record is None:
            raise RuntimeError("Update returned no result record.")
        return record, summary.counters

    start = time.perf_counter()
    record, counters = session.execute_write(work)
    commit_elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "elapsed_ms": commit_elapsed_ms,
        "nodes_affected": int(record["nodes_affected"]),
        "properties_set": int(counters.properties_set),
    }

def restore_and_verify(session, restore_query, verify_query, expected_total):
    restore_parameters = {
        "license_code": TARGET_LICENSE_CODE,
        "original_authority": ORIGINAL_AUTHORITY,
    }

    restore_record = session.run(
        restore_query,
        **restore_parameters,
    ).single()

    if restore_record is None:
        raise RuntimeError("Restoration returned no result record.")

    nodes_restored = int(restore_record["nodes_restored"])

    verify_record = session.run(
        verify_query,
        **restore_parameters,
    ).single()

    if verify_record is None:
        raise RuntimeError("Restoration verification returned no record.")

    total = int(verify_record["total"])
    restored = int(verify_record["restored"])

    if total != expected_total or restored != expected_total:
        raise RuntimeError(
            f"Restoration verification failed: total={total}, "
            f"restored={restored}, expected={expected_total}"
        )

    return nodes_restored

def bootstrap_median_ci(values, confidence_level=0.95):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap_medians = np.empty(BOOTSTRAP_SAMPLES)

    for i in range(BOOTSTRAP_SAMPLES):
        sample = rng.choice(values, size=len(values), replace=True)
        bootstrap_medians[i] = np.median(sample)

    alpha_tail = (1.0 - confidence_level) / 2.0
    return (
        float(np.quantile(bootstrap_medians, alpha_tail)),
        float(np.quantile(bootstrap_medians, 1.0 - alpha_tail)),
    )

def matched_rank_biserial(inline_times, structured_times):
    differences = np.asarray(inline_times) - np.asarray(structured_times)
    nonzero = differences[differences != 0]

    if len(nonzero) == 0:
        return 0.0

    ranks = rankdata(np.abs(nonzero))
    positive_rank_sum = ranks[nonzero > 0].sum()
    negative_rank_sum = ranks[nonzero < 0].sum()
    total_rank_sum = positive_rank_sum + negative_rank_sum

    return float(
        (positive_rank_sum - negative_rank_sum) / total_rank_sum
    )

def interpret_result(p_value, effect_size, inline_median, structured_median):
    if p_value >= ALPHA:
        return "No statistically significant difference"

    absolute_effect = abs(effect_size)
    if absolute_effect >= 0.5:
        magnitude = "large"
    elif absolute_effect >= 0.3:
        magnitude = "moderate"
    elif absolute_effect >= 0.1:
        magnitude = "small"
    else:
        magnitude = "negligible"

    if structured_median < inline_median:
        return f"Structured faster; {magnitude} effect"
    if inline_median < structured_median:
        return f"Inline faster; {magnitude} effect"
    return "Statistically significant but equal medians"

UPDATE_CONFIG = {
    "inline": {
        "update_query": INLINE_UPDATE_QUERY,
        "restore_query": INLINE_RESTORE_QUERY,
        "verify_query": INLINE_VERIFY_QUERY,
        "temporary_authority": TEMP_INLINE_AUTHORITY,
        "expected_nodes": 34379,
    },
    "structured": {
        "update_query": STRUCTURED_UPDATE_QUERY,
        "restore_query": STRUCTURED_RESTORE_QUERY,
        "verify_query": STRUCTURED_VERIFY_QUERY,
        "temporary_authority": TEMP_TRAIT_AUTHORITY,
        "expected_nodes": 1,
    },
}

def run_update_once(session, representation):
    config = UPDATE_CONFIG[representation]
    parameters = {
        "license_code": TARGET_LICENSE_CODE,
        "temporary_authority": config["temporary_authority"],
    }

    result = execute_committed_update(
        session,
        config["update_query"],
        parameters,
    )

    expected_nodes = config["expected_nodes"]
    if result["nodes_affected"] != expected_nodes:
        raise RuntimeError(
            f"Unexpected nodes affected for {representation}: "
            f"{result['nodes_affected']}, expected {expected_nodes}"
        )

    if result["properties_set"] != expected_nodes:
        raise RuntimeError(
            f"Unexpected properties set for {representation}: "
            f"{result['properties_set']}, expected {expected_nodes}"
        )

    nodes_restored = restore_and_verify(
        session,
        config["restore_query"],
        config["verify_query"],
        expected_nodes,
    )

    result["nodes_restored"] = nodes_restored
    return result

raw_rows = []
inline_times = []
structured_times = []

execution_orders = (
    [["inline", "structured"]] * 15
    + [["structured", "inline"]] * 15
)
random.Random(RANDOM_SEED).shuffle(execution_orders)

try:
    with driver.session() as session:
        print("Running discarded warm-ups...")
        run_update_once(session, "inline")
        run_update_once(session, "structured")

        for run_number, execution_order in enumerate(execution_orders, start=1):
            run_results = {}

            for representation in execution_order:
                run_results[representation] = run_update_once(
                    session,
                    representation,
                )

            inline_result = run_results["inline"]
            structured_result = run_results["structured"]
            inline_times.append(inline_result["elapsed_ms"])
            structured_times.append(structured_result["elapsed_ms"])

            raw_rows.append({
                "benchmark": "canonical_definition_update",
                "run": run_number,
                "first_executed": execution_order[0],
                "inline_elapsed_ms": round(inline_result["elapsed_ms"], 6),
                "structured_elapsed_ms": round(structured_result["elapsed_ms"], 6),
                "paired_difference_ms": round(inline_result["elapsed_ms"] - structured_result["elapsed_ms"], 6),
                "inline_nodes_affected": inline_result["nodes_affected"],
                "structured_nodes_affected": structured_result["nodes_affected"],
                "inline_properties_set": inline_result["properties_set"],
                "structured_properties_set": structured_result["properties_set"],
                "inline_nodes_restored": inline_result["nodes_restored"],
                "structured_nodes_restored": structured_result["nodes_restored"],
            })

            print(f"Completed paired run {run_number}/30")
finally:
    driver.close()

inline_median = statistics.median(inline_times)
structured_median = statistics.median(structured_times)
inline_ci_lower, inline_ci_upper = bootstrap_median_ci(inline_times)
structured_ci_lower, structured_ci_upper = bootstrap_median_ci(structured_times)

differences = np.asarray(inline_times) - np.asarray(structured_times)
if np.all(differences == 0):
    wilcoxon_statistic = 0.0
    p_value = 1.0
else:
    test_result = wilcoxon(
        inline_times,
        structured_times,
        alternative="two-sided",
        zero_method="wilcox",
        method="auto",
    )
    wilcoxon_statistic = float(test_result.statistic)
    p_value = float(test_result.pvalue)

effect_size = matched_rank_biserial(inline_times, structured_times)
median_ratio = inline_median / structured_median
interpretation = interpret_result(
    p_value,
    effect_size,
    inline_median,
    structured_median,
)

summary_rows = [{
    "benchmark": "canonical_definition_update",
    "runs": MEASURED_RUNS,
    "inline_mean_ms": round(statistics.mean(inline_times), 6),
    "structured_mean_ms": round(statistics.mean(structured_times), 6),
    "inline_median_ms": round(inline_median, 6),
    "structured_median_ms": round(structured_median, 6),
    "inline_median_ci95_lower_ms": round(inline_ci_lower, 6),
    "inline_median_ci95_upper_ms": round(inline_ci_upper, 6),
    "structured_median_ci95_lower_ms": round(structured_ci_lower, 6),
    "structured_median_ci95_upper_ms": round(structured_ci_upper, 6),
    "median_ratio_inline_over_structured": round(median_ratio, 6),
    "wilcoxon_statistic": round(wilcoxon_statistic, 6),
    "p_value": round(p_value, 10),
    "alpha": ALPHA,
    "rank_biserial_effect_size": round(effect_size, 6),
    "inline_nodes_affected_per_run": 34379,
    "structured_nodes_affected_per_run": 1,
    "interpretation": interpretation,
}]

raw_output = os.path.join(
    OUTPUT_DIR,
    "canonical_definition_update_raw_runs.csv",
)
summary_output = os.path.join(
    OUTPUT_DIR,
    "canonical_definition_update_statistical_summary.csv",
)

pd.DataFrame(raw_rows).to_csv(raw_output, index=False)
pd.DataFrame(summary_rows).to_csv(summary_output, index=False)

print("\nStatistical summary:")
print(pd.DataFrame(summary_rows).to_string(index=False))
print(f"\nRaw measurements saved to: {raw_output}")
print(f"Statistical summary saved to: {summary_output}")
