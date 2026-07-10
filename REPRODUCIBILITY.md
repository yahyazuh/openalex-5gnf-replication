# Reproducibility Instructions



This document describes how to reproduce the OpenAlex-based 5GNF experiment and its paired query-performance benchmark.



## 1. Environment



The experiment requires:



* Python 3

* Neo4j property graph database

* Neo4j Python driver

* pandas

* SciPy



Install the Python dependencies with:



```bash

pip install -r requirements.txt

```



The Neo4j connection can be configured through the following environment variables:



```text

NEO4J_URI

NEO4J_USER

NEO4J_PASSWORD

```



If these variables are not defined, the benchmark script uses the local defaults specified in the script.



## 2. Dataset Preparation



The paper experiment used:



```text

openalex_works_100k.jsonl

```



This file contains 100,000 raw OpenAlex work records. The repository includes a smaller 1,000-record sample for inspection and testing:



```text

data_sample/openalex_works_sample_1k.jsonl

```



To regenerate the full 100,000-record source file, run:



```bash

python scripts/download_openalex_100k.py

```



## 3. CSV Conversion



Convert the OpenAlex JSONL file into Neo4j import CSV files with:



```bash

python scripts/convert_openalex_jsonl_to_csv.py

```



The generated CSV files are written to:



```text

neo4j_csv/

```



This generated folder is not included in the repository.



## 4. Neo4j Loading and Indexes



Create the Neo4j constraints and indexes using:



```text

cypher/01_constraints.cypher

```



Load the generated CSV files into Neo4j using the same database configuration for both the inline-property and 5GNF representations.



The inline-property baseline is created with:



```bash

python scripts/run_inline_baseline_setup.py

```



Before benchmarking, verify that all required indexes are online and that the inline and 5GNF queries return identical result counts.



## 5. Query Workload



The 5GNF metadata-filtering queries are listed in:



```text

cypher/02_5gnf_metadata_queries.cypher

```



The equivalent inline-property queries are listed in:



```text

cypher/03_inline_baseline_queries.cypher

```



The evaluated predicates are:



* `language=en`

* `is_oa=True`

* `work_type=article`

* `oa_status=gold`

* `license=cc-by`



## 6. Paired Query-Performance Benchmark



Run the final paired benchmark with:



```bash

python scripts/run_paired_query_performance.py

```



For each predicate, the script:



* verifies equivalent inline and 5GNF result counts;

* performs one discarded warm-up execution for each representation;

* records 30 measured paired executions;

* uses exactly 15 inline-first and 15 5GNF-first execution blocks;

* randomizes the order of those balanced blocks;

* records every raw execution time;

* applies a two-sided Wilcoxon signed-rank test;

* uses a significance level of `alpha = 0.05`;

* computes paired rank-biserial correlation as the effect size;

* computes bootstrap 95% confidence intervals for the medians;

* reports median-based and mean-based descriptive statistics.



The paired design matches inline and 5GNF observations within the same execution block. Mean execution time is retained as a descriptive statistic, but statistical conclusions are based on the paired non-parametric analysis.



## 7. Recorded Outputs



The paired raw measurements are stored in:



```text

experiment_results/paired_query_performance_raw_runs.csv

```



The statistical summary is stored in:



```text

experiment_results/paired_query_performance_statistical_summary.csv

```



The raw file includes:



* query identifier;

* paired run number;

* representation executed first;

* inline execution time;

* 5GNF execution time;

* paired timing difference;

* verified result count.



The summary file includes:



* number of measured runs;

* result count;

* inline and 5GNF means;

* inline and 5GNF medians;

* bootstrap 95% confidence intervals for both medians;

* median speedup;

* Wilcoxon statistic;

* p-value;

* significance level;

* paired rank-biserial effect size;

* statistical interpretation.



Additional paper-oriented tables and recorded outputs are provided in:



```text

paper_tables/

```



## 8. Experimental Scale



The main OpenAlex experiment used:



* 100,000 raw work records;

* 98,783 unique `Work` nodes;

* 139,930 total nodes;

* 2,095,128 relationships;

* 442,537 metadata assignments;

* 57 reusable `MetadataValue` nodes.



The 1,000-record sample is included only for repository inspection and script testing. It is not expected to reproduce the full experimental results.



## 9. Interpretation Limits



The query-performance results are specific to the evaluated OpenAlex dataset, Neo4j configuration, indexes, hardware, query predicates, and paired execution protocol.



The results do not establish that 5GNF is universally faster than inline-property representations. They show only the behavior of the evaluated indexed metadata-filtering workload. The principal empirical claims of the paper remain metadata reuse, lossless reconstruction, and logical update-effort reduction.
