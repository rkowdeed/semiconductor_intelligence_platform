-- Delete statements for specific rows
-- Execute intentionally and review RETURNING output.

-- 1) Delete one curated MES row
DELETE FROM mdm.lot_master
WHERE id = 'f6a10849-b695-47fe-9ce3-259a8f538c35'::uuid
RETURNING *;

-- 2) Delete one raw event row
DELETE FROM metadata.raw_events
WHERE id = '86dd9126-76f5-4b11-9d53-519d9a97119d'::uuid
RETURNING *;

-- Optional safer execution:
-- BEGIN;
-- DELETE FROM mdm.lot_master
-- WHERE id = 'f6a10849-b695-47fe-9ce3-259a8f538c35'::uuid
-- RETURNING *;
-- DELETE FROM metadata.raw_events
-- WHERE id = '86dd9126-76f5-4b11-9d53-519d9a97119d'::uuid
-- RETURNING *;
-- ROLLBACK;
-- COMMIT;
