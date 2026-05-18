"""
Rutas para Vehículos Detectados - GET, SEARCH, etc
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.database import get_db
from models.vehicle import Vehicle
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/vehiculos", tags=["Vehicles"])


@router.get("")
def get_vehicles(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener lista de vehículos detectados
    GET /api/vehiculos?limit=100&offset=0
    """
    vehicles = db.query(Vehicle).order_by(Vehicle.detected_at.desc()).limit(limit).offset(offset).all()
    total = db.query(Vehicle).count()
    
    return {
        "data": vehicles,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/search")
def search_vehicles(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Buscar vehículos por matrícula
    GET /api/vehiculos/search?q=ABC-1234
    """
    results = db.query(Vehicle).filter(
        Vehicle.license_plate.ilike(f"%{q}%")
    ).limit(50).all()
    
    return results


@router.get("/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener vehículo específico
    GET /api/vehiculos/{id}
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    return vehicle


@router.get("/camera/{camera_id}")
def get_vehicles_by_camera(
    camera_id: int,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener vehículos detectados por una cámara específica
    GET /api/vehiculos/camera/{camera_id}
    """
    vehicles = db.query(Vehicle).filter(
        Vehicle.camera_id == camera_id
    ).order_by(Vehicle.detected_at.desc()).limit(limit).all()
    
    return vehicles
