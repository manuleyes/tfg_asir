"""
Middleware - Validación de JWT con fallback a session cookie
"""
from fastapi import Depends, HTTPException, status, Request
from auth.jwt_handler import decode_access_token
from auth.session_handler import validate_session_cookie, SESSION_COOKIE_NAME
from itsdangerous import BadSignature, SignatureExpired
from typing import Optional, Dict

def get_token_from_request(request: Request) -> Optional[str]:
    """Extraer JWT token del header Authorization"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def get_current_user(request: Request) -> Dict:
    """
    Dependency para validar identidad.
    Acepta JWT Bearer token (header) O session cookie (navegador).
    """
    # 1. Intentar JWT Bearer
    token = get_token_from_request(request)
    if token:
        payload = decode_access_token(token)
        if payload is not None:
            return payload

    # 2. Fallback: session cookie (dashboard del navegador)
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        try:
            session_data = validate_session_cookie(session_cookie)
            if session_data:
                return session_data
        except (BadSignature, SignatureExpired):
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado. Proporciona un token Bearer o inicia sesión.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Dependency para validar que el usuario sea admin
    
    Args:
        current_user: Usuario actual del JWT
        
    Returns:
        Datos del usuario si es admin
        
    Raises:
        HTTPException 403 si no es admin
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    
    return current_user
