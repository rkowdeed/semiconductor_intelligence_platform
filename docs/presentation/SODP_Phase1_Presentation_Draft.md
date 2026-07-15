# Semiconductor_Operations_Data_Platform (SODP) - Phase 1
## Metadata-Driven Ingestion for Semiconductor Manufacturing

- AWS-native local stack: FastAPI + PostgreSQL + S3 + Kinesis
- Ingests MES, ERP, Equipment, and PLM events
- Validates payloads, stores raw data, publishes streams, persists curated records
- Built for source onboarding by configuration, not endpoint code changes
- Owner: ravikanth.kowdeed@gmail.com

---

# Agenda

- Business context and problem statement
- Platform goals and architecture
- Source systems in semiconductor
- End-to-end ingestion flow
- Data model and lineage
- Deployment, APIs, and operations
- Testing, verification, and demo flow
- Current status and next steps

---

# Business Context

- Semiconductor manufacturing depends on strict process control, traceability, and rapid issue response
- Factory and enterprise data are typically fragmented across systems
- Common challenge: integrating new source systems without repeatedly changing service code

Outcome needed:
- Reliable ingestion framework with validation, observability, and metadata-driven extensibility

---

# Platform Goals

- Standardize ingestion for critical manufacturing and enterprise systems
- Ensure schema-driven quality gates before downstream persistence
- Maintain dual persistence pattern:
  - Raw payload durability in S3
  - Curated operational records in PostgreSQL
- Publish events to Kinesis for asynchronous downstream consumers

---

# Source Systems in Semiconductor

MES (Manufacturing Execution System)
- Tracks wafer lot movement and process execution in real time
- Enforces route and recipe discipline for yield and traceability

Equipment systems
- Tool telemetry and state events (alarms, status changes, context)
- Critical for uptime, excursion detection, and root-cause analysis

ERP (Enterprise Resource Planning)
- Work orders, planning, inventory, procurement, fulfillment alignment
- Connects fab execution with business demand and cost controls

PLM (Product Lifecycle Management)
- Product definitions, BOM/revisions, lifecycle state and ECO/ECR control
- Ensures manufacturing follows approved engineering intent

---

# Why Integrate All Four

- MES + Equipment: execution truth and process behavior
- ERP: supply-demand-business alignment
- PLM: engineering and configuration correctness

Together:
- End-to-end traceability from engineering change to production to delivery
- Better yield protection, faster cycle-time decisions, lower operational risk

---

# Architecture Overview

Incoming REST Request
- Load metadata from metadata/sources.yaml
- Load schema from schemas/source
- Validate payload (400 on failure)
- Persist raw payload to S3 (LocalStack)
- Publish event to Kinesis (LocalStack)
- Insert curated record into PostgreSQL
- Return HTTP 202 Accepted

---

# Metadata-Driven Design

Core metadata files:
- metadata/sources.yaml
- metadata/mappings.yaml
- metadata/routing.yaml
- metadata/validation.yaml
- metadata/streams.yaml

Principle:
- New source onboarding is primarily metadata and schema updates
- Minimal to no endpoint-handler code changes required

---

# Technology Stack

- Python 3.12
- FastAPI + Uvicorn
- Pydantic v2 + jsonschema
- SQLAlchemy 2.x + Alembic
- PostgreSQL 16
- LocalStack S3 + Kinesis
- Boto3
- structlog (JSON logging)
- pytest + moto + httpx
- Prometheus + Grafana
- Docker + Docker Compose

---

# Repository Structure (High Level)

- config: runtime YAML configuration
- metadata: source/routing/validation/stream definitions
- schemas: per-source JSON schemas
- sample-data: test payloads
- common: shared components (models, validation, storage, aws, repository)
- ingestion-service: API service implementation
- scripts/sql/init.sql: DB bootstrap
- infrastructure/localstack/init-aws.sh: S3/Kinesis bootstrap
- tests: offline-capable pytest suite

---

# Runtime Services and Ports

- Ingestion API: http://localhost:8000/api/v1
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- LocalStack: http://localhost:4566
- PostgreSQL: localhost:5432
- pgAdmin: http://localhost:5050
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

# API Endpoints by Source

Ingestion endpoints:
- POST /api/v1/mes/events
- POST /api/v1/erp/events
- POST /api/v1/equipment/events
- POST /api/v1/plm/events

Operational endpoints:
- GET /api/v1/health
- GET /api/v1/ready
- GET /api/v1/config/sources
- GET /api/v1/config/streams

---

# Example Ingestion Response (202)

- request_id
- source
- status = ACCEPTED
- s3_key
- stream
- sequence_number
- curated_record_id

Value:
- Immediate operational acknowledgement
- IDs for lineage tracing across storage and streaming

---

# Validation and Error Handling

- Payloads are validated per-source using JSON Schema
- Validation failure returns HTTP 400 with structured errors
- Malformed JSON also returns HTTP 400
- Health endpoint returns component-level statuses and can return 503 when dependencies fail

---

# PostgreSQL Data Model

Schemas:
- mdm
- metadata
- quality (reserved for future use)

Primary tables:
- mdm.lot_master: curated MES rows
- metadata.raw_events: generic curated rows for ERP/Equipment/PLM
- metadata.ingestion_log: request-level audit log

---

# Table Relationships and Lineage

Current model uses logical relationships (lineage keys), not strict FK constraints.

Logical linkage signals:
- request_id
- source
- stream
- s3_key
- time ordering

View:
- metadata.v_ingestion_lineage
- Normalizes request-to-curated mapping for analysis and operations

---

# Storage and Streaming Strategy

S3
- Durable raw payload retention by source prefix
- Supports replay and forensic analysis

Kinesis
- Event fan-out to downstream consumers
- Streams:
  - mes-events
  - metadata-events
  - quality-events
  - plm-events

---

# Verification and Operational Scripts

- scripts/verify_pipeline.ps1
  - Supports all-source verification mode
  - Can ingest samples and validate API, S3, Kinesis, and Postgres
  - Auto-writes results to docs/end_to_end_test_result.md

- scripts/sql/postgres_table_queries.sql
  - Counts, recent rows, lineage queries

- scripts/sql/postgres_delete_rows.sql
- scripts/sql/postgres_insert_rows.sql

---

# Testing Strategy

- Offline-friendly tests with moto and in-memory SQLite
- Coverage includes:
  - schema validation
  - API success and failure paths
  - repository behavior
  - S3 and Kinesis integration abstractions
  - configuration loading

Operational testing also available via dockerized runtime checks.

---

# Demo Flow (Recommended)

- Start stack: docker compose up --build
- Open docs UI: /docs
- Post sample events for MES, ERP, Equipment, PLM
- Verify S3 objects by source prefix
- Read Kinesis records per stream
- Query PostgreSQL tables and metadata.v_ingestion_lineage
- Run end-to-end verifier and review markdown report

---

# Business and Technical Value

- Faster source onboarding with lower engineering effort
- Strong data quality gate at ingress
- Unified observability and health status
- Better traceability for yield and compliance investigations
- Reusable platform pattern for future semiconductor services

---

# Current Status

- Endpoints active for MES, ERP, Equipment, PLM
- Source-specific sample payloads and schema validation in place
- LocalStack streams and S3 buckets provisioned
- Postgres lineage view implemented and queryable
- End-to-end verification script passing

---

# Future Roadmap

- Add stricter relational keys or optional FK strategy if required
- Introduce data quality service in quality schema
- Add semantic layer and catalog integration
- Extend with MDM and knowledge graph capabilities
- Add AI-assisted anomaly triage and operational copilots

---

# Appendix: Useful Commands

Start stack
- docker compose up --build

Run all-source verification
- .\scripts\verify_pipeline.ps1 -IngestAllSamples

Read Postgres query file
- Get-Content .\scripts\sql\postgres_table_queries.sql | docker compose exec -T postgres psql -U sap_user -d semiconductor

Read Kinesis (example)
- Use stream-specific shard iterator flow with awslocal kinesis get-records
