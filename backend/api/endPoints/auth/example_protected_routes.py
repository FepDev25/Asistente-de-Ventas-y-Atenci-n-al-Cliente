"""
EJEMPLO: Cómo proteger endpoints con autenticación JWT.

Este archivo muestra ejemplos de uso de las dependencias de autenticación.
NO es necesario incluir este router en main.py - es solo referencia.
"""
from fastapi import APIRouter, Depends
from backend.config.security.dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_client
)

router = APIRouter(prefix="/example", tags=["examples"])


@router.get("/public")
async def public_route():
    """Ruta pública - NO requiere autenticación."""
    return {"message": "Esta ruta es pública, cualquiera puede acceder"}


@router.get("/protected-basic")
async def protected_basic(current_user: dict = Depends(get_current_user)):
    """
    Ruta protegida - requiere token JWT válido.
    Usa get_current_user para validar solo el token (no verifica BD).
    """
    return {
        "message": "Acceso autorizado",
        "user_id": current_user["id"],
        "username": current_user["username"],
        "role": current_user["role"]
    }


@router.get("/protected-active")
async def protected_active(current_user: dict = Depends(get_current_active_user)):
    """
    Ruta protegida - requiere token JWT válido Y usuario activo en BD.
    Usa get_current_active_user para validar token + verificar is_active.
    """
    return {
        "message": f"Hola {current_user['username']}, tu cuenta está activa",
        "email": current_user["email"]
    }


@router.get("/admin-only")
async def admin_only(admin: dict = Depends(require_admin)):
    """
    Ruta solo para administradores (role = 1).
    Retorna 403 Forbidden si el usuario no es admin.
    """
    return {
        "message": "Panel de administración",
        "admin_username": admin["username"],
        "secret_data": "Información confidencial solo para admins"
    }


@router.get("/client-only")
async def client_only(client: dict = Depends(require_client)):
    """
    Ruta solo para clientes (role = 2).
    Retorna 403 Forbidden si el usuario no es cliente.
    """
    return {
        "message": "Panel de cliente",
        "client_username": client["username"],
        "recommendations": ["Producto A", "Producto B", "Producto C"]
    }


@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_active_user)):
    """
    Obtiene el perfil del usuario autenticado.
    Patrón común para endpoints tipo "/me".
    """
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": "admin" if current_user["role"] == 1 else "client"
    }


# EJEMPLO DE USO EN TU CÓDIGO:
#
# 1. Para proteger un endpoint de GraphQL:
#    from backend.config.security.dependencies import get_current_active_user
#
#    @router.post("/graphql")
#    async def graphql_endpoint(
#        current_user: dict = Depends(get_current_active_user),
#        query: str
#    ):
#        # El usuario ya está autenticado aquí
#        return process_graphql(query, user=current_user)
#
# 2. Para crear un endpoint de perfil:
#    @router.put("/profile")
#    async def update_profile(
#        data: ProfileUpdate,
#        current_user: dict = Depends(get_current_active_user)
#    ):
#        # Solo el usuario autenticado puede actualizar su perfil
#        return update_user_profile(current_user["id"], data)
#
# 3. Para crear un endpoint administrativo:
#    @router.delete("/users/{user_id}")
#    async def delete_user(
#        user_id: str,
#        admin: dict = Depends(require_admin)
#    ):
#        # Solo admins pueden eliminar usuarios
#        return delete_user_from_db(user_id)
