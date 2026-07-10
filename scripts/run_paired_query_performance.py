import os
import random
import time
import statistics

import numpy as np
import pandas as pd
from neo4j import GraphDatabase
from scipy.stats import rankdata, wilcoxon


OUTPUT_DIR = "experiment_results"
MEASURED_RUNS = 30
BOOTSTRAP_SAMPLES = 10_000
RANDOM_SEED = 20260710
ALPHA = 0.05

os.makedirs(OUTPUT_DIR, exist_ok=True)

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "neo4jPass123"),
    ),
)

query_pairs = {
    "language_en": {
        "inline": (
            'MATCH (w:Work {inline_language:"en"}) '
            "RETURN count(w) AS c"
        ),
        "5gnf": (
            'MATCH (:MetadataValue {category:"language", value:"en"})'
            "<-[:HAS_METADATA_VALUE]-(w:Work) "
            "RETURN count(w) AS c"
        ),
    },
    "is_oa_true": {
        "inline": (
            'MATCH (w:Work {inline_is_oa:"True"}) '
            "RETURN count(w) AS c"
        ),
        "5gnf": (
            'MATCH (:MetadataValue {category:"is_oa", value:"True"})'
            "<-[:HAS_METADATA_VALUE]-(w:Work) "
            "RETURN count(w) AS c"
        ),
    },
    "work_type_article": {
        "inline": (
            'MATCH (w:Work {inline_work_type:"article"}) '
            "RETURN count(w) AS c"
        ),
        "5gnf": (
            'MATCH (:MetadataValue {category:"work_type", value:"article"})'
            "<-[:HAS_METADATA_VALUE]-(w:Work) "
            "RETURN count(w) AS c"
        ),
    },
    "oa_status_gold": {
        "inline": (
            'MATCH (w:Work {inline_oa_status:"gold"}) '
            "RETURN count(w) AS c"
        ),
        "5gnf": (
            'MATCH (:MetadataValue {category:"oa_status", value:"gold"})'
            "<-[:HAS_METADATA_VALUE]-(w:Work) "
            "RETURN count(w) AS c"
        ),
    },
    "license_cc_by": {
        "inline": (
            'MATCH (w:Work {inline_license:"cc-by"}) '
            "RETURN count(w) AS c"
        ),
        "5gnf": (
            'MATCH (:MetadataValue {category:"license", value:"cc-by"})'
            "<-[:HAS_METADATA_VALUE]-(w:Work) "
            "RETURN count(w) AS c"
        ),
    },
}


def execute_timed(session, query):
    start = time.perf_counter()
    record = session.run(query).single()
    elapsed_ms = (time.perf_counter() - start) * 1000

    if record is None:
        raise RuntimeError("Query returned no result record.")

    return elapsed_ms, int(record["c"])


def bootstrap_median_ci(values, confidence_level=0.95):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(RANDOM_SEED)

    bootstrap_medians = np.empty(BOOTSTRAP_SAMPLES)

    for i in range(BOOTSTRAP_SAMPLES):
        sample = rng.choice(values, size=len(values), replace=True)
        bootstrap_medians[i] = np.median(sample)

    alpha_tail = (1.0 - confidence_level) / 2.0
    lower = np.quantile(bootstrap_medians, alpha_tail)
    upper = np.quantile(bootstrap_medians, 1.0 - alpha_tail)

    return float(lower), float(upper)


def matched_rank_biserial(inline_times, gnf_times):
    """
    Positive values indicate lower execution times for 5GNF.
    Negative values indicate lower execution times for inline properties.
    """
    differences = np.asarray(inline_times) - np.asarray(gnf_times)
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


def interpret_result(p_value, effect_size, inline_median, gnf_median):
    if p_value >= ALPHA:
        return "No statistically significant difference"

    if gnf_median < inline_median:
        if effect_size >= 0.5:
            magnitude = "large"
        elif effect_size >= 0.3:
            magnitude = "moderate"
        elif effect_size >= 0.1:
            magnitude = "small"
        else:
            magnitude = "negligible"

        return f"5GNF faster; {magnitude} effect"

    if inline_median < gnf_median:
        absolute_effect = abs(effect_size)

        if absolute_effect >= 0.5:
            magnitude = "large"
        elif absolute_effect >= 0.3:
            magnitude = "moderate"
        elif absolute_effect >= 0.1:
            magnitude = "small"
        else:
            magnitude = "negligible"

        return f"Inline faster; {magnitude} effect"

    return "Statistically significant but equal medians"


raw_rows = []
summary_rows = []

random.seed(RANDOM_SEED)

try:
    with driver.session() as session:
        for query_name, pair in query_pairs.items():
            print(f"\nBenchmarking {query_name}...")

            # One discarded warm-up execution for each representation.
            warmup_inline = session.run(pair["inline"]).single()
            warmup_5gnf = session.run(pair["5gnf"]).single()

            if warmup_inline is None or warmup_5gnf is None:
                raise RuntimeError(
                    f"Warm-up query failed for {query_name}."
                )

            warmup_inline_count = int(warmup_inline["c"])
            warmup_5gnf_count = int(warmup_5gnf["c"])

            if warmup_inline_count != warmup_5gnf_count:
                raise RuntimeError(
                    f"Result-count mismatch during warm-up for "
                    f"{query_name}: inline={warmup_inline_count}, "
                    f"5GNF={warmup_5gnf_count}"
                )

            inline_times = []
            gnf_times = []

            execution_orders = (
                [["inline", "5gnf"]] * (MEASURED_RUNS // 2)
                + [["5gnf", "inline"]] * (MEASURED_RUNS // 2)
            )

            random.shuffle(execution_orders)

            for run_number, execution_order in enumerate(
                execution_orders,
                start=1,
            ):



                run_results = {}

                for representation in execution_order:
                    elapsed_ms, result_count = execute_timed(
                        session,
                        pair[representation],
                    )

                    run_results[representation] = {
                        "elapsed_ms": elapsed_ms,
                        "result_count": result_count,
                    }

                inline_count = run_results["inline"]["result_count"]
                gnf_count = run_results["5gnf"]["result_count"]

                if inline_count != gnf_count:
                    raise RuntimeError(
                        f"Result-count mismatch for {query_name}, "
                        f"run {run_number}: inline={inline_count}, "
                        f"5GNF={gnf_count}"
                    )

                inline_ms = run_results["inline"]["elapsed_ms"]
                gnf_ms = run_results["5gnf"]["elapsed_ms"]

                inline_times.append(inline_ms)
                gnf_times.append(gnf_ms)

                raw_rows.append(
                    {
                        "query": query_name,
                        "run": run_number,
                        "first_executed": execution_order[0],
                        "inline_ms": round(inline_ms, 6),
                        "5gnf_ms": round(gnf_ms, 6),
                        "paired_difference_ms": round(
                            inline_ms - gnf_ms,
                            6,
                        ),
                        "result_count": inline_count,
                    }
                )

            inline_median = statistics.median(inline_times)
            gnf_median = statistics.median(gnf_times)

            inline_ci_lower, inline_ci_upper = bootstrap_median_ci(
                inline_times
            )
            gnf_ci_lower, gnf_ci_upper = bootstrap_median_ci(gnf_times)

            differences = np.asarray(inline_times) - np.asarray(gnf_times)

            if np.all(differences == 0):
                wilcoxon_statistic = 0.0
                p_value = 1.0
            else:
                test_result = wilcoxon(
                    inline_times,
                    gnf_times,
                    alternative="two-sided",
                    zero_method="wilcox",
                    method="auto",
                )
                wilcoxon_statistic = float(test_result.statistic)
                p_value = float(test_result.pvalue)

            effect_size = matched_rank_biserial(
                inline_times,
                gnf_times,
            )

            median_speedup = (
                inline_median / gnf_median
                if gnf_median != 0
                else float("nan")
            )

            interpretation = interpret_result(
                p_value,
                effect_size,
                inline_median,
                gnf_median,
            )

            summary_rows.append(
                {
                    "query": query_name,
                    "runs": MEASURED_RUNS,
                    "result_count": inline_count,
                    "inline_mean_ms": round(
                        statistics.mean(inline_times),
                        6,
                    ),
                    "5gnf_mean_ms": round(
                        statistics.mean(gnf_times),
                        6,
                    ),
                    "inline_median_ms": round(inline_median, 6),
                    "5gnf_median_ms": round(gnf_median, 6),
                    "inline_median_ci95_lower_ms": round(
                        inline_ci_lower,
                        6,
                    ),
                    "inline_median_ci95_upper_ms": round(
                        inline_ci_upper,
                        6,
                    ),
                    "5gnf_median_ci95_lower_ms": round(
                        gnf_ci_lower,
                        6,
                    ),
                    "5gnf_median_ci95_upper_ms": round(
                        gnf_ci_upper,
                        6,
                    ),
                    "median_speedup_inline_over_5gnf": round(
                        median_speedup,
                        6,
                    ),
                    "wilcoxon_statistic": round(
                        wilcoxon_statistic,
                        6,
                    ),
                    "p_value": round(p_value, 10),
                    "alpha": ALPHA,
                    "rank_biserial_effect_size": round(
                        effect_size,
                        6,
                    ),
                    "interpretation": interpretation,
                }
            )

finally:
    driver.close()


raw_dataframe = pd.DataFrame(raw_rows)
summary_dataframe = pd.DataFrame(summary_rows)

raw_output = os.path.join(
    OUTPUT_DIR,
    "paired_query_performance_raw_runs.csv",
)
summary_output = os.path.join(
    OUTPUT_DIR,
    "paired_query_performance_statistical_summary.csv",
)

raw_dataframe.to_csv(raw_output, index=False)
summary_dataframe.to_csv(summary_output, index=False)

print("\nStatistical summary:")
print(summary_dataframe.to_string(index=False))

print(f"\nRaw measurements saved to: {raw_output}")
print(f"Statistical summary saved to: {summary_output}")