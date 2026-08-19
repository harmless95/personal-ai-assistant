from fastapi import APIRouter, status

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check", status_code=status.HTTP_200_OK)
async def check_health() -> bool:
    return True
