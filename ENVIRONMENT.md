\# Experimental Environment



\## Software



\* Neo4j version: 5.21.2

\* Neo4j edition: Community Edition

\* Neo4j container image: `neo4j:5.21`

\* Container runtime: Docker Desktop

\* Python version: 3.12.0

\* Neo4j Python driver version: 5.28.2

\* pandas version: 2.3.2

\* scipy version: 1.15.2

\* Host Java version: 1.8.0\_491

\* Neo4j container JVM version: not recorded

\* Host operating system: Microsoft Windows, 64-bit



\## Hardware



\* Processor: AMD Ryzen 5 5500U with Radeon Graphics

\* Physical CPU cores: 6

\* Logical processors: 12

\* Installed RAM: 14,858,907,648 bytes, approximately 13.84 GiB

\* Storage: local Windows drive labelled `Windows-SSD`

\* Container name: `neo4j-gnf`

\* Neo4j HTTP port: 7474

\* Neo4j Bolt port: 7687



\## Neo4j Configuration



\* Initial JVM heap size: 108 MiB (effective JVM setting)

\* Maximum JVM heap size: 1,714 MiB (effective JVM setting)

\* Page cache size: 512 MiB (explicitly configured)


* Original mixed-representation database size: 542,648 KiB (529.93 MiB).




\* Query runtime: Neo4j default runtime

\* Index status: all indexes used by the evaluated queries were verified as `ONLINE`

\* Database instance: the same Neo4j container and database were used for both representations

\* Cache condition: one warm-up execution was discarded before the measured executions

## Physical Storage Comparison

A supplementary storage experiment was conducted using two
isolated Neo4j 5.21.2 Community Edition databases, reconstructed
from the same OpenAlex graph.

Both databases contained 98,783 Work nodes, 32,245 Concept nodes,
8,845 Source nodes, and identical non-metadata relationships.

* Inline-only: 139,873 nodes and 1,652,591 relationships.
* 5GNF-only: 139,930 nodes and 2,095,128 relationships.
* Inline-only database storage: 255,252 KiB (249.27 MiB).
* 5GNF-only database storage: 271,620 KiB (265.25 MiB).
* Absolute storage overhead: 16,368 KiB (15.98 MiB).
* Relative storage overhead: 6.41%.

Both representations used identical shared-node constraints and
Neo4j default lookup indexes. The inline representation used five
metadata-property indexes, while 5GNF used a composite
MetadataValue(category, value) index and a metadata_id uniqueness
constraint. All indexes were ONLINE.

Measurements were obtained using `du -sk` on the Neo4j database
directories after a graceful shutdown of both containers.

The comparison measures database-directory storage, including
representation-specific indexes. It excludes separate transaction
logs and does not isolate the cost of metadata relationships alone.

The structured-license experiment was excluded from both databases.



\## Dataset and Graph Size



\* Raw OpenAlex records: 100,000

\* Unique `Work` nodes: 98,783

\* Collapsed duplicate work rows: 1,217

\* Total graph nodes: 139,930

\* Total graph relationships: 2,095,128

\* Metadata assignments: 442,537

\* Canonical `MetadataValue` nodes: 57



\## Benchmark Protocol



\* Five metadata-filtering predicates were evaluated

\* 30 paired measured executions were recorded per predicate

\* One discarded warm-up execution was performed for each representation

\* The protocol used 15 inline-first and 15 5GNF-first execution blocks

\* The balanced execution-block order was randomized

\* Both representations were evaluated on the same database instance and dataset

\* Equivalent query-result counts were verified before interpreting timing differences

\* Median execution time was used as the primary descriptive statistic

\* Means were retained as supplementary descriptive statistics

\* Bootstrap 95% confidence intervals were calculated

\* A two-sided Wilcoxon signed-rank test was applied to the paired measurements

\* The statistical significance level was `alpha = 0.05`

\* Paired rank-biserial correlation was reported as the effect size



\## Interpretation



The recorded timing results are specific to this hardware, software environment, Neo4j configuration, dataset, indexes, query predicates, and warm-cache paired-execution protocol.



The environment information does not establish that the same absolute execution times will be obtained on another machine. Reproduction should focus on the experimental procedure, equivalent query results, direction of observed differences, and reported structural metrics.



