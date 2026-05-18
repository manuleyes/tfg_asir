#!/usr/bin/env python3
"""
Script para probar detección YOLO con imágenes
"""
import sys
from pathlib import Path
import requests

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.detection import DetectionService
import logging
import cv2
import numpy as np
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_image():
    """Crear una imagen de prueba con formas"""
    img = Image.new('RGB', (640, 480), color='white')
    draw = ImageDraw.Draw(img)
    
    # Dibujar algunos rectángulos que simulan objetos
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
    draw.rectangle([300, 100, 450, 200], fill='blue', outline='black')
    draw.rectangle([100, 300, 300, 400], fill='green', outline='black')
    
    # Guardar
    test_path = Path(__file__).parent / "test_image.jpg"
    img.save(test_path)
    logger.info(f" Imagen de prueba creada: {test_path}")
    return str(test_path)

def test_yolo_detection():
    """Probar servicio de detección YOLO"""
    print("\n" + "=" * 70)
    print("PRUEBA DE DETECCIÓN YOLO")
    print("=" * 70)
    
    try:
        # Inicializar servicio
        logger.info("Cargando modelo YOLO...")
        service = DetectionService("yolov8x.pt")
        logger.info(" Modelo YOLO cargado")
        
        # Crear imagen de prueba
        test_image = create_test_image()
        
        # Hacer detección
        logger.info("Ejecutando detección...")
        result = service.detect_in_image(test_image, conf=0.3)
        
        print("\n📊 RESULTADOS DE DETECCIÓN:")
        print(f"   - Total objetos detectados: {result.get('total', 0)}")
        print(f"   - Personas: {len(result.get('personas', []))}")
        print(f"   - Vehículos: {len(result.get('vehiculos', []))}")
        
        if result.get('personas'):
            print("\n👥 Detalles de personas:")
            for p in result['personas']:
                print(f"     - Confianza: {p.get('confidence', 0):.2%}")
        
        if result.get('vehiculos'):
            print("\n🚗 Detalles de vehículos:")
            for v in result['vehiculos']:
                print(f"     - Confianza: {v.get('confidence', 0):.2%}")
        
        return True
        
    except Exception as e:
        logger.error(f" Error en detección: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_detection():
    """Probar endpoint de detección vía API"""
    print("\n" + "=" * 70)
    print("PRUEBA DE API DE DETECCIÓN")
    print("=" * 70)
    
    # Login
    try:
        login_resp = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test endpoint info
        info_resp = requests.get(
            "http://localhost:8000/api/deteccion/info",
            headers=headers
        )
        
        if info_resp.status_code == 200:
            print(" Endpoint /api/deteccion/info:", info_resp.json())
        else:
            print(f" Error {info_resp.status_code}")
        
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    test_yolo_detection()
    test_api_detection()
    
    print("\n" + "=" * 70)
    print(" PRUEBA COMPLETADA")
    print("=" * 70 + "\n")
