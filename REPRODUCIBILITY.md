\# Reproducibility Instructions



This document describes how to reproduce the OpenAlex 5GNF experiment.



\## 1. Environment



The experiment was conducted using:



\- Python 3

\- Neo4j property graph database

\- Neo4j Python driver

\- pandas



Install Python dependencies with:



pip install -r requirements.txt



\## 2. Dataset Preparation



The paper experiment used the full file:



openalex\_works\_100k.jsonl



This file contains 100,000 raw OpenAlex work records. The repository includes a smaller 1,000-record sample only for inspection and testing:



data\_sample/openalex\_works\_sample\_1k.jsonl



To regenerate the full 100,000-record source file, run:



python scripts/download\_openalex\_100k.py



\## 3. CSV Conversion



Convert the OpenAlex JSONL file into Neo4j import CSV files with:



python scripts/convert\_openalex\_jsonl\_to\_csv.py



The generated CSV files are expected in the local folder:



neo4j\_csv/



This folder is not included in the repository because it is generated output.



\## 4. Neo4j Loading



Create the Neo4j constraints using:



cypher/01\_constraints.cypher



Then load the generated CSV files into Neo4j according to the import process used by the local experiment.



\## 5. 5GNF Query Evaluation



The 5GNF metadata-filtering queries are listed in:



cypher/02\_5gnf\_metadata\_queries.cypher



The script used to run the 5GNF query timing experiment is:



python scripts/run\_query\_performance.py



\## 6. Inline Baseline Evaluation



The inline-property baseline was created using:



python scripts/run\_inline\_baseline\_setup.py



The inline baseline queries are listed in:



cypher/03\_inline\_baseline\_queries.cypher



The script used to run the inline query timing experiment is:



python scripts/run\_inline\_query\_performance.py



\## 7. Recorded Results



The paper tables and recorded outputs are provided in:



paper\_tables/



These files record the results reported in the paper. The main experiment used 100,000 raw OpenAlex records and produced 98,783 unique Work nodes.



\## 8. Interpretation Limits



The reported timing results are workload-specific. They support the claim that 5GNF improved metadata-filtering queries in this OpenAlex experiment, but they do not establish that 5GNF is universally faster than inline properties.



The 1,000-record sample is included for testing repository structure and scripts. It is not expected to reproduce the exact 100,000-record paper results.

