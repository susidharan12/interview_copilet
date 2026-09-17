from __future__ import annotations

import uuid
from typing import IO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import parse_obj_as

from app.api.deps import DbSession
from app.models.models import Document
from app.schemas.document import DocumentIngestResponse, DocumentOut
from app.services.retrieval.indexer import ChunkIndexer, EmbeddingService
from app.services.retrieval.retrieval_chunk import chunk_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    db: DbSession,
    file: UploadFile = File(...),
    document_type: str = Form("other"),
    tags: str = Form(""),
    project_name: str | None = Form(None),
) -> DocumentOut:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    doc = Document(
        filename=file.filename or "unnamed",
        document_type=document_type,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        project_name=project_name,
        content=content.decode("utf-8", errors="replace")[:200_000],
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(document_id: uuid.UUID, db: DbSession) -> DocumentIngestResponse:
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "processing"
    await db.commit()

    try:
        chunks = chunk_document(doc.content or "", meta={"document_type": doc.document_type})
        indexer = ChunkIndexer(db, EmbeddingService())
        count = await indexer.index(
            document_id=doc.id,
            chunks=chunks,
            metadata_template={
                "document_id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type,
                "project": doc.project_name,
                "tags": doc.tags,
            },
        )
        doc.chunk_count = count
        doc.status = "ready"
        await db.commit()
        return DocumentIngestResponse(document_id=doc.id, status="ready", chunk_count=count, queued=False)
    except Exception as exc:
        doc.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc