// Q1: language = en
MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category: 'language', value: 'en'})
RETURN count(w) AS result_count;

// Q2: is_oa = True
MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category: 'is_oa', value: 'True'})
RETURN count(w) AS result_count;

// Q3: work_type = article
MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category: 'work_type', value: 'article'})
RETURN count(w) AS result_count;

// Q4: oa_status = gold
MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category: 'oa_status', value: 'gold'})
RETURN count(w) AS result_count;

// Q5: license = cc-by
MATCH (w:Work)-[:HAS_METADATA_VALUE]->(m:MetadataValue {category: 'license', value: 'cc-by'})
RETURN count(w) AS result_count;