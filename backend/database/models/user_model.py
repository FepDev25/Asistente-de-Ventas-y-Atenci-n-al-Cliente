"""
Modelo de Base de Datos: User
Usuarios del sistema de ventas
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    # ID y Tiempos
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("now()")
    )

    # Información del Usuario
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Seguridad
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Rol del sistema
    # 1 = Admin | 2 = Cliente
    role: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("2")
    )

    # Estado
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
