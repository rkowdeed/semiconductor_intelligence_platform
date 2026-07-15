"""Health and readiness endpoints.

GET /health reports the status of every downstream dependency (database,
localstack, kinesis, s3, application) so operators and orchestrators can
make informed decisions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db_session, get_kinesis_publisher, get_s3_client
from common.aws.kinesis_publisher import KinesisPublisher
from common.aws.s3_client import S3Client
from models.schemas import HealthComponent, HealthResponse

router = APIRouter(tags=["health"])


def _check_database(session: Session) -> HealthComponent:
    try:
        session.execute(text("SELECT 1"))
        return HealthComponent(status="UP")
    except Exception as exc:  # noqa: BLE001 - health checks must not raise
        return HealthComponent(status="DOWN", detail=str(exc))


def _check_s3(s3_client: S3Client) -> HealthComponent:
    return HealthComponent(status="UP" if s3_client.healthcheck() else "DOWN")


def _check_kinesis(kinesis_publisher: KinesisPublisher) -> HealthComponent:
    return HealthComponent(status="UP" if kinesis_publisher.healthcheck() else "DOWN")


@router.get("/health", response_model=HealthResponse, summary="Aggregate health check")
def health(
    response: Response,
    session: Session = Depends(get_db_session),
    s3_client: S3Client = Depends(get_s3_client),
    kinesis_publisher: KinesisPublisher = Depends(get_kinesis_publisher),
) -> HealthResponse:
    database_component = _check_database(session)
    s3_component = _check_s3(s3_client)
    kinesis_component = _check_kinesis(kinesis_publisher)
    # localstack is considered healthy if either AWS-facing dependency
    # backed by it responds
    localstack_status = (
        "UP" if s3_component.status == "UP" or kinesis_component.status == "UP" else "DOWN"
    )

    components = {
        "database": database_component,
        "localstack": HealthComponent(status=localstack_status),
        "kinesis": kinesis_component,
        "s3": s3_component,
        "application": HealthComponent(status="UP"),
    }

    overall = "UP" if all(c.status == "UP" for c in components.values()) else "DOWN"
    if overall != "UP":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(status=overall, components=components)


@router.get("/ready", summary="Readiness probe")
def ready() -> dict[str, str]:
    return {"status": "READY"}
