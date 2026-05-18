"""
routes/email_routes.py - Endpoints para configuración y prueba de notificaciones email
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from models.database import get_db
from models.user import User
from models.alert import Alert
from routes.twofa_routes import _get_session_user
from services.email_service import get_email_service
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/email", tags=["Email Notifications"])


class EmailConfigRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from: str = ""


class TestEmailRequest(BaseModel):
    to: str


class NotificationPrefsRequest(BaseModel):
    email_notifications: bool
    notify_critical: bool = True
    notify_warning: bool = False


@router.get("/status")
def email_status(request: Request, db: Session = Depends(get_db)):
    """Estado del servicio de email"""
    user = _get_session_user(request, db)
    svc = get_email_service()
    return {
        "configured": svc.is_configured(),
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user if settings.smtp_user else "(no configurado)",
        "user_email_notifications": user.email_notifications,
        "user_email": user.email,
    }


@router.post("/test")
def send_test_email(
    body: TestEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Enviar email de prueba al destinatario indicado"""
    user = _get_session_user(request, db)
    svc = get_email_service()

    if not svc.is_configured():
        raise HTTPException(
            status_code=400,
            detail=(
                "Servicio de email no configurado. "
                "Agrega smtp_user y smtp_password al archivo .env"
            ),
        )

    success = svc.send_test_email(to=body.to)
    if not success:
        raise HTTPException(status_code=500, detail="Error al enviar email de prueba")

    return {"message": f"Email de prueba enviado a {body.to}"}


@router.patch("/preferences")
def update_notification_preferences(
    body: NotificationPrefsRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Actualizar preferencias de notificación del usuario autenticado"""
    user = _get_session_user(request, db)
    user.email_notifications = body.email_notifications
    user.notify_critical = body.notify_critical
    user.notify_warning = body.notify_warning
    db.commit()
    return {
        "message": "Preferencias actualizadas",
        "email_notifications": user.email_notifications,
        "notify_critical": user.notify_critical,
        "notify_warning": user.notify_warning,
    }


async def notify_users_of_alert(db: Session, alert: Alert):
    """
    Enviar notificación de email a todos los usuarios que tengan
    las notificaciones activadas para la severidad de la alerta.
    Llamar desde el endpoint de creación de alertas.
    """
    svc = get_email_service()
    if not svc.is_configured():
        return

    try:
        users = db.query(User).filter(
            User.is_active == True,
            User.email_notifications == True,
            User.email != None,
        ).all()

        recipients = []
        for u in users:
            if alert.severity == "critical" and u.notify_critical:
                recipients.append(u.email)
            elif alert.severity == "warning" and u.notify_warning:
                recipients.append(u.email)

        if recipients:
            svc.send_alert_notification(
                to=recipients,
                alert_title=alert.title,
                alert_type=alert.alert_type,
                severity=alert.severity,
                description=alert.description or "",
                camera_id=alert.camera_id,
            )
    except Exception as e:
        logger.error(f"Error en notify_users_of_alert: {e}")
