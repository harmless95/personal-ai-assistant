from fastapi import APIRouter, status

from app.api.auth.deps import (
    AuthServiceDep,
    AuthUserDep,
    CurrentUserDep,
    LogoutTokenDep,
    RefreshTokenValidatedDep,
)
from app.api.auth.models.token import TokenResponse
from app.api.auth.models.user import RegisterRequest, RegisterResponse, StatusResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
)
async def register(
    register_request: RegisterRequest,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.register_new_user(
        register_request=register_request,
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def login(
    user: AuthUserDep,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    return await auth_service.get_tokens(
        user_id=user.id,
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def get_current_user(
    current_user: CurrentUserDep,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=StatusResponse,
)
async def logout(
    _: LogoutTokenDep,
) -> StatusResponse:
    return StatusResponse(detail="Successfully logged out")


@router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
)
async def refresh_access(
    refresh_token: RefreshTokenValidatedDep,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    return await auth_service.refresh_access(
        refresh_token=refresh_token,
    )
