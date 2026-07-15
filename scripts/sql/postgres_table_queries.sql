-- Postgres verification and maintenance queries
-- Database: semiconductor
-- User: sap_user

-- 1) Table-level record counts
SELECT 'mdm.lot_master' AS table_name, COUNT(*) AS record_count
FROM mdm.lot_master;

SELECT 'metadata.raw_events' AS table_name, COUNT(*) AS record_count
FROM metadata.raw_events;

-- 2) Source-wise counts in metadata.raw_events
SELECT source, COUNT(*) AS record_count
FROM metadata.raw_events
GROUP BY source
ORDER BY source;

-- 3) Read latest rows from curated MES table
SELECT id, lot_id, recipe_id, equipment_id, wafer_count, event_type, event_timestamp, created_at
FROM mdm.lot_master
ORDER BY created_at DESC
LIMIT 20;

-- 4) Read latest rows from generic raw events table
SELECT id, source, event_type, s3_key, created_at
FROM metadata.raw_events
ORDER BY created_at DESC
LIMIT 20;

-- 5) Read normalized ingestion lineage (request -> curated row)
SELECT ingestion_log_id,
	   request_id,
	   source,
	   stream,
	   curated_table,
	   curated_record_id,
	   curated_event_type,
	   curated_s3_key,
	   ingested_at,
	   curated_created_at
FROM metadata.v_ingestion_lineage
ORDER BY ingested_at DESC
LIMIT 50;

-- 6) Count lineage rows per source
SELECT source, COUNT(*) AS lineage_row_count
FROM metadata.v_ingestion_lineage
GROUP BY source
ORDER BY source;

-- Delete and reinsert statements were moved to:
--  - scripts/sql/postgres_delete_rows.sql
--  - scripts/sql/postgres_insert_rows.sql