"""
Rutas de Detección - Endpoints para YOLO y análisis de objetos
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel
from services.detection import get_detection_service
import logging
import cv2
import numpy as np
from PIL import Image
import io
import tempfile
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deteccion", tags=["Detection"])


class DetectionResponse(BaseModel):
    """Response de detección"""
    personas: list
    vehiculos: list
    total: int


@router.post("/imagen", response_model=DetectionResponse)
async def detect_image(file: UploadFile = File(...)):
    """
    Detectar objetos en una imagen
    
    Args:
        file: Imagen en formato PNG/JPG
        
    Returns:
        Personas y vehículos detectados
    """
    try:
        # Leer imagen
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Guardar temporalmente en fichero seguro
        suffix = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            image.save(tmp_path)
        
        # Detección
        try:
            service = get_detection_service()
            result = service.detect_in_image(tmp_path)
        finally:
            os.unlink(tmp_path)
        
        logger.info(f"Detección en imagen: {result['total']} objetos")
        
        return DetectionResponse(
            personas=result["personas"],
            vehiculos=result["vehiculos"],
            total=result["total"]
        )
        
    except Exception as e:
        logger.error(f"Error en detección: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en detección: {str(e)}"
        )


@router.get("/info")
async def detection_info():
    """
    Obtener información del modelo YOLO
    """
    try:
        service = get_detection_service()
        return {
            "modelo": "YOLOv8-XLarge",
            "clases_totales": len(service.model.names),
            "clases": list(service.model.names.values()),
            "dispositivo": str(service.model.device),
            "status": " Operativo"
        }
    except Exception as e:
        return {"error": str(e), "status": " Error"}


@router.post("/prueba")
async def test_detection():
    """
    Prueba de detección con imagen de prueba
    """
    try:
        # Crear imagen de prueba simple
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        img[100:200, 100:200] = [0, 255, 0]  # Rectángulo verde
        
        service = get_detection_service()
        
        # Convertir a PIL y guardar en temp seguro
        from PIL import Image
        test_img = Image.fromarray(img)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_path = tmp.name
            test_img.save(test_path)
        try:
            result = service.detect_in_image(test_path)
        finally:
            os.unlink(test_path)
        
        return {
            "status": " Modelo funcionando",
            "test": "Imagen de prueba procesada",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error en prueba: {e}")
        return {
            "status": " Error",
            "error": str(e)
        }
