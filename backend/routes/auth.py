"""Rutas de Autenticación - Login con Cookies de Sesión
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.user import User
from auth.password_hash import verify_password, hash_password
from auth.session_handler import create_session_cookie, SESSION_COOKIE_NAME
from config import get_settings
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Esquemas Pydantic
class LoginRequest(BaseModel):
    """Schema para login"""
    username: str
    password: str
    totp_token: Optional[str] = None  # Token 2FA si está activado


class LoginResponse(BaseModel):
    """Schema para respuesta de login"""
    username: str
    is_admin: bool
    role: str = "admin"
    totp_required: bool = False
    message: str


class RegisterRequest(BaseModel):
    """Schema para registro de nuevo admin"""
    username: str
    password: str
    email: str = None
    role: str = "admin"


@router.post("/login")
def login(credentials: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Endpoint de login - Valida credenciales y retorna:
    - Cookie de sesión segura (httponly)
    - Si el usuario tiene 2FA activado y no envía totp_token, devuelve totp_required=True

    Args:
        credentials: username, password y totp_token opcional
        response: Response para set cookies
        db: Sesión de base de datos
    """
    # Buscar usuario en BD
    user = db.query(User).filter(User.username == credentials.username).first()

    # Validar usuario existe y contraseña es correcta
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validar usuario activo
    if not user.is_active:
        logger.warning(f"Login attempt with inactive user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    # Verificar 2FA si está activado
    if user.totp_enabled:
        if not credentials.totp_token:
            # Indicar al frontend que necesita el token TOTP
            return {
                "username": user.username,
                "is_admin": user.is_admin,
                "role": user.role or "admin",
                "totp_required": True,
                "message": "Se requiere código de autenticación 2FA",
            }
        # Validar el token TOTP
        try:
            import pyotp
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(credentials.totp_token, valid_window=1):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Código 2FA inválido o expirado",
                )
        except ImportError:
            logger.error("pyotp no instalado pero usuario tiene 2FA activado")
            raise HTTPException(status_code=500, detail="Error interno: pyotp no disponible")

    # CREAR COOKIE DE SESIÓN
    session_cookie = create_session_cookie(
        user_id=user.id,
        username=user.username,
        is_admin=user.is_admin,
    )

    # SET COOKIE con protecciones de seguridad
    if response:
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_cookie,
            max_age=24 * 3600,
            expires=24 * 3600,
            secure=not settings.debug,
            httponly=True,
            samesite="lax",
            path="/",
        )

    logger.info(f"Successful login for user: {user.username}")

    return {
        "username": user.username,
        "is_admin": user.is_admin,
        "role": user.role or "admin",
        "totp_required": False,
        "message": f"Bienvenido {user.username}. Sesión iniciada correctamente.",
    }


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Endpoint para crear nuevo usuario admin (solo desarrollo)
    En producción, esto debería estar protegido
    """
    # Verificar que el usuario no exista
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya existe"
        )
    
    # Crear nuevo usuario
    new_user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        email=request.email,
        is_active=True,
        is_admin=True  # Por defecto admin en desarrollo
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username}")
    
    return {
        "message": "Usuario creado exitosamente",
        "username": new_user.username,
        "id": new_user.id,
        "is_admin": new_user.is_admin
    }


@router.get("/check-session")
def check_session(request: Request):
    """
    Endpoint para verificar si hay sesión válida
    Útil para frontend y rutas protegidas
    
    Returns:
        {authenticated: bool, user_data: {...}} o {authenticated: false}
    """
    from middleware.session_middleware import get_session_from_request
    
    session_data = get_session_from_request(request)
    
    if session_data:
        return {
            "authenticated": True,
            "user_id": session_data.get('user_id'),
            "username": session_data.get('username'),
            "is_admin": session_data.get('is_admin')
        }
    
    return {"authenticated": False}


@router.post("/logout")
def logout(response: Response):
    """
    Endpoint de logout - Elimina la cookie de sesión
    """
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=not settings.debug,  # True en producción (HTTPS), False en dev
        httponly=True,  # Consistente con set_cookie
        samesite="lax"  # Consistente con set_cookie
    )
    logger.info("User logged out")
    return {"message": "Sesión cerrada correctamente"}
