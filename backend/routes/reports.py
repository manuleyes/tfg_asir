"""
Rutas de Reportes - PDF generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from models.database import get_db
from models.person import Person
from models.vehicle import Vehicle
from models.camera import Camera
from services.reports import get_report_generator
import logging
from datetime import datetime
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reportes", tags=["Reports"])


@router.get("/detecciones")
async def generate_detection_report(db: Session = Depends(get_db)):
    """
    Generar reporte PDF de detecciones
    """
    try:
        # Obtener datos
        personas = db.query(Person).all()
        vehiculos = db.query(Vehicle).all()
        camaras = db.query(Camera).filter(Camera.is_active == True).count()
        
        data = {
            "personas": [
                {
                    "id": p.id,
                    "person_id": p.person_id,
                    "confidence": p.confidence,
                    "times_detected": p.times_detected,
                    "detected_at": p.detected_at.isoformat() if p.detected_at else None
                }
                for p in personas
            ],
            "vehiculos": [
                {
                    "id": v.id,
                    "license_plate": v.license_plate,
                    "vehicle_model": v.vehicle_model,
                    "vehicle_color": v.vehicle_color,
                    "confidence": v.confidence,
                    "times_detected": v.times_detected,
                    "detected_at": v.detected_at.isoformat() if v.detected_at else None
                }
                for v in vehiculos
            ],
            "total_personas": len(personas),
            "total_vehiculos": len(vehiculos),
            "total_detecciones": len(personas) + len(vehiculos),
            "camaras_activas": camaras
        }
        
        # Generar PDF
        generator = get_report_generator()
        pdf_buffer = generator.generate_detection_report(data)
        
        logger.info(" Reporte generado exitosamente")
        
        # Retornar como descarga
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=reporte_detecciones.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/estadisticas.json")
async def export_statistics(db: Session = Depends(get_db)):
    """
    Exportar estadísticas en JSON
    """
    try:
        personas = db.query(Person).count()
        vehiculos = db.query(Vehicle).count()
        camaras = db.query(Camera).count()
        camaras_activas = db.query(Camera).filter(Camera.is_active == True).count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "estadisticas": {
                "personas_detectadas": personas,
                "vehiculos_detectados": vehiculos,
                "camaras_totales": camaras,
                "camaras_activas": camaras_activas,
                "total_registros": personas + vehiculos
            }
        }
        
    except Exception as e:
        logger.error(f"Error en estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
