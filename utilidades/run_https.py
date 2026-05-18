#!/usr/bin/env python3
"""
Script para ejecutar el servidor FastAPI con HTTPS/SSL
Uso: python run_https.py
"""

import uvicorn
import sys
import os

# Asegurarse de que estamos en el directorio correcto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configurar y ejecutar uvicorn con SSL
if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
        log_level="info"
    )
