from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models import User
from schemas import UserCreate, Token, UserRead, ChangePassword
from security import get_password_hash, verify_password, create_access_token
from config import settings


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, user_create: UserCreate, hashed_password: str) -> User:
        new_user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        self.session.add(new_user)
        try:
            await self.session.commit()
            await self.session.refresh(new_user)
        except IntegrityError:
            await self.session.rollback()
            raise
        return new_user

    async def update_password(self, user: User, new_hashed_password: str) -> User:
        user.hashed_password = new_hashed_password
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd podczas aktualizacji hasła."
            )
        return user


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_create: UserCreate) -> UserRead:
        existing = await self.user_repo.get_by_email(user_create.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Użytkownik o tym adresie e-mail już istnieje."
            )

        hashed_pw = get_password_hash(user_create.password)
        try:
            user = await self.user_repo.create(user_create, hashed_pw)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nie udało się utworzyć konta."
            )

        return UserRead.from_orm(user)

    async def authenticate_user(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidłowy e-mail lub hasło.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return Token(access_token=access_token, token_type="bearer")

    async def change_password(
            self,
            current_user: User,
            change_data: ChangePassword
        ) -> None:
           
            if not verify_password(change_data.old_password, current_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stare hasło jest niepoprawne."
                )

            new_hashed = get_password_hash(change_data.new_password)

            await self.user_repo.update_password(current_user, new_hashed)

            return