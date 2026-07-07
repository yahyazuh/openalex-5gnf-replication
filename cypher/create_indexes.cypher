// Indexes for fair comparison between inline baseline and 5GNF representation.
// Run this before executing the query-performance benchmark.

CREATE INDEX workinline_language IF NOT EXISTS
FOR (w:WorkInline) ON (w.inline_language);

CREATE INDEX workinline_is_oa IF NOT EXISTS
FOR (w:WorkInline) ON (w.inline_is_oa);

CREATE INDEX workinline_work_type IF NOT EXISTS
FOR (w:WorkInline) ON (w.inline_work_type);

CREATE INDEX workinline_oa_status IF NOT EXISTS
FOR (w:WorkInline) ON (w.inline_oa_status);

CREATE INDEX workinline_license IF NOT EXISTS
FOR (w:WorkInline) ON (w.inline_license);

CREATE INDEX metadata_value_key_value IF NOT EXISTS
FOR (m:MetadataValue) ON (m.key, m.value);

CREATE INDEX work_id IF NOT EXISTS
FOR (w:Work) ON (w.id);