from pydantic import BaseModel, Field


class IngestFileResponse(BaseModel):
    chunks_saved: int = Field(ge=0)
    s3_key: str
    source: str
