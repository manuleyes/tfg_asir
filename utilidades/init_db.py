#!/usr/bin/env python3
"""
Script para inicializar la base de datos y crear las tablas
"""
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from models.database import engine, Base, SessionLocal
from models.user import User
from models.camera import Camera
from models.person import Person
from models.vehicle import Vehicle
from models.alert import Alert
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Crear todas las tablas en la base de datos"""
    logger.info("=" * 60)
    logger.info("Inicializando base de datos...")
    logger.info("=" * 60)
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        logger.info(" Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f" Error creando tablas: {e}")
        raise

def seed_admin_user():
    """Crear usuario administrador si no existe"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@sistema.local",
                hashed_password="$2b$12$8k2AYR8z.r7PK.OYlhj0y.K9pV3wGFG4H9Dn1K5pBqP5G0C9JQH7W",  # admin123 hasheado con bcrypt
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info(" Usuario admin creado")
        else:
            logger.info("ℹ️  Usuario admin ya existe")
    except Exception as e:
        logger.error(f" Error creando admin: {e}")
        db.rollback()
    finally:
        db.close()

def seed_test_data():
    """Crear datos de prueba"""
    db = SessionLocal()
    try:
        # Verificar cámaras
        cameras_count = db.query(Camera).count()
        if cameras_count == 0:
            cameras = [
                Camera(name="Cámara Entrada", url="http://192.168.1.100:8080", description="Entrada principal", 
                      location="Puerta frontal", is_active=True),
                Camera(name="Cámara Pasillo", url="http://192.168.1.101:8080", description="Pasillo central",
                      location="Pasillo 1", is_active=True),
                Camera(name="Cámara Patio", url="http://192.168.1.102:8080", description="Área exterior",
                      location="Patio trasero", is_active=True),
            ]
            db.add_all(cameras)
            db.commit()
            logger.info(f" {len(cameras)} cámaras creadas")
        else:
            logger.info(f"ℹ️  {cameras_count} cámaras ya existen")
        
        # Verificar personas
        persons_count = db.query(Person).count()
        if persons_count == 0:
            persons = []
            for i in range(1, 16):  # 15 personas
                person = Person(
                    name=f"Persona {i}",
                    description=f"Descripción de persona {i}",
                    image_path=f"/images/person_{i}.jpg",
                    confidence=0.85 + (i % 10) * 0.01
                )
                persons.append(person)
            db.add_all(persons)
            db.commit()
            logger.info(f" {len(persons)} personas creadas")
        else:
            logger.info(f"ℹ️  {persons_count} personas ya existen")
        
        # Verificar vehículos
        vehicles_count = db.query(Vehicle).count()
        if vehicles_count == 0:
            vehicles = []
            colors = ["Rojo", "Azul", "Negro", "Blanco", "Gris", "Verde", "Amarillo", "Naranja"]
            types_list = ["Carro", "Moto", "Camión", "Bicicleta"]
            for i in range(1, 46):  # 45 vehículos
                vehicle = Vehicle(
                    plate=f"PLACA{i:04d}",
                    vehicle_type=types_list[i % len(types_list)],
                    color=colors[i % len(colors)],
                    description=f"Vehículo {i}",
                    image_path=f"/images/vehicle_{i}.jpg",
                    confidence=0.80 + (i % 15) * 0.01
                )
                vehicles.append(vehicle)
            db.add_all(vehicles)
            db.commit()
            logger.info(f" {len(vehicles)} vehículos creados")
        else:
            logger.info(f"ℹ️  {vehicles_count} vehículos ya existen")
        
        # Verificar alertas
        alerts_count = db.query(Alert).count()
        if alerts_count == 0:
            alerts = []
            alert_types = ["Persona sospechosa", "Vehículo anómalo", "Movimiento detectado", "Acceso no autorizado"]
            for i in range(1, 13):  # 12 alertas
                alert = Alert(
                    alert_type=alert_types[i % len(alert_types)],
                    description=f"Alerta {i}: {alert_types[i % len(alert_types)]}",
                    severity="Alta" if i % 3 == 0 else "Media" if i % 2 == 0 else "Baja",
                    is_resolved=False if i <= 5 else True,
                    created_at=datetime.now() - timedelta(minutes=i*10)
                )
                alerts.append(alert)
            db.add_all(alerts)
            db.commit()
            logger.info(f" {len(alerts)} alertas creadas")
        else:
            logger.info(f"ℹ️  {alerts_count} alertas ya existen")
        
    except Exception as e:
        logger.error(f" Error sembrando datos: {e}")
        db.rollback()
    finally:
        db.close()

def verify_data():
    """Verificar que los datos se crearon correctamente"""
    db = SessionLocal()
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Verificación de datos en BD:")
        logger.info("=" * 60)
        
        users = db.query(User).count()
        cameras = db.query(Camera).count()
        persons = db.query(Person).count()
        vehicles = db.query(Vehicle).count()
        alerts = db.query(Alert).count()
        
        logger.info(f"👤 Usuarios: {users}")
        logger.info(f"📷 Cámaras: {cameras}")
        logger.info(f"👥 Personas: {persons}")
        logger.info(f"🚗 Vehículos: {vehicles}")
        logger.info(f"️  Alertas: {alerts}")
        
        logger.info("=" * 60)
        logger.info(" Base de datos inicializada correctamente")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f" Error verificando datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    seed_admin_user()
    seed_test_data()
    verify_data()
