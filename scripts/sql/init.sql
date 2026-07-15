-- ---------------------------------------------------------------------------
-- Semiconductor_Operations_Data_Platform - PostgreSQL bootstrap
-- Executed automatically by the official postgres image on first startup
-- (mounted into /docker-entrypoint-initdb.d/).
-- ---------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS mdm;
CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS quality;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- mdm.lot_master ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mdm.lot_master (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id           VARCHAR(64) NOT NULL,
    recipe_id        VARCHAR(64) NOT NULL,
    equipment_id     VARCHAR(64) NOT NULL,
    wafer_count      INTEGER NOT NULL,
    temperature      DOUBLE PRECISION,
    event_type       VARCHAR(64) NOT NULL,
    event_timestamp  TIMESTAMPTZ NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_lot_master_lot_id ON mdm.lot_master (lot_id);

-- metadata.raw_events ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.raw_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source      VARCHAR(64) NOT NULL,
    event_type  VARCHAR(64),
    payload     JSONB NOT NULL,
    s3_key      VARCHAR(512),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_raw_events_source ON metadata.raw_events (source);

-- metadata.ingestion_log -------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.ingestion_log (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id    VARCHAR(64) NOT NULL,
    source        VARCHAR(64) NOT NULL,
    stream        VARCHAR(64),
    status        VARCHAR(32) NOT NULL,
    duration_ms   DOUBLE PRECISION,
    error_message VARCHAR(2048),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ingestion_log_request_id ON metadata.ingestion_log (request_id);

-- metadata.v_ingestion_lineage ------------------------------------------------
-- Normalized lineage view that pairs each successful ingestion_log entry
-- with its curated row by source and chronological sequence.
CREATE OR REPLACE VIEW metadata.v_ingestion_lineage AS
WITH logs AS (
    SELECT
        l.id AS ingestion_log_id,
        l.request_id,
        l.source,
        l.stream,
        l.status,
        l.duration_ms,
        l.error_message,
        l.created_at AS ingested_at,
        ROW_NUMBER() OVER (PARTITION BY l.source ORDER BY l.created_at, l.id) AS rn
    FROM metadata.ingestion_log l
    WHERE l.status = 'SUCCESS'
),
mes_curated AS (
    SELECT
        lm.id AS curated_record_id,
        'mes'::VARCHAR(64) AS source,
        lm.event_type,
        lm.created_at AS curated_created_at,
        NULL::VARCHAR(512) AS s3_key,
        ROW_NUMBER() OVER (PARTITION BY 'mes' ORDER BY lm.created_at, lm.id) AS rn
    FROM mdm.lot_master lm
),
raw_curated AS (
    SELECT
        re.id AS curated_record_id,
        re.source,
        re.event_type,
        re.created_at AS curated_created_at,
        re.s3_key,
        ROW_NUMBER() OVER (PARTITION BY re.source ORDER BY re.created_at, re.id) AS rn
    FROM metadata.raw_events re
)
SELECT
    l.ingestion_log_id,
    l.request_id,
    l.source,
    l.stream,
    l.status,
    l.duration_ms,
    l.error_message,
    l.ingested_at,
    CASE WHEN l.source = 'mes' THEN 'mdm.lot_master' ELSE 'metadata.raw_events' END AS curated_table,
    COALESCE(m.curated_record_id, r.curated_record_id) AS curated_record_id,
    COALESCE(m.event_type, r.event_type) AS curated_event_type,
    COALESCE(m.curated_created_at, r.curated_created_at) AS curated_created_at,
    COALESCE(m.s3_key, r.s3_key) AS curated_s3_key
FROM logs l
LEFT JOIN mes_curated m
    ON l.source = 'mes' AND m.source = l.source AND m.rn = l.rn
LEFT JOIN raw_curated r
    ON l.source <> 'mes' AND r.source = l.source AND r.rn = l.rn;

-- quality schema is reserved for the future Data Quality Service and is
-- intentionally left without tables in Phase 1.
