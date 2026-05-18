#!/usr/bin/env python3
"""
Suite completa de tests automatizados para CI/CD
"""
import subprocess
import sys
import time
import requests
import json
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8000"
RESULTS = {
    "tests": [],
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "start_time": None,
    "end_time": None
}

def log_test(name, status, message="", duration=0):
    """Registrar resultado de test"""
    result = {
        "name": name,
        "status": status,
        "message": message,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    }
    RESULTS["tests"].append(result)
    
    if status == " PASSED":
        RESULTS["passed"] += 1
        print(f" {name}")
    elif status == " FAILED":
        RESULTS["failed"] += 1
        print(f" {name}: {message}")
    else:
        RESULTS["warnings"] += 1
        print(f"️  {name}: {message}")
    
    return result

def test_authentication():
    """Pruebas de autenticación"""
    print("\n" + "="*70)
    print("TESTING: Autenticación")
    print("="*70)
    
    start = time.time()
    
    # Test 1: Login exitoso
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                log_test("Login con credenciales correcías", " PASSED", "", time.time() - start)
                return data["access_token"]
            else:
                log_test("Login con credenciales correctas", " FAILED", "No token en respuesta")
        else:
            log_test("Login con credenciales correctas", " FAILED", f"Status {response.status_code}")
    except Exception as e:
        log_test("Login con credenciales correctas", " FAILED", str(e))
    
    # Test 2: Login fallido (credenciales inválidas)
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        if response.status_code == 401 or response.status_code == 422:
            log_test("Login rechaza credenciales incorrectas", " PASSED", "", time.time() - start)
        else:
            log_test("Login rechaza credenciales incorrectas", "️  WARNING", f"Expected 401/422, got {response.status_code}")
    except Exception as e:
        log_test("Login rechaza credenciales incorrectas", " FAILED", str(e))
    
    return None

def test_api_endpoints(token):
    """Pruebas de endpoints protegidos"""
    print("\n" + "="*70)
    print("TESTING: Endpoints")
    print("="*70)
    
    if not token:
        log_test("Endpoints API", " FAILED", "Token no disponible")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/api/camaras", "GET", None, "Cámaras"),
        ("/api/personas", "GET", None, "Personas"),
        ("/api/vehiculos", "GET", None, "Vehículos"),
        ("/api/alertas", "GET", None, "Alertas"),
        ("/api/deteccion/info", "GET", None, "Detección Info"),
    ]
    
    for endpoint, method, body, label in endpoints:
        try:
            start = time.time()
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=body)
            
            duration = time.time() - start
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('total', '?')
                log_test(f"{label}", " PASSED", f"{count} items", duration)
            else:
                log_test(f"{label}", " FAILED", f"Status {response.status_code}", duration)
        except Exception as e:
            log_test(f"{label}", " FAILED", str(e)[:50])

def test_database():
    """Pruebas de base de datos"""
    print("\n" + "="*70)
    print("TESTING: Base de Datos")
    print("="*70)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        from models.database import SessionLocal
        from models.camera import Camera
        from models.person import Person
        from models.vehicle import Vehicle
        from models.alert import Alert
        from models.user import User
        
        db = SessionLocal()
        
        tables = [
            (User, "Tabla de usuarios"),
            (Camera, "Tabla de cámaras"),
            (Person, "Tabla de personas"),
            (Vehicle, "Tabla de vehículos"),
            (Alert, "Tabla de alertas"),
        ]
        
        for model, label in tables:
            try:
                count = db.query(model).count()
                if count >= 0:
                    log_test(f"DB: {label}", " PASSED", f"{count} registros")
                else:
                    log_test(f"DB: {label}", "️  WARNING", "0 registros")
            except Exception as e:
                log_test(f"DB: {label}", " FAILED", str(e)[:50])
        
        db.close()
    except Exception as e:
        log_test("Base de datos", " FAILED", f"No se pudo conectar: {e}")

def test_yolo():
    """Pruebas de detección YOLO"""
    print("\n" + "="*70)
    print("TESTING: Detección YOLO")
    print("="*70)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        from services.detection import DetectionService
        
        start = time.time()
        service = DetectionService("yolov8x.pt")
        load_time = time.time() - start
        
        log_test("Modelo YOLO carga", " PASSED", f"{service.model.__class__.__name__}", load_time)
        
        # Test detección con imagen de prueba
        test_img = Path(__file__).parent / "test_image.jpg"
        if test_img.exists():
            try:
                start = time.time()
                result = service.detect_in_image(str(test_img), conf=0.3)
                detect_time = time.time() - start
                
                if "total" in result:
                    log_test("Detección en imagen", " PASSED", f"{result['total']} objetos", detect_time)
                else:
                    log_test("Detección en imagen", "️  WARNING", "Respuesta incompleta")
            except Exception as e:
                log_test("Detección en imagen", " FAILED", str(e)[:50])
        else:
            log_test("Detección en imagen", "️  WARNING", "Imagen de prueba no encontrada")
            
    except Exception as e:
        log_test("YOLO Service", " FAILED", str(e)[:60])

def test_reports():
    """Pruebas de reportes"""
    print("\n" + "="*70)
    print("TESTING: Generación de Reportes")
    print("="*70)
    
    # Obtener token
    try:
        login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login.json().get("access_token")
        if not token:
            log_test("Reportes PDF", " FAILED", "No token")
            return
    except:
        log_test("Reportes PDF", " FAILED", "No pudiera autenticar")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test PDF
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/reportes/detecciones", headers=headers)
        pdf_time = time.time() - start
        
        if response.status_code == 200 and len(response.content) > 100:
            log_test("Generación PDF", " PASSED", f"{len(response.content)} bytes", pdf_time)
        else:
            log_test("Generación PDF", " FAILED", f"Status {response.status_code}")
    except Exception as e:
        log_test("Generación PDF", " FAILED", str(e)[:50])
    
    # Test JSON
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/reportes/estadisticas.json", headers=headers)
        json_time = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            log_test("Estadísticas JSON", " PASSED", "Datos extraídos", json_time)
        else:
            log_test("Estadísticas JSON", " FAILED", f"Status {response.status_code}")
    except Exception as e:
        log_test("Estadísticas JSON", " FAILED", str(e)[:50])

def test_frontend():
    """Pruebas de frontend"""
    print("\n" + "="*70)
    print("TESTING: Frontend")
    print("="*70)
    
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/dashboard")
        load_time = time.time() - start
        
        if response.status_code == 200 and "html" in response.text.lower():
            log_test("Dashboard HTML", " PASSED", f"Cargado en {load_time:.2f}s", load_time)
        else:
            log_test("Dashboard HTML", "️  WARNING", f"Status {response.status_code}")
    except Exception as e:
        log_test("Dashboard HTML", " FAILED", str(e))

def generate_report():
    """Generar reporte de testing"""
    print("\n" + "="*70)
    print("REPORTE FINAL")
    print("="*70)
    
    total = RESULTS["passed"] + RESULTS["failed"]
    success_rate = (RESULTS["passed"] / total * 100) if total > 0 else 0
    
    print(f"""
TestResults Summary:
├─ Passed  : {RESULTS['passed']}/{total}  
├─ Failed  : {RESULTS['failed']}/{total}  
├─ Warnings: {RESULTS['warnings']}        ️
└─ Success Rate: {success_rate:.1f}%

Tests Details:
────────────────────────────────────────────
""")
    
    for test in RESULTS["tests"]:
        status_icon = "" if test["status"] == " PASSED" else "" if test["status"] == " FAILED" else "️"
        print(f"{status_icon} {test['name']}")
        if test["message"]:
            print(f"   └─ {test['message']} ({test['duration']:.3f}s)")
    
    # Guardar reporté en JSON
    report_path = Path(__file__).parent / "test_report.json"
    report_path.write_text(json.dumps(RESULTS, indent=2, default=str))
    print(f"\n📊 Reporte guardado en: {report_path}")

def main():
    """Correr suite de tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "SISTEMA DE VIGILANCIA - TEST SUITE" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    
    RESULTS["start_time"] = datetime.now().isoformat()
    
    # Ejecutar tests
    token = test_authentication()
    test_api_endpoints(token)
    test_database()
    test_yolo()
    test_reports()
    test_frontend()
    
    RESULTS["end_time"] = datetime.now().isoformat()
    
    # Reporte final
    generate_report()
    
    # Exit code basado en resultados
    sys.exit(0 if RESULTS["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
