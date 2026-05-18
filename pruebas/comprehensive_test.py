#!/usr/bin/env python3
"""
Comprehensive System Test - Verificar todos los componentes del sistema
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:16000"

def test_system():
    print("\n" + "=" * 70)
    print("VERIFICACIÓN COMPLETA DEL SISTEMA DE VIGILANCIA")
    print("=" * 70)
    
    # 1. Get token
    print("\n[1/6] Obteniendo token de autenticación...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token_data = login_response.json()
        token = token_data["access_token"]
        print(" Token obtenido exitosamente")
    except Exception as e:
        print(f" Error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test Frontend HTML
    print("\n[2/6] Verificando acceso a frontend...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard")
        if response.status_code == 200 and "html" in response.text.lower():
            print(" Dashboard HTML accesible")
        else:
            print(f"️  Dashboard retornó status {response.status_code}")
    except Exception as e:
        print(f"️  Error accediendo dashboard: {e}")
    
    # 3. Test YOLO Detection Service Info
    print("\n[3/6] Verificando servicio de detección YOLO...")
    try:
        response = requests.get(f"{BASE_URL}/api/deteccion/info", headers=headers)
        if response.status_code == 200:
            info = response.json()
            print(f" Servicio YOLO disponible")
            print(f"   - Versión: {info.get('version', 'N/A')}")
            print(f"   - Modelos: {info.get('available_models', 'N/A')}")
        else:
            print(f"️  Status {response.status_code}")
    except Exception as e:
        print(f"️  Error: {e}")
    
    # 4. Test Video Streaming Setup
    print("\n[4/6] Verificando setup de streaming...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/video/iniciar",
            headers=headers,
            json={"camera_index": 0}
        )
        if response.status_code in [200, 201]:
            print(" Comando de streaming enviado exitosamente")
        else:
            print(f"️  Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"️  Error: {e}")
    
    # 5. Test PDF Report Generation
    print("\n[5/6] Verificando generación de reportes...")
    try:
        response = requests.get(f"{BASE_URL}/api/reportes/estadisticas.json", headers=headers)
        if response.status_code == 200:
            report = response.json()
            print(f" Reporte JSON generado")
            print(f"   - Total detectiones: {report.get('total', 0)}")
        else:
            print(f"️  Status {response.status_code}")
    except Exception as e:
        print(f"️  Error: {e}")
    
    # 6. Database Summary
    print("\n[6/6] Resumen de datos en BD...")
    try:
        cameras = len(requests.get(f"{BASE_URL}/api/camaras", headers=headers).json())
        persons = len(requests.get(f"{BASE_URL}/api/personas", headers=headers).json())
        vehicles = len(requests.get(f"{BASE_URL}/api/vehiculos", headers=headers).json())
        alerts = len(requests.get(f"{BASE_URL}/api/alertas", headers=headers).json())
        
        print(f" Base de Datos:")
        print(f"   - Cámaras: {cameras}")
        print(f"   - Personas: {persons}")
        print(f"   - Vehículos: {vehicles}")
        print(f"   - Alertas: {alerts}")
    except Exception as e:
        print(f" Error: {e}")
    
    print("\n" + "=" * 70)
    print(" VERIFICACIÓN COMPLETADA")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    test_system()
