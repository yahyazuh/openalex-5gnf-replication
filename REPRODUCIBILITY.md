# Reproducibility Instructions

This document describes how to reproduce the OpenAlex-based 5GNF experiment and the final indexed paired query-performance benchmark.

## 1. Environment

The reported experiment used:

* Neo4j 5.21.2 Community Edition;
* Docker image `neo4j:5.21`;
* Python 3.12.0;
* Neo4j Python driver 5.28.2;
* pandas 2.3.2;
* SciPy 1.15.2.

Full environment details are provided in:

```text
ENVIRONMENT.md
```

Install the required Python packages with:

```bash
pip install -r requirements.txt
```

Configure the Neo4j connection through:

```text
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
```

## 2. Dataset Preparation

The original experiment used:

```text
openalex_works_100k.jsonl
```

It contained 100,000 raw OpenAlex work records.

The complete file is not included in the repository. A 1,000-record sample is available at:

```text
data_sample/openalex_works_sample_1k.jsonl
```

A new dataset can be downloaded with:

```bash
python scripts/download_openalex_100k.py
```

Because OpenAlex changes over time, a newly downloaded dataset may not reproduce exactly the same records or numerical results.

## 3. CSV Conversion

Convert the JSONL file into Neo4j CSV files with:

```bash
python scripts/convert_openalex_jsonl_to_csv.py
```

The generated files are written to:

```text
neo4j_csv/
```

The original conversion produced:

* 100,000 raw records;
* 98,783 unique `Work` nodes;
* 1,217 collapsed duplicate rows.

## 4. Neo4j Setup

Create the required constraints and indexes using:

```text
cypher/01_constraints.cypher
```

Create the inline-property baseline with:

```bash
python scripts/run_inline_baseline_setup.py
```

Before benchmarking:

* verify that all required indexes are `ONLINE`;
* use the same database instance and dataset for both representations;
* verify that equivalent queries return identical result counts.

## 5. Query Workload

The 5GNF queries are stored in:

```text
cypher/02_5gnf_metadata_queries.cypher
```

The equivalent inline queries are stored in:

```text
cypher/03_inline_baseline_queries.cypher
```

The evaluated predicates are:

* `language=en`;
* `is_oa=True`;
* `work_type=article`;
* `oa_status=gold`;
* `license=cc-by`.

## 6. Final Paired Benchmark

Run the authoritative indexed benchmark with:

```bash
python scripts/run_paired_query_performance.py
```

For each predicate, the script:

* verifies equivalent result counts;
* performs one discarded warm-up per representation;
* records 30 paired executions;
* uses 15 inline-first and 15 5GNF-first blocks;
* randomizes the balanced execution order;
* reports medians and bootstrap 95% confidence intervals;
* applies a two-sided Wilcoxon signed-rank test;
* reports paired rank-biserial correlation as the effect size.

## 7. Authoritative Outputs

Raw paired measurements:

```text
experiment_results/paired_query_performance_raw_runs.csv
```

Statistical summary:

```text
experiment_results/paired_query_performance_statistical_summary.csv
```

These files supersede all preliminary and pre-index benchmark outputs.

The preliminary pre-index results are retained only in:

```text
experiment_results/supplementary_pre_index_benchmark/
```

They are not used as the final manuscript results.

## 8. Main Experimental Scale

The original OpenAlex graph contained:

* 98,783 `Work` nodes;
* 139,930 total nodes;
* 2,095,128 relationships;
* 442,537 metadata assignments;
* 57 canonical `MetadataValue` nodes.

The assignment-to-canonical-value reuse ratio was:

```text
7,763.81:1
```

This is a logical metadata reuse ratio, not a physical storage-compression ratio.

## 9. Lossless Reconstruction

The main experiment reported:

* inline assignments: 442,537;
* reconstructed assignments: 442,537;
* missing assignments: 0;
* mismatched assignments: 0;
* duplicate reconstructed assignments: 0;
* reconstruction ratio: 1.00.

## 10. Supplementary Experiments

The structured-license experiment evaluates:

```text
licenseCode -> licenseAuthority
```

It examines reconstruction, conjunctive reads, canonical-definition updates, and individual-assignment corrections.

The Northwind validation is stored in:

```text
data_sample/northwind/
northwind_results/
```

It provides supplementary structural evidence and is not a second query-performance benchmark.

## 11. Interpretation Limits

The timing results are specific to the recorded dataset, Neo4j version, hardware, indexes, predicates, and warm-cache paired protocol.

The final indexed benchmark showed that the inline-property representation was faster for all five evaluated atomic predicates.

The experiment therefore does not establish that 5GNF is a general query-performance optimization.

The strongest supported findings are:

* high metadata reuse;
* exact reconstruction;
* explicit reusable metadata structures;
* reduced update effort for shared canonical definitions;
* a clear trade-off between normalization and simple indexed reads.
