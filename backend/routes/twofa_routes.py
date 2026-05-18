"""
routes/twofa_routes.py - Endpoints para 2FA (TOTP) y gestión de roles
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from models.database import get_db
from models.user import User, UserRole
from auth.password_hash import verify_password, hash_password
from auth.session_handler import (
    SESSION_COOKIE_NAME,
    validate_session_cookie,
    create_session_cookie,
)
from itsdangerous import BadSignature, SignatureExpired
import logging
import secrets
import base64
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/2fa", tags=["2FA & Roles"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_session_user(request: Request, db: Session) -> User:
    """Obtener usuario desde cookie de sesión o lanzar 401"""
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        session_data = validate_session_cookie(cookie)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    return user


def _require_totp():
    """Importar pyotp; lanzar 501 si no está instalado"""
    try:
        import pyotp
        return pyotp
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="pyotp no instalado. Ejecuta: pip install pyotp qrcode[pil]",
        )


# ─── Schemas ─────────────────────────────────────────────────────────────────

class TOTPVerifyRequest(BaseModel):
    token: str


class TOTPDisableRequest(BaseModel):
    password: str
    token: str


class RoleUpdateRequest(BaseModel):
    role: UserRole


class UserUpdateRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    email_notifications: bool | None = None
    notify_critical: bool | None = None
    notify_warning: bool | None = None
    phone_notifications: bool | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ─── 2FA Endpoints ───────────────────────────────────────────────────────────

@router.post("/setup")
def setup_2fa(request: Request, db: Session = Depends(get_db)):
    """
    Generar secreto TOTP y QR code para el usuario autenticado.
    Devuelve: {secret, qr_data_url, provisioning_uri}
    """
    pyotp = _require_totp()
    user = _get_session_user(request, db)

    if user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA ya está activado")

    # Generar nuevo secreto
    secret = pyotp.random_base32()
    user.totp_secret = secret
    db.commit()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email or user.username,
        issuer_name="Vigilancia Inteligente",
    )

    # Generar QR code como data URL
    try:
        import qrcode
        qr = qrcode.make(provisioning_uri)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode()
        qr_data_url = f"data:image/png;base64,{qr_b64}"
    except ImportError:
        qr_data_url = None

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_data_url": qr_data_url,
        "message": "Escanea el QR con tu app autenticadora y luego verifica con /api/2fa/verify",
    }


@router.post("/verify")
def verify_2fa(
    body: TOTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Verificar token TOTP y activar 2FA si es la primera vez.
    """
    pyotp = _require_totp()
    user = _get_session_user(request, db)

    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="Primero ejecuta /api/2fa/setup")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    user.totp_enabled = True
    db.commit()

    return {"message": "2FA activado correctamente", "totp_enabled": True}


@router.post("/disable")
def disable_2fa(
    body: TOTPDisableRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Desactivar 2FA (requiere contraseña y token TOTP actual)
    """
    pyotp = _require_totp()
    user = _get_session_user(request, db)

    if not user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA no está activado")

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Token TOTP inválido")

    user.totp_enabled = False
    user.totp_secret = None
    db.commit()

    return {"message": "2FA desactivado correctamente", "totp_enabled": False}


@router.get("/status")
def get_2fa_status(request: Request, db: Session = Depends(get_db)):
    """Estado de 2FA del usuario autenticado"""
    user = _get_session_user(request, db)
    return {
        "totp_enabled": user.totp_enabled,
        "username": user.username,
        "role": user.role,
        "email_notifications": user.email_notifications,
    }


# ─── Role Management (solo admin) ────────────────────────────────────────────

@router.get("/users")
def list_users(request: Request, db: Session = Depends(get_db)):
    """Listar todos los usuarios (solo admin)"""
    current = _get_session_user(request, db)
    if current.role != UserRole.admin and current.is_admin is not True:
        raise HTTPException(status_code=403, detail="Solo administradores")

    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "totp_enabled": u.totp_enabled,
            "email_notifications": u.email_notifications,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: RoleUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Cambiar rol de usuario (solo admin)"""
    current = _get_session_user(request, db)
    if current.role != UserRole.admin and current.is_admin is not True:
        raise HTTPException(status_code=403, detail="Solo administradores")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target.role = body.role
    # Sincronizar is_admin con el rol
    target.is_admin = body.role == UserRole.admin
    db.commit()

    return {"message": f"Rol actualizado a {body.role}", "user_id": user_id}


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Activar/desactivar usuario (solo admin)"""
    current = _get_session_user(request, db)
    if current.role != UserRole.admin and current.is_admin is not True:
        raise HTTPException(status_code=403, detail="Solo administradores")

    if current.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes desactivarte a ti mismo")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target.is_active = not target.is_active
    db.commit()

    return {"user_id": user_id, "is_active": target.is_active}


@router.get("/profile/me")
def get_profile(request: Request, db: Session = Depends(get_db)):
    """Obtener perfil del usuario autenticado"""
    user = _get_session_user(request, db)
    return {
        "username": user.username,
        "email": user.email or "",
        "phone": getattr(user, 'phone', None) or "",
        "role": user.role,
        "is_admin": user.is_admin,
        "totp_enabled": user.totp_enabled,
        "email_notifications": user.email_notifications,
        "notify_critical": user.notify_critical,
        "notify_warning": user.notify_warning,
        "phone_notifications": getattr(user, 'phone_notifications', False) or False,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.patch("/profile")
def update_profile(
    body: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Actualizar perfil del usuario autenticado"""
    user = _get_session_user(request, db)

    if body.email is not None:
        existing = db.query(User).filter(User.email == body.email, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email ya en uso")
        user.email = body.email

    if body.phone is not None:
        user.phone = body.phone
    if body.email_notifications is not None:
        user.email_notifications = body.email_notifications
    if body.notify_critical is not None:
        user.notify_critical = body.notify_critical
    if body.notify_warning is not None:
        user.notify_warning = body.notify_warning
    if body.phone_notifications is not None:
        user.phone_notifications = body.phone_notifications

    db.commit()
    return {"message": "Perfil actualizado"}


@router.patch("/change-password")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Cambiar contraseña del usuario autenticado"""
    user = _get_session_user(request, db)
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    if len(body.new_password) < 4:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")
    from auth.password_hash import hash_password
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente"}
