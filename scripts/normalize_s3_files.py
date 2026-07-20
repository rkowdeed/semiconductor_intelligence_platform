#!/usr/bin/env python3
"""Normalize S3 raw files (xml/csv/text/parquet/etc.) into JSON objects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = REPO_ROOT / "ingestion-service"
for candidate in (REPO_ROOT, SERVICE_ROOT):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from common.aws.s3_client import S3Client
from common.config.metadata_registry import MetadataRegistry
from services.s3_normalization_service import S3NormalizationService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize raw files in S3 into JSON objects for downstream processing."
    )
    parser.add_argument("--source", required=True, help="Source name from metadata/sources.yaml")
    parser.add_argument("--bucket", help="Override bucket name (defaults to source raw_bucket)")
    parser.add_argument(
        "--source-prefix",
        help="Override source prefix (defaults to source raw_prefix)",
    )
    parser.add_argument(
        "--normalized-prefix",
        help="Target prefix for normalized JSON objects (default: <source-prefix>/normalized)",
    )
    parser.add_argument(
        "--format",
        dest="source_format",
        help="Optional fallback input format when extension is unknown",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of objects to normalize")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = MetadataRegistry()
    source = registry.get_source(args.source)

    bucket = args.bucket or source.raw_bucket
    source_prefix = args.source_prefix or source.raw_prefix
    normalized_prefix = args.normalized_prefix or f"{source_prefix.rstrip('/')}/normalized"

    service = S3NormalizationService(S3Client())
    normalized_keys = service.normalize_prefix(
        bucket=bucket,
        source_prefix=source_prefix,
        normalized_prefix=normalized_prefix,
        source_format=args.source_format or source.input_format,
        limit=args.limit,
    )

    print(
        json.dumps(
            {
                "source": args.source,
                "bucket": bucket,
                "source_prefix": source_prefix,
                "normalized_prefix": normalized_prefix,
                "normalized_count": len(normalized_keys),
                "normalized_keys": normalized_keys,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
