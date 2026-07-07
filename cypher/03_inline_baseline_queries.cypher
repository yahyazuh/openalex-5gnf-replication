// Q1: language = en
MATCH (w:Work)
WHERE w.inline_language = 'en'
RETURN count(w) AS result_count;

// Q2: is_oa = True
MATCH (w:Work)
WHERE w.inline_is_oa = true
RETURN count(w) AS result_count;

// Q3: work_type = article
MATCH (w:Work)
WHERE w.inline_work_type = 'article'
RETURN count(w) AS result_count;

// Q4: oa_status = gold
MATCH (w:Work)
WHERE w.inline_oa_status = 'gold'
RETURN count(w) AS result_count;

// Q5: license = cc-by
MATCH (w:Work)
WHERE w.inline_license = 'cc-by'
RETURN count(w) AS result_count;