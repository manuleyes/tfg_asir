#!/usr/bin/env python3
"""
API Testing Script
Verify all endpoints are working with valid JWT token
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    print("=" * 60)
    print("PRUEBAS DE API - SISTEMA DE VIGILANCIA")
    print("=" * 60)
    
    # Test 1: Login
    print("\n[TEST 1] Login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        login_result = response.json()
        
        if response.status_code == 200 and "access_token" in login_result:
            print(f" Login exitoso")
            print(f"   - Username: {login_result.get('username')}")
            print(f"   - Is Admin: {login_result.get('is_admin')}")
            token = login_result["access_token"]
        else:
            print(f" Login falló: {response.status_code}")
            return
    except Exception as e:
        print(f" Error en login: {e}")
        return
    
    # Test protected endpoints
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/api/camaras", "Cámaras"),
        ("/api/personas", "Personas"),
        ("/api/vehiculos", "Vehículos"),
        ("/api/alertas", "Alertas"),
    ]
    
    test_num = 2
    for endpoint, name in endpoints:
        print(f"\n[TEST {test_num}] GET {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('total', 'N/A')
                print(f" {name} - Encontrados: {count} items")
                
                # Show first item as sample
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Ejemplo: {json.dumps(data[0], indent=2, default=str)[:200]}...")
            else:
                print(f" Error {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f" Excepción: {e}")
        
        test_num += 1
    
    print("\n" + "=" * 60)
    print(" TODOS LOS TESTS COMPLETADOS")
    print("=" * 60)

if __name__ == "__main__":
    # Esperar a que el servidor esté listo
    time.sleep(1)
    test_api()
