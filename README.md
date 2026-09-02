# OpenAlex 5GNF Replication Materials

This repository contains replication materials for the IEEE Access paper:

**A Fifth Graph Normal Form for Property Graph Schemas: Formal Foundations, Dependency-Preserving Decomposition, and OpenAlex-Based Evaluation**

## Important Note

The repository does not include the complete `openalex_works_100k.jsonl` file used in the main experiment because of its size.

Instead, the repository provides:

* scripts for regenerating the OpenAlex dataset;
* the SHA-256 checksum and retrieval configuration of the exact dataset;
* the 100,000 OpenAlex identifiers in original record order;
* a 1,000-record OpenAlex sample for inspection and testing;
* an idempotent CSV-to-Neo4j import script;
* Cypher files for Neo4j constraints, indexes, and benchmark queries;
* raw paired query-performance measurements;
* statistical summaries;
* scripts for constructing and evaluating the inline and 5GNF representations;
* structured-license experiment materials;
* supplementary Northwind structural-validation materials.

The repository supports reproduction and inspection of the experimental procedure, but it is not a complete copy of the original OpenAlex dataset.

## Purpose

The repository supports the OpenAlex-based evaluation of Fifth Graph Normal Form (5GNF) for property graph schemas.

The main experiment evaluates:

* reusable metadata representation;
* metadata reuse;
* lossless reconstruction;
* logical update effort;
* indexed metadata-filtering query behavior.

In the evaluated 5GNF representation, reusable metadata values are represented as `MetadataValue` nodes connected to `Work` nodes through `HAS_METADATA_VALUE` relationships.

The repository also includes a supplementary Northwind structural validation. This experiment evaluates metadata externalization and lossless reconstruction on a transactional-style graph. It is not used for query-performance benchmarking.

## Authoritative Experimental Results

The primary query-performance results are the indexed, randomized, paired benchmark results stored in:

```text
experiment_results/paired_query_performance_raw_runs.csv
```

and:

```text
experiment_results/paired_query_performance_statistical_summary.csv
```

The corresponding paper-ready table is stored in:

```text
paper_tables/table_7_final_indexed_results.csv
```

These files are the authoritative results for the manuscript and supersede all preliminary and pre-index benchmark outputs.

Historical and preliminary results are retained only in clearly labelled archival or supplementary folders. They are not used as evidence in the submitted manuscript.

## OpenAlex Dataset

The complete OpenAlex experiment used:

* source file: `openalex_works_100k.jsonl`;
* raw OpenAlex records: 100,000;
* unique `Work` nodes after duplicate identifiers were collapsed: 98,783;
* collapsed duplicate rows: 1,217;
* total graph nodes: 139,930;
* total graph relationships: 2,095,128;
* metadata assignments: 442,537;
* canonical `MetadataValue` nodes: 57.

The complete JSONL file is not included in the repository. A smaller inspection sample is provided in:

```text
data_sample/openalex_works_sample_1k.jsonl
```

The exact file checksum, retrieval configuration, and ordered record identifiers are preserved in:

```text
dataset_manifest/openalex_works_100k_sha256.txt
dataset_manifest/openalex_works_100k_metadata.json
dataset_manifest/openalex_work_ids_100k.txt.gz
```

The original file had SHA-256 checksum
`6f194b77c7a7fe37e4402aeafff49a0061f68044f48a47f50e0646b32ea504e1`.

The OpenAlex dataset can be regenerated with:

```bash
python scripts/download_openalex_100k.py
```

Because OpenAlex is a changing external data source, a newly downloaded file may not be byte-for-byte identical to the original experimental dataset unless the same snapshot, retrieval procedure, identifiers, and date are used.

## Metadata Reuse

The main experiment contains 442,537 metadata assignments represented through 57 canonical metadata values.

This corresponds to an assignment-to-canonical-value reuse ratio of:

```text
7,763.81:1
```

This value measures logical metadata reuse. It must not be interpreted as a physical database-storage compression ratio.

## Paired Query-Performance Benchmark

The final indexed query-performance experiment is executed with:

```bash
python scripts/run_paired_query_performance.py
```

For each of the five metadata-filtering predicates, the script:

* performs one discarded warm-up execution for each representation;
* records 30 paired measured executions;
* uses 15 inline-first and 15 5GNF-first execution blocks;
* randomizes the balanced execution-block sequence;
* verifies equivalent result counts;
* reports median execution times;
* reports bootstrap 95% confidence intervals;
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

The indexed inline-property representation was faster for all five evaluated atomic equality predicates.

These results show that 5GNF is not a general query-performance optimization for simple indexed property filtering. Its primary benefits concern metadata reuse, explicit representation of reusable structures, lossless reconstruction, and centralized maintenance of shared metadata definitions.

## Supplementary Pre-Index Benchmark

Pre-index results are retained in:

```text
experiment_results/supplementary_pre_index_benchmark/
```

These results were collected before equivalent inline-property indexes were created.

They are included only to document the effect of index configuration and must not be treated as the primary performance results.

The indexed paired benchmark is the definitive comparison used in the manuscript.

## Lossless Reconstruction

Lossless reconstruction is evaluated by comparing the metadata assignments represented in the inline graph with the assignments reconstructed from the 5GNF graph.

The main OpenAlex experiment reports:

* inline assignments: 442,537;
* reconstructed assignments: 442,537;
* missing assignments: 0;
* mismatched assignments: 0;
* duplicate reconstructed assignments: 0;
* reconstruction ratio: 1.00.

These results verify lossless reconstruction for the measured metadata scope.

## Structured-License Experiment

The repository includes a structured-license experiment based on the trait dependency:

```text
licenseCode -> licenseAuthority
```

The experiment evaluates:

* canonical representation of license traits;
* reconstruction of structured license information;
* indexed conjunctive read behavior;
* canonical-definition update behavior;
* individual-assignment correction behavior.

The canonical-definition update benchmark evaluates a change to shared information associated with a canonical license trait.

It does not represent a correction to the license assigned to one individual work.

This distinction is important:

* changing a shared canonical definition may require many repeated inline updates but only one normalized update;
* correcting one individual work assignment requires one local modification in either representation.

## Supplementary Northwind Structural Validation

The Northwind experiment is not used for query-performance benchmarking.

Its purpose is to evaluate whether reusable metadata can be externalized into canonical metadata-value structures and reconstructed without loss.

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

The Northwind validation should be interpreted as supplementary structural evidence rather than as a second complete performance experiment.

## Installation

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

The required packages include:

* `neo4j`;
* `numpy`;
* `pandas`;
* `requests`;
* `scipy`;
* `tqdm`.

For exact reproducibility, the package versions recorded in `requirements.txt` should match the versions used to generate the final results.

## Reproducibility Instructions

Detailed setup, loading, execution, output, and interpretation instructions are provided in:

```text
REPRODUCIBILITY.md
```

The experimental environment, including Neo4j, Java, Python, operating-system, hardware, memory, and database configuration details, should be recorded in:

```text
ENVIRONMENT.md
```

## Interpretation Limits

The experimental results are specific to:

* the evaluated OpenAlex dataset;
* the selected metadata scope;
* the Neo4j implementation;
* the evaluated indexes;
* the execution environment;
* the tested predicates;
* the measured graph size;
* the paired execution protocol.

The results do not establish that 5GNF:

* is universally faster than inline-property representations;
* reduces physical database storage by the metadata reuse ratio;
* improves every read or update workload;
* is optimal for every graph database system.

The strongest supported empirical findings are:

* high logical reuse of canonical metadata values;
* exact reconstruction for the evaluated metadata scope;
* explicit representation of reusable metadata structures;
* reduced logical update effort for shared canonical definitions;
* a measurable trade-off between normalization benefits and simple indexed read performance.

## Update benchmark timing note

The canonical-definition update benchmark retained all 30 paired observations, including four unusually long inline executions.
The affected runs and timing values are documented in experiment_results/structured_license/UPDATE_OUTLIERS.md.
Median-based and nonparametric statistics are used as the principal timing evidence, while the affected-element count is the more implementation-independent result.
