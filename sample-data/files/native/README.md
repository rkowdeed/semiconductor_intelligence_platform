# Native Source File Samples

These are native-format sample files for testing normalization into JSON via:

- scripts/normalize_s3_files.py
- ingestion-service/services/s3_normalization_service.py

Files:

- system_health_sample.xml
- work_orders_sample.csv
- driver_logs_sample.txt
- benchmark_sample.parquet

Note: `benchmark_sample.parquet` is a placeholder blob to validate fallback behavior when `pyarrow` is unavailable.
