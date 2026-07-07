# OpenAlex 5GNF Replication Package

This repository contains the replication materials for the IEEE Access paper:

A Fifth Graph Normal Form for Property Graph Schemas: Formal Foundations, Dependency-Preserving Decomposition, and Large-Scale OpenAlex Evaluation

## Purpose

The package supports reproduction of the OpenAlex-based evaluation of Fifth Graph Normal Form (5GNF) for property graph schemas. The experiment evaluates metadata-level normalization using reusable MetadataValue nodes and HAS_METADATA_VALUE relationships.

The replication package includes:

- Python scripts used to prepare and evaluate the dataset
- Cypher query templates for Neo4j
- Paper tables and recorded experimental results
- A small OpenAlex JSONL sample for inspection and testing

## Dataset

The full experiment used:

- Source file: openalex_works_100k.jsonl
- Raw OpenAlex records: 100,000
- Unique Work nodes: 98,783

The full JSONL file is not included in this repository. A smaller sample is provided in:

data_sample/openalex_works_sample_1k.jsonl

The complete dataset can be regenerated using:

scripts/download_openalex_100k.py

## Main Results

The experiment produced the following high-level results:

- Total nodes: 139,930
- Total relationships: 2,095,128
- MetadataValue nodes: 57
- HAS_METADATA_VALUE relationships: 442,537
- Metadata reuse ratio: 7,763.81x
- Mean 5GNF query time: 49.268 ms
- Mean inline-property baseline query time: 111.677 ms
- Mean observed speedup: 2.27x

These results apply to the tested OpenAlex metadata-filtering workload. They should not be interpreted as a universal performance claim for all graph workloads.

## Repository Structure

openalex_5gnf_replication/
- cypher/
  - 01_constraints.cypher
  - 02_5gnf_metadata_queries.cypher
  - 03_inline_baseline_queries.cypher
- data_sample/
  - openalex_works_sample_1k.jsonl
- paper_tables/
  - experiment_summary_for_paper.txt
  - latex_tables_results.txt
  - reproducibility_note.txt
  - results_section_draft.txt
  - table_1_final_experiment_summary.csv
  - table_2_graph_size_summary.csv
  - table_3_metadata_category_reuse_summary.csv
  - table_4_query_performance_metadata_filtering.csv
  - table_5_schema_evolution_update_benefit.csv
  - table_6_query_performance_5gnf_vs_inline.csv
  - table_7_baseline_comparison_summary.csv
- scripts/
  - check_openalex_metadata.py
  - convert_openalex_jsonl_to_csv.py
  - download_openalex_100k.py
  - run_inline_baseline_setup.py
  - run_inline_query_performance.py
  - run_query_performance.py
- requirements.txt
- README.md

## Requirements

Install dependencies with:

pip install -r requirements.txt

Required Python packages:

- neo4j
- pandas

## Notes

The reported paper results were generated from the full 100,000-record OpenAlex file, not from the 1,000-record sample. The sample is included only to make the repository inspectable and easier to test.

The performance results depend on the Neo4j environment, indexing, hardware, memory state, and query execution conditions.