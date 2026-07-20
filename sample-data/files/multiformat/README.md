# Multi-Format Sample Payloads

These files are sample request payloads for:

- `POST /api/v1/files/multiformat/events`

Coverage includes one sample for each supported data category:

- telemetry (`Protobuf`)
- system_health (`JSON`)
- logs (`Syslog`)
- events (`Kafka`)
- configuration (`YAML`)
- performance (`Parquet`)
- validation (`HDF5`)
- environmental (`MQTT`)
- design (`Verilog`)
- manufacturing (`SECS/GEM`)

All files in this folder ending with `_sample.json` are automatically validated by `tests/test_schema_validation.py`.
