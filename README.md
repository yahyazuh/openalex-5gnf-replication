# OpenAlex 5GNF Replication Materials

This repository contains replication materials for the IEEE Access paper:

**A Fifth Graph Normal Form for Property Graph Schemas: Formal Foundations, Dependency-Preserving Decomposition, and OpenAlex-Based Evaluation**

## Important Note

The repository does not include the full `openalex_works_100k.jsonl` file used in the paper experiment because of file size and repository practicality.

Instead, it includes:

* scripts for regenerating the OpenAlex dataset;
* a 1,000-record OpenAlex sample for inspection and testing;
* Cypher files for Neo4j constraints, indexes, and benchmark queries;
* raw paired timing measurements;
* statistical query-performance summaries;
* scripts for constructing and evaluating the 5GNF and inline-property representations;
* supplementary Northwind structural-validation materials.

The repository supports reproduction and inspection of the experiment, but it is not a complete dump of the full OpenAlex dataset.

## Purpose

The materials support reproduction of the OpenAlex-based evaluation of Fifth Graph Normal Form (5GNF) for property graph schemas.

The main experiment evaluates:

* reusable metadata representation;
* metadata reuse;
* lossless reconstruction;
* logical update effort;
* indexed metadata-filtering query behavior.

The 5GNF representation uses reusable `MetadataValue` nodes connected to `Work` nodes through `HAS_METADATA_VALUE` relationships.

The repository also includes a smaller Northwind structural validation. This supplementary experiment evaluates metadata externalization and lossless reconstruction on a transactional-style graph. It is not used for query-performance benchmarking.

## OpenAlex Dataset

The full OpenAlex experiment used:

* source file: `openalex_works_100k.jsonl`;
* raw OpenAlex records: 100,000;
* unique `Work` nodes: 98,783;
* collapsed duplicate work rows: 1,217;
* total nodes: 139,930;
* total relationships: 2,095,128;
* metadata assignments: 442,537;
* reusable `MetadataValue` nodes: 57.

The full JSONL file is not included. A smaller sample is provided in:

```text
data_sample/openalex_works_sample_1k.jsonl
```

The full source file can be regenerated with:

```bash
python scripts/download_openalex_100k.py
```

## Paired Query-Performance Benchmark

The final query-performance experiment is executed with:

```bash
python scripts/run_paired_query_performance.py
```

For each of the five metadata-filtering predicates, the script:

* performs one discarded warm-up execution for each representation;
* records 30 paired measured executions;
* uses 15 inline-first and 15 5GNF-first execution blocks;
* randomizes the balanced execution-block sequence;
* verifies equivalent result counts;
* reports medians and bootstrap 95% confidence intervals;
* applies a two-sided Wilcoxon signed-rank test;
* uses a significance level of `alpha = 0.05`;
* reports paired rank-biserial correlation as the effect size;
* retains means as supplementary descriptive statistics.

The evaluated predicates are:

* `language=en`;
* `is_oa=True`;
* `work_type=article`;
* `oa_status=gold`;
* `license=cc-by`.

The raw paired measurements are stored in:

```text
experiment_results/paired_query_performance_raw_runs.csv
```

The statistical summary is stored in:

```text
experiment_results/paired_query_performance_statistical_summary.csv
```

## Supplementary Northwind Structural Validation

The Northwind validation is not used for query-performance benchmarking. Its purpose is to evaluate whether reusable metadata can be externalized into canonical metadata-value structures and reconstructed without loss.

Input files are stored in:

```text
data_sample/northwind/
```

The validation script is:

```text
scripts/northwind/run_northwind_structural_metrics.py
```

Recorded results are stored in:

```text
northwind_results/
```

## Installation

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

The required packages are:

* `neo4j`;
* `pandas`;
* `scipy`.

## Reproducibility Instructions

Detailed setup, loading, execution, output, and interpretation instructions are provided in:

```text
REPRODUCIBILITY.md
```

## Interpretation Limits

The timing results are specific to the evaluated OpenAlex dataset, Neo4j environment, indexes, hardware, predicates, and paired execution protocol.

They do not establish that 5GNF is universally faster than inline-property representations. The strongest supported empirical results remain metadata reuse, lossless reconstruction, and logical update-effort reduction.
