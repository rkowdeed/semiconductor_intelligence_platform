"""FastAPI application entrypoint for the Ingestion Service.

Run locally with:

    uvicorn main:app --reload --port 8000

(from within the ingestion-service directory, with the repository root and
this directory both on PYTHONPATH - see infrastructure/docker/Dockerfile).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config_routes import router as config_router
from api.dependencies import get_metadata_registry
from api.exception_handlers import register_exception_handlers
from api.health_routes import router as health_router
from api.middleware import RequestLoggingMiddleware
from api.routes import build_ingestion_router
from api.ui_routes import router as ui_router
from common.config.loader import config_loader
from common.logger.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app_config = config_loader.load("config/application.yaml")["app"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = get_metadata_registry()
    enabled_sources = [s.name for s in registry.get_sources().values() if s.enabled]
    logger.info("ingestion_service_started", enabled_sources=enabled_sources)
    yield


app = FastAPI(
    title=app_config["api"]["title"],
    description=app_config["api"]["description"],
    version=app_config["version"],
    docs_url=app_config["api"]["docs_url"],
    redoc_url=app_config["api"]["redoc_url"],
    openapi_url=app_config["api"]["openapi_url"],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config["cors"]["allow_origins"],
    allow_methods=app_config["cors"]["allow_methods"],
    allow_headers=app_config["cors"]["allow_headers"],
)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

api_base_url = app_config["api"]["base_url"]

app.include_router(health_router, prefix=api_base_url)
app.include_router(config_router, prefix=api_base_url)
app.include_router(ui_router)
app.include_router(build_ingestion_router(), prefix=api_base_url)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "service": app_config["name"],
        "version": app_config["version"],
        "docs": app_config["api"]["docs_url"],
    }
