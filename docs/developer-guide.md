# Developer Guide

This guide explains how the repository is organized, how the local services fit together, how to configure and run them, and how to troubleshoot the most common problems.

## 1. What this repository does

At a high level, the platform provides a metadata-driven ingestion pipeline for semiconductor data sources such as MES, ERP, equipment, PLM, telemetry, yield, and generic file feeds.

For a successful ingestion request, the platform:

1. Receives an HTTP request in the FastAPI ingestion service.
2. Resolves source metadata from YAML files.
3. Parses the payload into a canonical Python dictionary.
4. Validates the payload against a JSON Schema.
5. Writes the raw payload to Amazon S3.
6. Publishes an event to Amazon Kinesis.
7. Writes a curated record to PostgreSQL.
8. Writes an audit entry to `metadata.ingestion_log`.

That behavior is centered in [ingestion-service/services/ingestion_service.py](ingestion-service/services/ingestion_service.py).

## 2. Repository tour

Use this section when you want to understand where to look before changing anything.

| Path | Why it exists |
|---|---|
| [README.md](README.md) | Entry point for the repository |
| [docker-compose.yml](docker-compose.yml) | Defines the local multi-service stack |
| [.env](.env) | Default local environment variables used by Docker Compose |
| [requirements.txt](requirements.txt) | Python dependencies for the service and tests |
| [ingestion-service/](../ingestion-service) | FastAPI application, API routes, parsers, validators, storage, and orchestration |
| [common/](../common) | Shared platform code: config loading, AWS wrappers, models, repositories, logging, governance, traceability, AI scaffolding |
| [config/](../config) | Application, AWS, database, and logging YAML config |
| [metadata/](../metadata) | Source registry and metadata-driven runtime behavior |
| [schemas/](../schemas) | Per-source JSON Schemas |
| [scripts/](../scripts) | Verification, smoke testing, SQL bootstrap helpers, and normalization utilities |
| [infrastructure/](../infrastructure) | Dockerfile, optional LocalStack bootstrap assets, Prometheus config, helper scripts |
| [sample-data/](../sample-data) | Example payloads for manual testing and end-to-end validation |
| [tests/](../tests) | Offline automated test suite |
| [docs/](.) | Design notes and documentation |

## 3. Local runtime architecture

### Services started by Docker Compose

[docker-compose.yml](../docker-compose.yml) starts five services:

| Service | Container name | Purpose | Port |
|---|---|---|---:|
| PostgreSQL | `sap-postgres` | Curated data, audit logs, and platform tables | 5432 |
| pgAdmin | `sap-pgadmin` | PostgreSQL UI | 5050 |
| Ingestion service | `sap-ingestion-service` | FastAPI HTTP API | 8000 |
| Prometheus | `sap-prometheus` | Metrics scraping | 9090 |
| Grafana | `sap-grafana` | Dashboards | 3000 |

### What initializes each service

- PostgreSQL runs [scripts/sql/init.sql](../scripts/sql/init.sql) on first startup.
- The ingestion image is built from [infrastructure/docker/Dockerfile](../infrastructure/docker/Dockerfile).
- Prometheus uses [infrastructure/prometheus/prometheus.yml](../infrastructure/prometheus/prometheus.yml).

### AWS resources required before startup

Before startup, ensure these AWS resources already exist in your account:

- S3 bucket `semiconductor-landing`
- Kinesis stream `mes-events`
- Kinesis stream `metadata-events`
- Kinesis stream `quality-events`
- Kinesis stream `plm-events`

The service does not auto-provision these resources. If S3 uploads or Kinesis publishes fail, verify the bucket/stream names in [metadata/streams.yaml](../metadata/streams.yaml), [metadata/sources.yaml](../metadata/sources.yaml), and [.env](../.env).

## 4. Request lifecycle, step by step

This is the most important flow in the repository.

### Step 1: FastAPI starts and loads routes

The application entrypoint is [ingestion-service/main.py](../ingestion-service/main.py).

At startup it:

- loads [config/application.yaml](../config/application.yaml)
- configures logging
- registers health routes
- registers config inspection routes
- dynamically builds ingestion routes

Dynamic route generation happens in [ingestion-service/api/routes.py](../ingestion-service/api/routes.py).

### Step 2: Source definitions come from metadata

[metadata/sources.yaml](../metadata/sources.yaml) is the main source registry. Each source entry defines:

- endpoint
- HTTP method
- input format
- schema path
- curated target table/schema
- logical stream
- raw S3 bucket/prefix
- enabled flag

Those files are loaded through [common/config/loader.py](../common/config/loader.py), then exposed through [common/config/metadata_registry.py](../common/config/metadata_registry.py).

### Step 3: The incoming payload is parsed

The request body is parsed in [ingestion-service/parser/payload_parser.py](../ingestion-service/parser/payload_parser.py), which delegates to [ingestion-service/parser/format_parser_registry.py](../ingestion-service/parser/format_parser_registry.py).

Supported parsing behavior includes:

- JSON
- XML
- CSV
- YAML
- plain text
- Parquet
- binary passthrough wrappers for HDF5, Protobuf, Avro, gRPC, STDF, SECS/GEM, and OPC-UA

Format selection uses:

1. `input_format` from [metadata/sources.yaml](../metadata/sources.yaml), if present
2. otherwise the HTTP `Content-Type`
3. otherwise JSON by default

### Step 4: The payload is validated

Validation metadata is defined in [metadata/validation.yaml](../metadata/validation.yaml).

The validator loads the schema path for the source and rejects invalid payloads with HTTP 400.

### Step 5: Raw payload is stored in S3

The storage flow uses:

- [ingestion-service/storage/raw_storage_service.py](../ingestion-service/storage/raw_storage_service.py)
- [common/storage/raw_payload_store.py](../common/storage/raw_payload_store.py)
- [common/aws/s3_client.py](../common/aws/s3_client.py)

The S3 key prefix comes from the source metadata and routing configuration.

### Step 6: Event is published to Kinesis

Publishing uses:

- [ingestion-service/publisher/event_publisher.py](../ingestion-service/publisher/event_publisher.py)
- [common/aws/kinesis_publisher.py](../common/aws/kinesis_publisher.py)
- [metadata/streams.yaml](../metadata/streams.yaml)

Logical stream names such as `mes` and `quality` are resolved into physical stream names such as `mes-events` and `quality-events`.

### Step 7: Curated data is written to PostgreSQL

Curation uses [ingestion-service/repository/curation_service.py](../ingestion-service/repository/curation_service.py).

Behavior is:

- `mes` maps into `mdm.lot_master`
- sources without a dedicated curator fall back to `metadata.raw_events`

The repository layer lives in [common/repository/repositories.py](../common/repository/repositories.py).

### Step 8: Audit log is always written

Even if the request fails, [ingestion-service/services/ingestion_service.py](../ingestion-service/services/ingestion_service.py) still tries to write an entry to `metadata.ingestion_log` in its `finally` block.

That table is created in [scripts/sql/init.sql](../scripts/sql/init.sql).

## 5. Configuration model

Configuration is split between environment variables and YAML files.

### `.env`

[.env](../.env) provides local defaults for:

- PostgreSQL
- pgAdmin
- AWS account credentials
- S3 bucket name
- Kinesis stream names
- Grafana

### `config/*.yaml`

| File | Purpose |
|---|---|
| [config/application.yaml](../config/application.yaml) | API settings, metadata file locations, health check list |
| [config/aws.yaml](../config/aws.yaml) | AWS endpoint, region, credentials, S3 and Kinesis defaults |
| [config/database.yaml](../config/database.yaml) | Database connection settings and schema list |
| [config/logging.yaml](../config/logging.yaml) | Logging behavior |

### Interpolation rules

[common/config/loader.py](../common/config/loader.py) supports `${VAR:default}` interpolation. That means:

- YAML values can refer to environment variables
- if the variable is not set, the default value in the YAML string is used
- loaded config objects are cached for reuse

### Important local nuance

For Docker Compose, the ingestion container receives an explicit `DATABASE_URL` that points to the `postgres` container.

For host-based local development, set `DATABASE_URL` yourself before starting the app. The default fallback in [common/models/base.py](../common/models/base.py) is intentionally redacted and should not be relied on.

## 6. Metadata files and what each one controls

These files are the heart of the repository.

| File | Controls |
|---|---|
| [metadata/sources.yaml](../metadata/sources.yaml) | Source registry, endpoint paths, formats, schemas, tables, raw prefixes, logical streams |
| [metadata/routing.yaml](../metadata/routing.yaml) | Routing overrides for raw buckets, raw prefixes, and logical streams |
| [metadata/streams.yaml](../metadata/streams.yaml) | Physical Kinesis stream names and shard counts |
| [metadata/mappings.yaml](../metadata/mappings.yaml) | Field-to-column mapping for curated tables |
| [metadata/validation.yaml](../metadata/validation.yaml) | Per-source schema path and validation policy |
| [metadata/data_categories.yaml](../metadata/data_categories.yaml) | Supported data categories and example formats exposed by `/api/v1/config/data-categories` |

## 7. Database objects created locally

On first PostgreSQL startup, [scripts/sql/init.sql](../scripts/sql/init.sql) creates:

### Schemas

- `mdm`
- `metadata`
- `quality`
- `ai`

### Main tables

- `mdm.lot_master`
- `metadata.raw_events`
- `metadata.ingestion_log`
- `metadata.governance_policies`
- `metadata.lakehouse_assets`
- `metadata.traceability_lineage`
- `metadata.agent_heartbeats`
- `ai.documents`

### Derived view

- `metadata.v_ingestion_lineage`

That lineage view is useful when you want to correlate requests, curated records, and S3 keys.

## 8. Setup instructions

### Option A: full local stack with Docker Compose

This is the recommended path for new developers.

#### Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- Python 3.12 if you also want to run tests or host scripts outside containers
- Free host ports: `5432`, `5050`, `8000`, `9090`, `3000`

#### Startup

From the repository root:

```powershell
docker compose up --build
```

To run detached:

```powershell
docker compose up --build -d
```

#### Confirm service health

```powershell
docker compose ps
curl.exe http://localhost:8000/api/v1/ready
curl.exe http://localhost:8000/api/v1/health
```

#### Open the main UIs

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- pgAdmin: `http://localhost:5050`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

### Option B: run the API on the host but keep dependencies in Docker

This is useful for faster edit/reload loops.

1. Start only PostgreSQL:

   ```powershell
   docker compose up -d postgres
   ```

2. Create and activate a Python environment.
3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Set the required environment variables:

   ```powershell
   $env:PYTHONPATH = "$PWD;$PWD\ingestion-service"
   $env:POSTGRES_USER = "sap_user"
   $env:POSTGRES_PASSWORD = "sap_password"
   $env:POSTGRES_DB = "semiconductor"
   $env:DATABASE_URL = "postgresql+psycopg2://$env:POSTGRES_USER`:$env:POSTGRES_PASSWORD@localhost:5432/$env:POSTGRES_DB"
   $env:AWS_REGION = "ap-south-2"
   $env:AWS_PROFILE = "agent-toolkit"
   ```

5. Start the API:

   ```powershell
   cd ingestion-service
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

There is also a helper script at [scripts/run_local.sh](../scripts/run_local.sh), but it is bash-oriented. On Windows, the PowerShell commands above are usually clearer.

## 9. How to run and verify the platform

### Check health and metadata endpoints

```powershell
curl.exe http://localhost:8000/api/v1/health
curl.exe http://localhost:8000/api/v1/config/sources
curl.exe http://localhost:8000/api/v1/config/streams
curl.exe http://localhost:8000/api/v1/config/data-categories
```

### Post sample events

#### MES

```powershell
curl.exe -X POST http://localhost:8000/api/v1/mes/events -H "Content-Type: application/json" --data-binary "@sample-data/mes/lot_completed_sample.json"
```

#### ERP

```powershell
curl.exe -X POST http://localhost:8000/api/v1/erp/events -H "Content-Type: application/json" --data-binary "@sample-data/erp/work_order_sample.json"
```

#### Equipment

```powershell
curl.exe -X POST http://localhost:8000/api/v1/equipment/events -H "Content-Type: application/json" --data-binary "@sample-data/equipment/equipment_event_sample.json"
```

#### PLM

```powershell
curl.exe -X POST http://localhost:8000/api/v1/plm/events -H "Content-Type: application/json" --data-binary "@sample-data/plm/product_lifecycle_event_sample.json"
```

#### Telemetry

```powershell
curl.exe -X POST http://localhost:8000/api/v1/telemetry/events -H "Content-Type: application/json" --data-binary "@sample-data/telemetry/telemetry_sample.json"
```

#### Yield CSV

```powershell
curl.exe -X POST http://localhost:8000/api/v1/yield/events -H "Content-Type: text/csv" --data-binary "@sample-data/yield/yield_sample.csv"
```

### Expected response shape

Successful ingestion returns HTTP 202 and a JSON object with:

- `request_id`
- `source`
- `status`
- `s3_key`
- `stream`
- `sequence_number`
- `curated_record_id`

### Verify S3, Kinesis, and PostgreSQL manually

#### S3

```powershell
aws --region ap-south-2 --profile agent-toolkit s3 ls s3://semiconductor-landing --recursive
```

#### Kinesis

```powershell
aws --region ap-south-2 --profile agent-toolkit kinesis describe-stream --stream-name mes-events
```

#### PostgreSQL

```powershell
docker compose exec -T postgres psql -U sap_user -d semiconductor -c "SELECT * FROM mdm.lot_master ORDER BY created_at DESC LIMIT 5;"
docker compose exec -T postgres psql -U sap_user -d semiconductor -c "SELECT * FROM metadata.raw_events ORDER BY created_at DESC LIMIT 5;"
docker compose exec -T postgres psql -U sap_user -d semiconductor -c "SELECT * FROM metadata.ingestion_log ORDER BY created_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U sap_user -d semiconductor -c "SELECT * FROM metadata.v_ingestion_lineage ORDER BY ingested_at DESC LIMIT 10;"
```

### Use the built-in verification scripts

For Windows and PowerShell users:

```powershell
.\scripts\verify_pipeline.ps1 -IngestAllSamples
```

That script:

- checks Docker Compose reachability
- checks API readiness
- optionally ingests sample payloads
- checks S3 object presence
- checks Kinesis stream health and record counts
- checks PostgreSQL tables and row counts
- runs native file normalization checks
- writes a report to [docs/end_to_end_test_result.md](end_to_end_test_result.md)

For bash environments:

```bash
./scripts/smoke_test.sh
```

## 10. Normalizing raw files from S3

The repository supports a secondary workflow for raw files already stored in S3.

The entrypoint is [scripts/normalize_s3_files.py](../scripts/normalize_s3_files.py), which calls [ingestion-service/services/s3_normalization_service.py](../ingestion-service/services/s3_normalization_service.py).

Typical usage:

```powershell
python .\scripts\normalize_s3_files.py --source file_multiformat --bucket semiconductor-landing --source-prefix files/native --normalized-prefix files/native/normalized --format AUTO
```

Use this when:

- you uploaded XML, CSV, text, Parquet, or other raw files directly to S3
- you want canonical JSON output under a normalized prefix
- you want to verify multi-format parsing behavior without going through the HTTP API

## 11. Automated testing

The test suite lives in [tests/](../tests).

Run it with:

```powershell
python -m pytest
```

Important implementation detail: the tests are designed to run offline.

- AWS dependencies are mocked with `moto`
- database tests use in-memory SQLite or isolated test fixtures

That means you usually do not need a running Docker stack to run the tests.

Useful test files:

- [tests/test_api.py](../tests/test_api.py)
- [tests/test_format_parser_registry.py](../tests/test_format_parser_registry.py)
- [tests/test_schema_validation.py](../tests/test_schema_validation.py)
- [tests/test_s3_normalization_service.py](../tests/test_s3_normalization_service.py)

## 12. How to add a new source

This repository is designed so most source onboarding is configuration-driven.

### Minimum path

1. Add the source to [metadata/sources.yaml](../metadata/sources.yaml).
2. Add the JSON Schema under [schemas/](../schemas).
3. Add or update validation metadata in [metadata/validation.yaml](../metadata/validation.yaml) if needed.
4. Add routing information in [metadata/routing.yaml](../metadata/routing.yaml) if the defaults should differ.
5. Add a stream definition in [metadata/streams.yaml](../metadata/streams.yaml) if a new logical stream is required.
6. Add a mapping in [metadata/mappings.yaml](../metadata/mappings.yaml) if the source should populate a dedicated curated table instead of `metadata.raw_events`.
7. Restart the ingestion service so routes are rebuilt from metadata.

### When code changes are required

You do need code changes if:

- the new source needs a brand-new curated table and curator
- the format requires a parser not already supported in [ingestion-service/parser/format_parser_registry.py](../ingestion-service/parser/format_parser_registry.py)
- the runtime needs a new AWS dependency or a new downstream sink

## 13. Observability and support surfaces

### Health endpoints

- `GET /api/v1/health` returns aggregate dependency health
- `GET /api/v1/ready` returns application readiness

Those are implemented in [ingestion-service/api/health_routes.py](../ingestion-service/api/health_routes.py).

### Config inspection endpoints

- `GET /api/v1/config/sources`
- `GET /api/v1/config/streams`
- `GET /api/v1/config/data-categories`

Those are implemented in [ingestion-service/api/config_routes.py](../ingestion-service/api/config_routes.py).

### Logging

The service configures structured logging through [common/logger/logger.py](../common/logger/logger.py) and [config/logging.yaml](../config/logging.yaml).

When troubleshooting a request, inspect the ingestion-service container logs first:

```powershell
docker compose logs ingestion-service --tail=200
```

## 14. Troubleshooting guide

### `docker compose up` fails because a port is already in use

Symptoms:

- Compose exits during startup
- container shows bind errors for `5432`, `5050`, `8000`, `9090`, or `3000`

What to do:

1. Stop the conflicting local service.
2. Or change the host-side port mapping in [docker-compose.yml](../docker-compose.yml).
3. Restart Compose.

### `/api/v1/ready` works but `/api/v1/health` returns 503

What it means:

- the FastAPI process is up
- one or more dependencies are down

What to check:

1. `curl.exe http://localhost:8000/api/v1/health`
2. `docker compose ps`
3. `docker compose logs postgres --tail=200`
4. verify AWS credentials with `aws --profile agent-toolkit sts get-caller-identity`

Common causes:

- PostgreSQL not healthy yet
- required S3/Kinesis resources are missing in AWS
- wrong environment values for `DATABASE_URL`, `AWS_REGION`, or `AWS_PROFILE`

### Ingestion returns HTTP 400

Common causes:

- malformed JSON, XML, or CSV
- payload does not match the source schema
- wrong `Content-Type`
- wrong source endpoint

What to do:

1. Compare the payload to the matching sample under [sample-data/](../sample-data).
2. Inspect the matching schema under [schemas/](../schemas).
3. Check the source `input_format` in [metadata/sources.yaml](../metadata/sources.yaml).

### S3 or Kinesis checks fail in AWS

What to check:

1. verify your session with `aws --profile agent-toolkit sts get-caller-identity`
2. verify the resources exist in the configured region
3. re-check the stream names in [metadata/streams.yaml](../metadata/streams.yaml)
4. make sure the bucket name matches [.env](../.env) and [config/aws.yaml](../config/aws.yaml)

### Host-based local run cannot import modules

Symptoms:

- errors importing `api`, `services`, or `common`

Cause:

- both the repository root and [ingestion-service/](../ingestion-service) need to be on `PYTHONPATH`

Fix:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\ingestion-service"
```

### Host-based local run cannot connect to PostgreSQL

What to check:

1. Make sure PostgreSQL is running: `docker compose ps`
2. Make sure `DATABASE_URL` points to `localhost`, not `postgres`, for host-based runs
3. Test the connection:

   ```powershell
   docker compose exec -T postgres psql -U sap_user -d semiconductor -c "SELECT 1;"
   ```

### Native file normalization produces zero outputs

What to check:

1. confirm files exist under the source prefix in S3
2. confirm `--source-prefix` and `--normalized-prefix` values
3. confirm the source exists in [metadata/sources.yaml](../metadata/sources.yaml)
4. inspect parser support in [ingestion-service/parser/format_parser_registry.py](../ingestion-service/parser/format_parser_registry.py)

### Tests fail after dependency installation

What to check:

1. use Python 3.12
2. reinstall from [requirements.txt](../requirements.txt)
3. run a focused test first:

   ```powershell
   python -m pytest tests/test_api.py -q
   ```

## 15. What is currently scaffolded versus fully wired

Not every module in [common/](../common) is part of the synchronous ingestion path today.

These are already directly involved in the running path:

- config loading
- metadata registry
- logging
- AWS S3 wrapper
- AWS Kinesis wrapper
- repository layer
- validation

These are present as lightweight platform scaffolds for later phases:

- [common/governance/governance_service.py](../common/governance/governance_service.py)
- [common/storage/lakehouse_service.py](../common/storage/lakehouse_service.py)
- [common/traceability/traceability_service.py](../common/traceability/traceability_service.py)
- [common/orchestration/agent_service.py](../common/orchestration/agent_service.py)
- [common/ai/intelligence_service.py](../common/ai/intelligence_service.py)

That distinction is important for new developers: the codebase already contains platform direction beyond ingestion, but the local runnable core is the ingestion pipeline plus its local infrastructure.

## 16. Recommended first-day walkthrough for a new developer

If you are handing this repository to a new engineer, this order works well:

1. Read [README.md](../README.md).
2. Read [docs/architecture.md](architecture.md).
3. Read [metadata/sources.yaml](../metadata/sources.yaml) to understand the platform's source model.
4. Read [ingestion-service/main.py](../ingestion-service/main.py) and [ingestion-service/api/routes.py](../ingestion-service/api/routes.py).
5. Start the full local stack with Docker Compose.
6. Open Swagger and inspect the generated endpoints.
7. Post the MES sample payload.
8. Verify the result in S3, Kinesis, and PostgreSQL.
9. Run [scripts/verify_pipeline.ps1](../scripts/verify_pipeline.ps1).
10. Run `python -m pytest`.

After that, the repository structure and runtime model usually become much easier to navigate.
