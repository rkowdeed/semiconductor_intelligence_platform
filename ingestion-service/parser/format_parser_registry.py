"""Pluggable raw format parsers used to normalize inbound payloads to dict."""

from __future__ import annotations

import base64
import csv
import io
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Protocol

import yaml

from common.exceptions.exceptions import ValidationException


class RawFormatParser(Protocol):
    def parse_bytes(self, raw_body: bytes) -> dict:
        ...


class JsonFormatParser:
    def parse_bytes(self, raw_body: bytes) -> dict:
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationException(f"Request body is not valid JSON: {exc}") from exc

        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}


class XmlFormatParser:
    @staticmethod
    def _element_to_dict(element: ET.Element):
        children = list(element)
        has_children = len(children) > 0

        if not has_children:
            text = (element.text or "").strip()
            if element.attrib:
                result = {"@attributes": dict(element.attrib)}
                if text:
                    result["#text"] = text
                return result
            return text

        result: dict[str, object] = {}
        if element.attrib:
            result["@attributes"] = dict(element.attrib)

        for child in children:
            child_value = XmlFormatParser._element_to_dict(child)
            if child.tag in result:
                existing = result[child.tag]
                if isinstance(existing, list):
                    existing.append(child_value)
                else:
                    result[child.tag] = [existing, child_value]
            else:
                result[child.tag] = child_value

        text = (element.text or "").strip()
        if text:
            result["#text"] = text
        return result

    def parse_bytes(self, raw_body: bytes) -> dict:
        try:
            root = ET.fromstring(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, ET.ParseError) as exc:
            raise ValidationException(f"Request body is not valid XML: {exc}") from exc
        return {root.tag: self._element_to_dict(root)}


class CsvFormatParser:
    def parse_bytes(self, raw_body: bytes) -> dict:
        try:
            text = raw_body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationException(f"Request body is not valid UTF-8 CSV: {exc}") from exc

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValidationException("CSV body is missing a header row")

        rows = list(reader)
        return {"columns": reader.fieldnames, "rows": rows, "row_count": len(rows)}


class YamlFormatParser:
    def parse_bytes(self, raw_body: bytes) -> dict:
        try:
            parsed = yaml.safe_load(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            raise ValidationException(f"Request body is not valid YAML: {exc}") from exc

        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}


class TextFormatParser:
    def parse_bytes(self, raw_body: bytes) -> dict:
        try:
            return {"text": raw_body.decode("utf-8")}
        except UnicodeDecodeError as exc:
            raise ValidationException(f"Request body is not valid UTF-8 text: {exc}") from exc


class BinaryPassthroughParser:
    def parse_bytes(self, raw_body: bytes) -> dict:
        return {"content_base64": base64.b64encode(raw_body).decode("ascii")}


class ParquetFormatParser:
    def parse_bytes(self, raw_body: bytes) -> dict:
        try:
            import pyarrow.parquet as pq
        except ModuleNotFoundError:
            # Keep normalization usable without extra dependencies by
            # preserving parquet bytes in a canonical JSON envelope.
            return {
                "content_base64": base64.b64encode(raw_body).decode("ascii"),
                "parser": "binary_fallback",
                "format": "PARQUET",
            }

        try:
            table = pq.read_table(io.BytesIO(raw_body))
        except Exception as exc:
            raise ValidationException(f"Request body is not valid Parquet: {exc}") from exc

        rows = table.to_pylist()
        return {"columns": table.column_names, "rows": rows, "row_count": len(rows)}


@dataclass(frozen=True)
class ContentTypeMapping:
    content_type: str
    format_name: str


class FormatParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, RawFormatParser] = {
            "JSON": JsonFormatParser(),
            "XML": XmlFormatParser(),
            "CSV": CsvFormatParser(),
            "YAML": YamlFormatParser(),
            "TEXT": TextFormatParser(),
            "PARQUET": ParquetFormatParser(),
            "HDF5": BinaryPassthroughParser(),
            "PROTOBUF": BinaryPassthroughParser(),
            "AVRO": BinaryPassthroughParser(),
            "GRPC": BinaryPassthroughParser(),
            "STDF": BinaryPassthroughParser(),
            "SECS/GEM": BinaryPassthroughParser(),
            "OPC-UA": BinaryPassthroughParser(),
        }
        self._aliases: dict[str, str] = {
            "APPLICATION/JSON": "JSON",
            "TEXT/JSON": "JSON",
            "APPLICATION/XML": "XML",
            "TEXT/XML": "XML",
            "TEXT/CSV": "CSV",
            "TEXT/PLAIN": "TEXT",
            "APPLICATION/X-YAML": "YAML",
            "TEXT/YAML": "YAML",
            "APPLICATION/YAML": "YAML",
            "APPLICATION/OCTET-STREAM": "BINARY",
            "JSON": "JSON",
            "XML": "XML",
            "CSV": "CSV",
            "TEXT": "TEXT",
            "YAML": "YAML",
            "PARQUET": "PARQUET",
            "HDF5": "HDF5",
            "PROTOBUF": "PROTOBUF",
            "AVRO": "AVRO",
            "GRPC": "GRPC",
            "STDF": "STDF",
            "SECS/GEM": "SECS/GEM",
            "OPC-UA": "OPC-UA",
        }

    def _resolve_format(self, content_type: str | None, source_format: str | None) -> str:
        if source_format:
            normalized = self._aliases.get(source_format.strip().upper())
            if normalized:
                return normalized

        if not content_type:
            return "JSON"

        mime = content_type.split(";", 1)[0].strip().upper()
        normalized = self._aliases.get(mime)
        if normalized:
            return normalized

        return "JSON"

    def parse(
        self,
        raw_body: bytes | str | dict,
        *,
        content_type: str | None = None,
        source_format: str | None = None,
    ) -> dict:
        if isinstance(raw_body, dict):
            return raw_body
        if isinstance(raw_body, str):
            raw_bytes = raw_body.encode("utf-8")
        else:
            raw_bytes = raw_body

        resolved = self._resolve_format(content_type, source_format)
        if resolved == "BINARY":
            return BinaryPassthroughParser().parse_bytes(raw_bytes)

        parser = self._parsers.get(resolved)
        if not parser:
            raise ValidationException(f"Unsupported source format: {resolved}")
        return parser.parse_bytes(raw_bytes)


format_parser_registry = FormatParserRegistry()
