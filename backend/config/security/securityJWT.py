from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from backend.config.security.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash de contraseña con truncamiento a 72 bytes para bcrypt."""
    # bcrypt tiene límite de 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verifica contraseña con truncamiento a 72 bytes para bcrypt."""
    # bcrypt tiene límite de 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict, user: dict) -> str:
    """Crea un token JWT con los datos del usuario y tiempo de expiración."""
    to_encode = user.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
