"""
Rutas de Análisis - Insertar detecciones en BD
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from models.database import get_db
from models.person import Person
from models.vehicle import Vehicle
from models.camera import Camera
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analisis", tags=["Analysis"])


class GuardarPersonaRequest(BaseModel):
    """Solicitud para guardar persona detectada"""
    camera_id: int
    person_id: str
    facial_features: str = "Características faciales"
    confidence: float = 0.95
    image_path: str = "/static/detections/person.jpg"


class GuardarVehiculoRequest(BaseModel):
    """Solicitud para guardar vehículo detectado"""
    camera_id: int
    license_plate: str = "NO DETECTADA"
    vehicle_model: str = "Modelo detectado"
    vehicle_color: str = "Color detectado"
    confidence: float = 0.95
    image_path: str = "/static/detections/vehicle.jpg"


@router.post("/guardar-persona")
async def save_detected_person(
    request: GuardarPersonaRequest,
    db: Session = Depends(get_db)
):
    """
    Guardar una persona detectada en la BD
    
    Args:
        request: Datos de la persona
        db: Sesión de BD
        
    Returns:
        Persona guardada
    """
    try:
        # Verificar que la cámara existe
        camera = db.query(Camera).filter(Camera.id == request.camera_id).first()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cámara no encontrada"
            )
        
        # Verificar si ya existe esta persona
        existing_person = db.query(Person).filter(
            Person.person_id == request.person_id,
            Person.camera_id == request.camera_id
        ).first()
        
        if existing_person:
            # Actualizar conteo
            existing_person.times_detected += 1
            existing_person.detected_at = datetime.utcnow()
            db.commit()
            logger.info(f"Persona actualizada: {request.person_id} (detección #{existing_person.times_detected})")
            return existing_person
        
        # Crear nueva persona
        new_person = Person(
            camera_id=request.camera_id,
            person_id=request.person_id,
            facial_features=request.facial_features,
            confidence=request.confidence,
            times_detected=1,
            image_path=request.image_path,
            detected_at=datetime.utcnow()
        )
        
        db.add(new_person)
        db.commit()
        db.refresh(new_person)
        
        logger.info(f" Persona guardada: ID={request.person_id}, Cámara={request.camera_id}")
        
        return {
            "id": new_person.id,
            "person_id": new_person.person_id,
            "camera_id": new_person.camera_id,
            "confidence": new_person.confidence,
            "detected_at": new_person.detected_at
        }
        
    except Exception as e:
        logger.error(f"Error guardando persona: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/guardar-vehiculo")
async def save_detected_vehicle(
    request: GuardarVehiculoRequest,
    db: Session = Depends(get_db)
):
    """
    Guardar un vehículo detectado en la BD
    
    Args:
        request: Datos del vehículo
        db: Sesión de BD
        
    Returns:
        Vehículo guardado
    """
    try:
        # Verificar que la cámara existe
        camera = db.query(Camera).filter(Camera.id == request.camera_id).first()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cámara no encontrada"
            )
        
        # Verificar si ya existe este vehículo
        existing_vehicle = db.query(Vehicle).filter(
            Vehicle.license_plate == request.license_plate,
            Vehicle.camera_id == request.camera_id
        ).first()
        
        if existing_vehicle:
            # Actualizar conteo
            existing_vehicle.times_detected += 1
            existing_vehicle.detected_at = datetime.utcnow()
            db.commit()
            logger.info(f"Vehículo actualizado: {request.license_plate} (detección #{existing_vehicle.times_detected})")
            return existing_vehicle
        
        # Crear nuevo vehículo
        new_vehicle = Vehicle(
            camera_id=request.camera_id,
            license_plate=request.license_plate,
            vehicle_model=request.vehicle_model,
            vehicle_color=request.vehicle_color,
            confidence=request.confidence,
            times_detected=1,
            image_path=request.image_path,
            detected_at=datetime.utcnow()
        )
        
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        
        logger.info(f" Vehículo guardado: Placa={request.license_plate}, Cámara={request.camera_id}")
        
        return {
            "id": new_vehicle.id,
            "license_plate": new_vehicle.license_plate,
            "camera_id": new_vehicle.camera_id,
            "confidence": new_vehicle.confidence,
            "detected_at": new_vehicle.detected_at
        }
        
    except Exception as e:
        logger.error(f"Error guardando vehículo: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/estadisticas")
async def detection_statistics(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de detecciones
    """
    try:
        total_personas = db.query(Person).count()
        total_vehiculos = db.query(Vehicle).count()
        
        # Top cámaras
        cameras = db.query(Camera).filter(Camera.is_active == True).all()
        
        stats = {
            "personas_unicas": total_personas,
            "vehiculos_unicos": total_vehiculos,
            "total_detecciones": total_personas + total_vehiculos,
            "camaras_activas": len(cameras),
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Estadísticas: {total_personas} personas,  {total_vehiculos} vehículos")
        return stats
        
    except Exception as e:
        logger.error(f"Error en estadísticas: {e}")
        return {"error": str(e)}
