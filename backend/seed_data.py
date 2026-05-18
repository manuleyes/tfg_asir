"""
Script para crear datos de prueba
Cámaras, personas y vehículos de ejemplo
"""
import sys
from datetime import datetime, timedelta
import random
sys.path.insert(0, '.')

from models.database import SessionLocal, engine, Base
from models.camera import Camera
from models.person import Person
from models.vehicle import Vehicle
from models.alert import Alert

# Crear tablas
Base.metadata.create_all(bind=engine)

# Crear sesión
db = SessionLocal()

# Limpiar datos previos (opcional, comentar si quieres conservarlos)
# db.query(Alert).delete()
# db.query(Vehicle).delete()
# db.query(Person).delete()
# db.query(Camera).delete()
# db.commit()

# Cámaras seed eliminadas — solo se registran dispositivos reales que se conecten
cameras = []
db.commit()

print("Creando personas detectadas...")
# Crear personas de prueba
for camera in cameras[:2]:  # Solo primeras 2 cámaras
    for i in range(3):
        detected_at = datetime.utcnow() - timedelta(hours=random.randint(0, 24))
        person = Person(
            camera_id=camera.id,
            person_id=f"PERSON_{camera.id}_{i+1:03d}",
            facial_features="Adulto, cara rectangular",
            confidence=random.uniform(0.85, 0.99),
            times_detected=random.randint(1, 10),
            detected_at=detected_at,
        )
        db.add(person)

db.commit()

print("Creando vehículos detectados...")
# Crear vehículos de prueba
plates = [
    "ABC-1234", "XYZ-9876", "MNO-5555", "DEF-2020", "GHI-3030",
    "JKL-4040", "PQR-5050", "STU-6060", "VWX-7070"
]
for camera in cameras[:2]:  # Solo primeras 2 cámaras
    for plate in plates[:5]:
        detected_at = datetime.utcnow() - timedelta(hours=random.randint(0, 24))
        vehicle = Vehicle(
            camera_id=camera.id,
            license_plate=plate,
            vehicle_model=random.choice([
                "Toyota Corolla", "Honda Civic", "Ford Focus",
                "Renault Duster", "Chevrolet Cruze", "Volkswagen Golf"
            ]),
            vehicle_color=random.choice([
                "Blanco", "Negro", "Gris", "Rojo", "Azul", "Plateado"
            ]),
            confidence=random.uniform(0.90, 0.99),
            times_detected=random.randint(1, 15),
            detected_at=detected_at,
        )
        db.add(vehicle)

db.commit()

print("Creando alertas...")
# Crear alertas de prueba
for camera in cameras:
    for i in range(2):
        alert = Alert(
            camera_id=camera.id,
            alert_type="person" if i % 2 == 0 else "vehicle",
            title=f"Detección en {camera.name}",
            description="Detección automática realizada por el sistema",
            severity=random.choice(["info", "warning", "critical"]),
            is_read=random.choice([True, False]),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 24)),
        )
        db.add(alert)

db.commit()

print(" Datos de prueba creados exitosamente!")
print(f"   - {len(cameras)} cámaras")
print(f"   - {db.query(Person).count()} personas")
print(f"   - {db.query(Vehicle).count()} vehículos")
print(f"   - {db.query(Alert).count()} alertas")

db.close()
