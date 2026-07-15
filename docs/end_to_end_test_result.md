# End-to-End Test Command and Latest Result

Date: 2026-07-15 15:15:57 +05:30

## Command Executed

```powershell
.\\scripts\\verify_pipeline.ps1 -IngestAllSamples
```

## Result Returned

| Check | Status | Details |
|---|---|---|
| Docker Compose reachable | PASS | docker compose is available |
| API readiness | PASS | HTTP 200 |
| Sample ingestion (mes) | PASS | HTTP 202 |
| Sample ingestion (erp) | PASS | HTTP 202 |
| Sample ingestion (equipment) | PASS | HTTP 202 |
| Sample ingestion (plm) | PASS | HTTP 202 |
| S3 objects present | PASS | Found 6 object(s) under mes/ |
| S3 objects (mes) | PASS | Found 6 object(s) under mes/ |
| S3 objects (erp) | PASS | Found 3 object(s) under erp/ |
| S3 objects (equipment) | PASS | Found 3 object(s) under equipment/ |
| S3 objects (plm) | PASS | Found 4 object(s) under plm/ |
| Kinesis stream data | PASS | Status=ACTIVE, Records=6 |
| Kinesis stream data (mes) | PASS | Status=ACTIVE, Records=6 |
| Kinesis stream data (erp) | PASS | Status=ACTIVE, Records=3 |
| Kinesis stream data (equipment) | PASS | Status=ACTIVE, Records=3 |
| Kinesis stream data (plm) | PASS | Status=ACTIVE, Records=3 |
| Postgres data | PASS | TableExists=t, Rows=6 |
| Postgres data (mes) | PASS | TableExists=t, Rows=6 |
| Postgres data (erp) | PASS | TableExists=t, Rows=3 |
| Postgres data (equipment) | PASS | TableExists=t, Rows=3 |
| Postgres data (plm) | PASS | TableExists=t, Rows=3 |

## Save Future Runs To File

```powershell
.\\scripts\\verify_pipeline.ps1 -IngestAllSamples | Tee-Object -FilePath .\\docs\\end_to_end_test_latest.txt
```
