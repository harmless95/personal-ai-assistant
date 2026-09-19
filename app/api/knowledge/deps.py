from typing import Annotated

from fastapi import Depends

from app.knowledge import KnowledgeGrpcClient, get_knowledge_client

KnowledgeClientDep = Annotated[KnowledgeGrpcClient, Depends(get_knowledge_client)]
