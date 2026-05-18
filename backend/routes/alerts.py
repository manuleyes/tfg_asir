"""
Rutas para Alertas - GET, FILTER, UPDATE, CREATE, etc
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.alert import Alert
from middleware.auth_middleware import get_current_user
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alertas", tags=["Alerts"])


class AlertCreate(BaseModel):
    camera_id: int
    alert_type: str
    title: str
    description: Optional[str] = None
    severity: str = "info"


@router.get("")
def get_alerts(
    severity: str = Query(None),
    is_read: bool = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener lista de alertas
    GET /api/alertas?severity=critical&is_read=false&limit=100
    """
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset).all()
    total = query.count()
    
    return {
        "data": alerts,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener alerta específica
    GET /api/alertas/{id}
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    return alert


@router.patch("/{alert_id}/read")
def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Marcar alerta como leída
    PATCH /api/alertas/{id}/read
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    
    return {"message": "Alerta marcada como leída"}


@router.get("/camera/{camera_id}")
def get_alerts_by_camera(
    camera_id: int,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener alertas de una cámara específica
    GET /api/alertas/camera/{camera_id}
    """
    alerts = db.query(Alert).filter(
        Alert.camera_id == camera_id
    ).order_by(Alert.created_at.desc()).limit(limit).all()

    return alerts


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crear nueva alerta y notificar por email + WebSocket si es crítica.
    POST /api/alertas
    """
    alert = Alert(
        camera_id=body.camera_id,
        alert_type=body.alert_type,
        title=body.title,
        description=body.description,
        severity=body.severity,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Notificaciones en background (no bloquean la respuesta)
    from routes.email_routes import notify_users_of_alert
    background_tasks.add_task(notify_users_of_alert, db, alert)

    # Broadcast WebSocket
    from routes.websocket_routes import broadcast_new_alert
    background_tasks.add_task(
        broadcast_new_alert,
        {
            "id": alert.id,
            "camera_id": alert.camera_id,
            "alert_type": alert.alert_type,
            "title": alert.title,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        },
    )

    logger.info(f"Nueva alerta creada: id={alert.id} severity={alert.severity}")
    return alert

