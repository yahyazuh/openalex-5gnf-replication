# Dataset provenance

The complete OpenAlex JSONL file used in the main experiment is not included in this repository because its size is 592,978,139 bytes. The repository instead preserves the exact dataset checksum, retrieval configuration, record identifiers, aggregate counts, raw benchmark results, and a 1,000-record sample.

## Exact experimental dataset

- Raw records: 100,000
- Unique OpenAlex Work identifiers: 98,783
- Duplicate identifiers: 1,217
- SHA-256: `6f194b77c7a7fe37e4402aeafff49a0061f68044f48a47f50e0646b32ea504e1`

The checksum is stored in `openalex_works_100k_sha256.txt`. Dataset metadata and the original query configuration are stored in `openalex_works_100k_metadata.json`.

The compressed file `openalex_work_ids_100k.txt.gz` contains the 100,000 OpenAlex identifiers in their original record order, including the 1,217 duplicate identifiers collapsed during graph construction.

## Inspection sample

A 1,000-record sample is provided as `data_sample/openalex_works_sample_1k.jsonl`. Its checksum is stored in `openalex_works_sample_1k_sha256.txt`.

## Reproducibility limitation

OpenAlex is continuously updated. Retrieving the preserved identifiers again may produce records whose metadata differs from the original experimental file. Exact numerical reproduction therefore requires a JSONL file matching the recorded SHA-256 checksum.
