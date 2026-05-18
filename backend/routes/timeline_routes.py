"""
Línea temporal — consultas por rango de fechas sobre alertas, personas y vehículos
GET /api/timeline?since=2026-05-03T21:00:00&until=2026-05-04T07:23:00&types=alertas,personas,vehiculos
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from models.database import get_db
from models.alert import Alert
from models.person import Person
from models.vehicle import Vehicle
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/timeline", tags=["Timeline"])


def _parse_dt(value: str, field: str) -> datetime:
    """Parsea ISO 8601 o formato simple YYYY-MM-DDTHH:MM"""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise HTTPException(status_code=422, detail=f"Formato de fecha incorrecto en '{field}'. Usa YYYY-MM-DDTHH:MM")


@router.get("")
def get_timeline(
    since: str = Query(..., description="Inicio del rango: YYYY-MM-DDTHH:MM"),
    until: str = Query(..., description="Fin del rango:   YYYY-MM-DDTHH:MM"),
    types: str = Query("alertas,personas,vehiculos", description="Entidades a incluir (csv)"),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Devuelve todos los eventos registrados entre *since* y *until*.
    Tipos disponibles: alertas, personas, vehiculos
    """
    dt_since = _parse_dt(since, "since")
    dt_until = _parse_dt(until, "until")

    if dt_since >= dt_until:
        raise HTTPException(status_code=422, detail="'since' debe ser anterior a 'until'")

    requested = {t.strip().lower() for t in types.split(",")}
    events: list = []

    # ── Alertas ────────────────────────────────────────────────────────────────
    if "alertas" in requested:
        rows = (
            db.query(Alert)
            .filter(Alert.created_at >= dt_since, Alert.created_at <= dt_until)
            .order_by(Alert.created_at.asc())
            .limit(limit)
            .all()
        )
        for r in rows:
            events.append({
                "type": "alerta",
                "id": r.id,
                "ts": r.created_at.isoformat() if r.created_at else None,
                "title": r.title,
                "detail": r.description or "",
                "severity": r.severity,
                "extra": {"camera_id": r.camera_id, "alert_type": r.alert_type, "is_read": r.is_read},
            })

    # ── Personas ───────────────────────────────────────────────────────────────
    if "personas" in requested:
        rows = (
            db.query(Person)
            .filter(Person.created_at >= dt_since, Person.created_at <= dt_until)
            .order_by(Person.created_at.asc())
            .limit(limit)
            .all()
        )
        for r in rows:
            events.append({
                "type": "persona",
                "id": r.id,
                "ts": r.created_at.isoformat() if r.created_at else None,
                "title": f"Persona detectada: {r.name or 'Desconocida'}",
                "detail": r.description or "",
                "severity": "info",
                "extra": {"camera_id": getattr(r, "camera_id", None), "confidence": getattr(r, "confidence", None)},
            })

    # ── Vehículos ──────────────────────────────────────────────────────────────
    if "vehiculos" in requested:
        rows = (
            db.query(Vehicle)
            .filter(Vehicle.created_at >= dt_since, Vehicle.created_at <= dt_until)
            .order_by(Vehicle.created_at.asc())
            .limit(limit)
            .all()
        )
        for r in rows:
            events.append({
                "type": "vehiculo",
                "id": r.id,
                "ts": r.created_at.isoformat() if r.created_at else None,
                "title": f"Vehículo detectado: {getattr(r, 'plate', None) or 'Sin matrícula'}",
                "detail": getattr(r, "description", "") or "",
                "severity": "info",
                "extra": {"camera_id": getattr(r, "camera_id", None), "vehicle_type": getattr(r, "vehicle_type", None)},
            })

    # Ordenar todo por timestamp ascendente
    events.sort(key=lambda e: e["ts"] or "")

    return {
        "since": dt_since.isoformat(),
        "until": dt_until.isoformat(),
        "total": len(events),
        "events": events,
    }
