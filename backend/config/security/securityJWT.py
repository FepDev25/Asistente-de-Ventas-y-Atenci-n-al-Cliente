from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from backend.config.security.config import settings


def hash_password(password: str) -> str:
    """
    Hash de contraseña usando bcrypt directamente.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash de bcrypt como string
    """
    # bcrypt requiere bytes
    password_bytes = password.encode('utf-8')
    
    # bcrypt tiene limite de 72 bytes
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generar salt y hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifica contraseña usando bcrypt directamente.
    
    Args:
        password: Contraseña en texto plano
        hashed: Hash almacenado (desde hash_password)
        
    Returns:
        True si coincide, False si no
    """
    try:
        password_bytes = password.encode('utf-8')
        
        # bcrypt tiene limite de 72 bytes
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        hashed_bytes = hashed.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, user: dict) -> str:
    """Crea un token JWT con los datos del usuario y tiempo de expiracion."""
    to_encode = user.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
