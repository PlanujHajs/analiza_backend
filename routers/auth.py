from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import UserCreate, UserLogin, UserRead, Token
from services.auth_service import UserRepository, AuthService, ChangePassword
from security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.register_user(user_data)


@router.post(
    "/login",
    response_model=Token,
)
async def login_user_json(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.authenticate_user(user_data.email, user_data.password)


@router.post(
    "/token",
    response_model=Token,
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.authenticate_user(form_data.username, form_data.password)


@router.get(
    "/users/me",
    response_model=UserRead,
   
)
async def read_users_me(current_user=Depends(get_current_user)):
    return UserRead.from_orm(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
   )
async def change_password(
    change_data: ChangePassword,
    current_user=Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.change_password(current_user, change_data)
    return