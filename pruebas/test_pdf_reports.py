#!/usr/bin/env python3
"""
Prueba de generación de PDF de reportes
"""
import sys
from pathlib import Path
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_pdf_generation():
    """Probar generación de PDF de reportes"""
    print("\n" + "=" * 70)
    print("PRUEBA DE GENERACIÓN DE REPORTES PDF")
    print("=" * 70)
    
    # Login
    print("\n[1] Autenticando...")
    try:
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(" Autenticado")
    except Exception as e:
        print(f" Error: {e}")
        return
    
    # Probar endpoint de PDF
    print("\n[2] Solicitando reporte PDF...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/reportes/detecciones",
            headers=headers
        )
        
        if response.status_code == 200:
            # Guardar PDF
            pdf_path = Path(__file__).parent / "reporte_vigilancia.pdf"
            pdf_path.write_bytes(response.content)
            print(f" PDF generado exitosamente")
            print(f"   - Ubicación: {pdf_path}")
            print(f"   - Tamaño: {len(response.content)} bytes")
        else:
            print(f" Error {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f" Error: {e}")
    
    # Reporte en JSON
    print("\n[3] Solicitando estadísticas JSON...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/reportes/estadisticas.json",
            headers=headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f" Estadísticas obtenidas:")
            print(f"   - Total detecciones: {stats.get('total', 0)}")
            print(f"   - Personas: {stats.get('persons', 0)}")
            print(f"   - Vehículos: {stats.get('vehicles', 0)}")
            
            # Guardar JSON
            import json
            json_path = Path(__file__).parent / "estadisticas.json"
            json_path.write_text(json.dumps(stats, indent=2))
            print(f"   - JSON guardado en: {json_path}")
        else:
            print(f" Error {response.status_code}")
    except Exception as e:
        print(f" Error: {e}")
    
    print("\n" + "=" * 70)
    print(" PRUEBA DE REPORTES COMPLETADA")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    test_pdf_generation()
