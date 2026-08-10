# Semiconductor Intelligence Platform (SIP)

A sovereign semiconductor intelligence platform for ingesting, governing, and analyzing manufacturing and engineering data. It combines metadata-driven ingestion, S3 lakehouse-style storage, PostgreSQL-backed intelligence, and AI-ready retrieval scaffolding.

## What this repository provides

- Multi-format ingestion for MES, ERP, equipment, PLM, telemetry, and yield payloads
- Metadata-driven validation and routing for new data sources
- S3-based raw landing and lakehouse-style asset cataloging
- Governance controls for IP-sensitive and restricted data
- Traceability links across lots, wafers, tools, and design versions
- AI/RAG-ready document indexing and search scaffolding

## Architecture at a glance

1. Source systems send events into the ingestion API.
2. The parser and validator normalize each payload and land it in the S3 raw bronze layer.
3. Transformation and loader jobs move data from bronze to silver and then from silver to gold.
4. The S3 gold layer publishes to AWS Kinesis / Kafka topics, and a data loader persists the curated operational records into PostgreSQL.
5. PostgreSQL-backed consumption is then exposed securely to governance, traceability, AI services, and human users.

### Secure AI and Human Consumption Reference Architecture

This reference view shows how Archimedes chip data and telemetry flow through S3 bronze, silver, and gold layers, then through AWS Kinesis / Kafka topics into PostgreSQL via a data loader before secure consumption by AI agents and human users.

```mermaid
flowchart TD
    A[Archimedes Server<br/>chip data + telemetry] --> B[Ingestion API]
    B --> C[Validation / Parsing]
    C --> D[S3 Bronze<br/>raw landing]
    D --> E[Bronze to Silver<br/>transformations / loaders]
    E --> F[S3 Silver<br/>refined layer]
    F --> G[Silver to Gold<br/>transformations / loaders]
    G --> H[S3 Gold<br/>curated layer]
    H --> I[AWS Kinesis / Kafka<br/>Topics]
    I --> J[PostgreSQL Data Loader]
    J --> K[Curated PostgreSQL]

    K --> L[Query / App API]
    L --> M[Authentication / Authorization]
    M --> N[Rate Limiter]
    N --> O[LLM Gateway<br/>for AI-agent access]
    N --> P[Human users / analysts]
    O --> Q[AI agents]
    O --> K

    K -. lineage / audit .-> R[Observability]
    L -. policy enforcement .-> S[Governance]
```

Notes:
- PostgreSQL remains the trusted curated data store for downstream consumption.
- S3 is organized into bronze, silver, and gold lakehouse layers, with dedicated transformations and loaders between them.
- AWS Kinesis / Kafka topics are fed from the S3 gold layer, and PostgreSQL is loaded from those topics through a data-loader tier.
- Human users consume through the secured API layer.
- AI agents consume through the LLM gateway path when prompt governance, guardrails, and model routing are required.
- The rate limiter applies at the shared consumption edge to protect both human and agent-driven workloads.

## Quick start

```bash
git clone <this-repo>
cd Semiconductor_Operations_Data_Platform
docker compose up --build
```

Once the services are up, use the Swagger UI at `http://localhost:8000/docs` or call the ingestion endpoints directly.

## Key services

| Service | Purpose |
| --- | --- |
| FastAPI ingestion API | Accepts and routes new events |
| S3 landing zone | Stores raw payloads for lakehouse workflows |
| PostgreSQL | Stores curated records and audit information |
| Governance and AI layers | Applies policy rules and supports retrieval-based intelligence |

## Test and validation

```powershell
./scripts/run_pytest.ps1 -q tests/test_api.py -k "validation_ui"
```

The repository includes sample payloads and smoke-test flows for telemetry, yield, and core ingestion paths.

## Project owner

ravikanth.kowdeed@gmail.com
