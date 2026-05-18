"""
Rutas de Video - Streaming y captura en tiempo real
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import cv2
import logging
import asyncio
from services.detection import get_detection_service
import threading
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["Video"])

# Variables globales para control de streaming
streaming_active = False
latest_frame = None
latest_detections = None


def generate_frames():
    """
    Generador de frames con detección
    Para streaming MJPEG
    """
    global streaming_active, latest_frame, latest_detections
    
    try:
        cap = cv2.VideoCapture(0)  # Webcam
        service = get_detection_service()
        streaming_active = True
        
        logger.info("Iniciando captura de webcam...")
        
        frame_count = 0
        while streaming_active:
            ret, frame = cap.read()
            if not ret:
                logger.warning("No se pudo leer frame")
                break
            
            # Redimensionar para procesamiento
            frame_small = cv2.resize(frame, (640, 480))
            
            # Detección
            annotated_frame, detections = service.detect_in_frame(frame_small, conf=0.5)
            
            # Guardar estado
            latest_frame = annotated_frame
            latest_detections = detections
            
            # Codificar frame
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()
            
            # MJPEG boundary
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                   frame_bytes + b'\r\n')
            
            frame_count += 1
            
            if frame_count % 30 == 0:
                logger.info(f"Frames procesados: {frame_count}, Detecciones: {detections['total']}")
        
        cap.release()
        logger.info("Captura de webcam finalizada")
        
    except Exception as e:
        logger.error(f"Error en generación de frames: {e}")
        streaming_active = False


@router.get("/stream")
async def video_stream():
    """
    Stream de video MJPEG desde webcam con detecciones
    
    Acceso: http://localhost:8000/api/video/stream
    Visualizar en: <img src="http://localhost:8000/api/video/stream">
    """
    try:
        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        logger.error(f"Error en stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en streaming de video"
        )


@router.get("/detecciones-activas")
async def active_detections():
    """
    Obtener últimas detecciones del stream en vivo
    """
    global latest_detections
    if latest_detections:
        return {
            "status": "streaming",
            "detecciones": latest_detections,
            "timestamp": time.time()
        }
    return {
        "status": "sin-stream",
        "detecciones": {"personas": [], "vehiculos": [], "total": 0}
    }


@router.post("/iniciar")
async def start_streaming():
    """
    Iniciar streaming de webcam
    """
    global streaming_active
    if not streaming_active:
        streaming_active = True
        logger.info("Streaming iniciado")
        return {"status": " Streaming iniciado"}
    return {"status": "️ Streaming ya activo"}


@router.post("/detener")
async def stop_streaming():
    """
    Detener streaming de webcam
    """
    global streaming_active
    streaming_active = False
    logger.info("Streaming detenido")
    return {"status": " Streaming detenido"}


@router.get("/estado")
async def streaming_status():
    """
    Estado actual del streaming
    """
    global streaming_active
    return {
        "activo": streaming_active,
        "tiene_detecciones": latest_detections is not None,
        "ultimas_detecciones": latest_detections or {"personas": [], "vehiculos": [], "total": 0}
    }
