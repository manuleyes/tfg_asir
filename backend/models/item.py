"""
Modelo unificado de items detectados (personas y vehículos)
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime
from models.database import Base


class DetectedItem(Base):
    """
    Tabla única para todas las detecciones del sistema.
    El campo 'type' distingue persona ('person') de vehículo ('vehicle').
    """
    __tablename__ = "detected_items"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    item_id = Column(String(100), nullable=False)   # ID único de detección
    type = Column(String(20), nullable=False)        # 'person' o 'vehicle'
    label = Column(String(200), nullable=True)       # descripción legible
    confidence = Column(Float, default=0.0)
    times_detected = Column(Integer, default=1)
    image_path = Column(String(500), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DetectedItem {self.type}:{self.item_id}>"
