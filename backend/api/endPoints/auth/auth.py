from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, or_

from backend.database.session import get_session
from backend.database.models.user_model import User
from backend.config.security.securityJWT import verify_password, create_access_token
from backend.api.endPoints.auth.shemas import Token as TokenSchema

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest):
    """Inicia sesión con `username` o `email` y `password`. Devuelve un token JWT."""

    # Validación básica de entrada
    if not (credentials.username or credentials.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere 'username' o 'email' junto con 'password'",
        )

    async with get_session() as session:
        query = select(User).where(
            or_(User.username == credentials.username, User.email == credentials.email)
        )
        result = await session.execute(query)
        user: User | None = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Construir payload seguro para el token
        user_payload = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": int(user.role),
        }

        token = create_access_token({}, user_payload)

        return TokenSchema(access_token=token)
