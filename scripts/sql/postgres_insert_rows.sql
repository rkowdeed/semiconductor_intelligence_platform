-- Insert statements to restore the same rows targeted by postgres_delete_rows.sql
-- Run this file after delete operations if you want to reinsert those rows.

-- 1) Merge curated MES row (insert or update by primary key)
INSERT INTO mdm.lot_master (
    id,
    lot_id,
    recipe_id,
    equipment_id,
    wafer_count,
    temperature,
    event_type,
    event_timestamp,
    created_at
) VALUES (
    'f6a10849-b695-47fe-9ce3-259a8f538c35'::uuid,
    'LOT10001',
    'REC100',
    'ETCH001',
    25,
    47.8,
    'LOT_COMPLETED',
    '2026-07-15 10:30:00+00'::timestamptz,
    '2026-07-15 09:45:30.641835+00'::timestamptz
) ON CONFLICT (id) DO UPDATE SET
    lot_id = EXCLUDED.lot_id,
    recipe_id = EXCLUDED.recipe_id,
    equipment_id = EXCLUDED.equipment_id,
    wafer_count = EXCLUDED.wafer_count,
    temperature = EXCLUDED.temperature,
    event_type = EXCLUDED.event_type,
    event_timestamp = EXCLUDED.event_timestamp,
    created_at = EXCLUDED.created_at;

-- 2) Merge raw event row (insert or update by primary key)
INSERT INTO metadata.raw_events (
    id,
    source,
    event_type,
    payload,
    s3_key,
    created_at
) VALUES (
    '86dd9126-76f5-4b11-9d53-519d9a97119d'::uuid,
    'plm',
    'ECO_RELEASED',
    '{"owner": "eng_lead", "eventType": "ECO_RELEASED", "timestamp": "2026-07-15T10:40:00Z", "partNumber": "PN-AX12-9001", "changeOrderId": "ECO-2026-0042", "lifecycleState": "RELEASED"}'::jsonb,
    'plm/2026/07/15/plm-073e45aa-e82f-4ad4-82aa-98321f98d301.json',
    '2026-07-15 09:45:30.983785+00'::timestamptz
) ON CONFLICT (id) DO UPDATE SET
    source = EXCLUDED.source,
    event_type = EXCLUDED.event_type,
    payload = EXCLUDED.payload,
    s3_key = EXCLUDED.s3_key,
    created_at = EXCLUDED.created_at;

-- 3) Merge ingestion log row for MES (required for lineage view)
INSERT INTO metadata.ingestion_log (
    id,
    request_id,
    source,
    stream,
    status,
    duration_ms,
    error_message,
    created_at
) VALUES (
    '93a4d64b-3d9f-4ad2-bf58-395dcfe8bf6f'::uuid,
    'd7d0e96e-e542-4ca8-ad7a-dbcde8cce683',
    'mes',
    'mes-events',
    'SUCCESS',
    18.4,
    NULL,
    '2026-07-15 09:45:31.100000+00'::timestamptz
) ON CONFLICT (id) DO UPDATE SET
    request_id = EXCLUDED.request_id,
    source = EXCLUDED.source,
    stream = EXCLUDED.stream,
    status = EXCLUDED.status,
    duration_ms = EXCLUDED.duration_ms,
    error_message = EXCLUDED.error_message,
    created_at = EXCLUDED.created_at;

-- 4) Merge ingestion log row for PLM (required for lineage + source counts)
INSERT INTO metadata.ingestion_log (
    id,
    request_id,
    source,
    stream,
    status,
    duration_ms,
    error_message,
    created_at
) VALUES (
    'fc0ee37c-6d5f-4f66-b3d2-16df8abf53dc'::uuid,
    '073e45aa-e82f-4ad4-82aa-98321f98d301',
    'plm',
    'plm-events',
    'SUCCESS',
    22.1,
    NULL,
    '2026-07-15 09:45:31.300000+00'::timestamptz
) ON CONFLICT (id) DO UPDATE SET
    request_id = EXCLUDED.request_id,
    source = EXCLUDED.source,
    stream = EXCLUDED.stream,
    status = EXCLUDED.status,
    duration_ms = EXCLUDED.duration_ms,
    error_message = EXCLUDED.error_message,
    created_at = EXCLUDED.created_at;
