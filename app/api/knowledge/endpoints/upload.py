from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.auth.deps import CurrentUserDep
from app.api.knowledge.deps import KnowledgeClientDep
from app.api.knowledge.models.ingest import IngestFileResponse
from app.config import settings
from app.knowledge import KnowledgeIngestError

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload/", response_model=IngestFileResponse)
async def upload_knowledge_file(
    current_user: CurrentUserDep,
    knowledge_client: KnowledgeClientDep,
    file: UploadFile = File(...),
    source: str | None = Form(default=None),
) -> IngestFileResponse:
    _ = current_user
    content = await file.read()
    max_upload_bytes = settings.knowledge.max_upload_bytes
    if len(content) > max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"file exceeds {max_upload_bytes} bytes",
        )

    resolved_source = (source or file.filename or "").strip()
    if not resolved_source:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="source or filename is required",
        )

    content_type = (file.content_type or "text/plain").strip() or "text/plain"
    try:
        result = await knowledge_client.ingest_file(
            content,
            source=resolved_source,
            content_type=content_type,
        )
    except KnowledgeIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return IngestFileResponse(
        chunks_saved=result.chunks_saved,
        s3_key=result.s3_key,
        source=resolved_source,
    )
