# Canonical definition update timing note

The benchmark retained all 30 paired observations.
Four inline executions were unusually long: runs 12, 16, 25, and 29.
Their elapsed times were 14638.4503 ms, 20898.8774 ms, 33599.5368 ms, and 40009.0505 ms.
Most remaining inline observations were approximately 795 to 1323 ms.
No observations were removed after inspection.
The affected-element count is the more implementation-independent result: 34379 inline property instances versus one canonical structured node.
The median, bootstrap confidence interval, Wilcoxon signed-rank test, and rank-biserial effect size are therefore used as the principal timing statistics.
