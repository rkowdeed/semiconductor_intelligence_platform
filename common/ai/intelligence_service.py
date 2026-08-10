"""Prototype AI intelligence scaffold for RAG-style search over indexed documents."""

from __future__ import annotations

from typing import Any


class IntelligenceService:
    """Stores and searches lightweight document embeddings in memory."""

    def __init__(self) -> None:
        self._documents: list[dict[str, Any]] = []

    def index_document(self, *, title: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        document = {
            "title": title,
            "content": content,
            "metadata": metadata or {},
        }
        self._documents.append(document)
        return document

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        normalized = query.lower()
        scored = []
        for document in self._documents:
            content = document["content"].lower()
            score = 1 if normalized in content else 0
            if score > 0:
                scored.append({"score": score, "document": document})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]
