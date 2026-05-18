"""
middleware/session_middleware.py - Validación de sesiones
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from itsdangerous import BadSignature, SignatureExpired
import logging

from auth.session_handler import validate_session_cookie, SESSION_COOKIE_NAME

logger = logging.getLogger(__name__)


def get_session_from_request(request: Request) -> dict:
    """
    Extraer datos de sesión desde cookie de request
    
    Args:
        request: FastAPI Request
        
    Returns:
        dict con datos de sesión o None
    """
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    
    if not session_cookie:
        return None
    
    try:
        session_data = validate_session_cookie(session_cookie)
        return session_data
    except (BadSignature, SignatureExpired):
        return None


def get_current_user_from_session(request: Request) -> dict:
    """
    Dependency para obtener usuario actual desde sesión cookie
    
    Args:
        request: FastAPI Request
        
    Returns:
        dict con user_id, username, is_admin
        
    Raises:
        HTTPException 401 si no hay sesión válida
    """
    session_data = get_session_from_request(request)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found or session expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session_data


def get_current_admin_from_session(request: Request) -> dict:
    """
    Dependency para obtener admin desde sesión cookie
    
    Args:
        request: FastAPI Request
        
    Returns:
        dict con datos de admin
        
    Raises:
        HTTPException 403 si no es admin
    """
    session_data = get_current_user_from_session(request)
    
    if not session_data.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return session_data


class SessionValidationMiddleware(BaseHTTPMiddleware):
    """Middleware para validar sesiones (opcional)"""
    
    async def dispatch(self, request: Request, call_next):
        # Validar sesión si existe
        session_data = get_session_from_request(request)
        
        if session_data:
            # Agregar session data al request state
            request.state.session = session_data
            request.state.user_id = session_data['user_id']
            request.state.username = session_data['username']
            request.state.is_admin = session_data['is_admin']
            logger.info(f"Session validated for user: {session_data['username']}")
        
        response = await call_next(request)
        return response
