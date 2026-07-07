# OpenAlex 5GNF Replication Materials

This repository contains replication materials for the IEEE Access paper:

**A Fifth Graph Normal Form for Property Graph Schemas: Formal Foundations, Dependency-Preserving Decomposition, and OpenAlex-Based Evaluation**

## Important Note

This repository does not include the full `openalex_works_100k.jsonl` file used in the paper experiment. The full dataset is excluded because of file size and repository practicality. Instead, the repository includes:

- Scripts for regenerating the OpenAlex dataset
- A small 1,000-record OpenAlex sample for inspection and testing
- Cypher files for Neo4j constraints, indexes, and benchmark queries
- Paper tables and recorded experimental results
- Raw and summary timing results from the indexed benchmark
- Scripts used to prepare and evaluate the 5GNF and inline baseline representations

Therefore, this repository supports reproducibility and inspection, but it is not a complete data dump of the full experiment.

## Purpose

The materials support reproduction and inspection of the OpenAlex-based evaluation of Fifth Graph Normal Form (5GNF) for property graph schemas. The experiment evaluates metadata-level normalization using reusable `MetadataValue` nodes and `HAS_METADATA_VALUE` relationships.

## Dataset

The full experiment used:

- Source file: `openalex_works_100k.jsonl`
- Raw OpenAlex records: 100,000
- Unique Work nodes: 98,783
- Collapsed duplicate work rows: 1,217

The full JSONL file is not included in this repository. A smaller sample is provided in:

```text
data_sample/openalex_works_sample_1k.jsonl