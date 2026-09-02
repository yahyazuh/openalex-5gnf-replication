CREATE CONSTRAINT work_id_unique IF NOT EXISTS
FOR (w:Work)
REQUIRE w.work_id IS UNIQUE;

CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept)
REQUIRE c.concept_id IS UNIQUE;

CREATE CONSTRAINT source_id_unique IF NOT EXISTS
FOR (s:Source)
REQUIRE s.source_id IS UNIQUE;

CREATE CONSTRAINT metadata_id_unique IF NOT EXISTS
FOR (m:MetadataValue)
REQUIRE m.metadata_id IS UNIQUE;

CREATE CONSTRAINT license_trait_code_unique IF NOT EXISTS
FOR (l:LicenseTrait)
REQUIRE l.licenseCode IS UNIQUE;

