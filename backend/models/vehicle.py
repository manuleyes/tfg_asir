"""
Modelo de Vehículo Detectado
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from datetime import datetime
from models.database import Base


class Vehicle(Base):
    """
    Tabla de vehículos detectados por el sistema
    """
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    license_plate = Column(String(20), nullable=True, index=True)
    vehicle_model = Column(String(100), nullable=True)
    vehicle_color = Column(String(50), nullable=True)
    confidence = Column(Float, default=0.0)  # Confianza de detección
    times_detected = Column(Integer, default=1)  # Veces visto
    image_path = Column(String(500), nullable=True)  # Ruta de imagen
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Vehicle {self.license_plate}>"
