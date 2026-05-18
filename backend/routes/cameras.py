"""
Rutas para Cámaras - GET, POST, DELETE, etc
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.camera import Camera
from middleware.auth_middleware import get_current_admin, get_current_user

router = APIRouter(prefix="/api/camaras", tags=["Cameras"])


class CameraCreate(BaseModel):
    """Schema para crear cámara"""
    name: str
    url: str
    location: str = None
    description: str = None


class CameraResponse(BaseModel):
    """Schema de respuesta"""
    id: int
    name: str
    url: str
    location: str | None = None
    description: str | None = None
    is_active: bool
    created_at: object = None
    updated_at: object = None

    class Config:
        from_attributes = True


@router.get("", response_model=list[CameraResponse])
def get_cameras(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Obtener lista de cámaras
    GET /api/camaras
    """
    cameras = db.query(Camera).all()
    return cameras


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Obtener cámara específica
    GET /api/camaras/{id}
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    return camera


@router.post("", response_model=dict)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Crear nueva cámara
    POST /api/camaras
    Requiere permisos de admin
    """
    new_camera = Camera(
        name=camera.name,
        url=camera.url,
        location=camera.location,
        description=camera.description,
        is_active=True
    )
    
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    return {
        "message": "Cámara creada exitosamente",
        "id": new_camera.id,
        "name": new_camera.name
    }


@router.put("/{camera_id}")
def update_camera(
    camera_id: int,
    camera: CameraCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Actualizar cámara
    PUT /api/camaras/{id}
    Requiere permisos de admin
    """
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    db_camera.name = camera.name
    db_camera.url = camera.url
    db_camera.location = camera.location
    db_camera.description = camera.description
    
    db.commit()
    db.refresh(db_camera)
    
    return {
        "message": "Cámara actualizada",
        "id": db_camera.id
    }


@router.delete("/{camera_id}")
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Eliminar cámara
    DELETE /api/camaras/{id}
    Requiere permisos de admin
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    db.delete(camera)
    db.commit()
    
    return {
        "message": "Cámara eliminada",
        "id": camera_id
    }


@router.patch("/{camera_id}/toggle")
def toggle_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Activar/Desactivar cámara
    PATCH /api/camaras/{id}/toggle
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cámara no encontrada"
        )
    
    camera.is_active = not camera.is_active
    db.commit()
    db.refresh(camera)
    
    return {
        "message": f"Cámara {'activada' if camera.is_active else 'desactivada'}",
        "is_active": camera.is_active
    }
