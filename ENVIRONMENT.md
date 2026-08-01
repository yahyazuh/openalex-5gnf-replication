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



\* Initial heap size: not explicitly recorded

\* Maximum heap size: not explicitly recorded

\* Page cache size: not explicitly recorded

\* Database size on disk: not explicitly recorded

\* Query runtime: Neo4j default runtime

\* Index status: all indexes used by the evaluated queries were verified as `ONLINE`

\* Database instance: the same Neo4j container and database were used for both representations

\* Cache condition: one warm-up execution was discarded before the measured executions



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



