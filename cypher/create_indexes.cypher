// Indexes for fair comparison between inline baseline and 5GNF representation.
// Run this before executing the query-performance benchmark.

CREATE INDEX work_inline_language IF NOT EXISTS
FOR (w:Work) ON (w.inline_language);

CREATE INDEX work_inline_is_oa IF NOT EXISTS
FOR (w:Work) ON (w.inline_is_oa);

CREATE INDEX work_inline_work_type IF NOT EXISTS
FOR (w:Work) ON (w.inline_work_type);

CREATE INDEX work_inline_oa_status IF NOT EXISTS
FOR (w:Work) ON (w.inline_oa_status);

CREATE INDEX work_inline_license IF NOT EXISTS
FOR (w:Work) ON (w.inline_license);

CREATE INDEX metadata_value_category_value IF NOT EXISTS
FOR (m:MetadataValue) ON (m.category, m.value);

CREATE INDEX work_id IF NOT EXISTS
FOR (w:Work) ON (w.id);