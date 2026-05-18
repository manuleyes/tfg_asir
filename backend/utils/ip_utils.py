"""
Utilidades para obtener IPs del servidor
"""
import os
import socket
import requests
from pathlib import Path
from typing import Dict, Optional

BACKEND_DIR  = Path(__file__).parent.parent
SSL_CERT     = BACKEND_DIR / "ssl" / "cert.pem"

def get_local_ip() -> str:
    """
    Obtener IP local del servidor
    """
    try:
        # Intentar conectar a Google DNS para determinar IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error obteniendo IP local: {e}")
        return "127.0.0.1"

def get_public_ip() -> Optional[str]:
    """
    Obtener IP pública del servidor
    """
    try:
        # Intentar obtener IP pública de diferentes servicios
        services = [
            "https://ifconfig.me",
            "https://ifconfig.io",
            "https://icanhazip.com",
            "https://api.ipify.org",
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=3)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if ip:
                        return ip
            except:
                continue
        
        return None
    except Exception as e:
        print(f"Error obteniendo IP pública: {e}")
        return None

def get_server_ips() -> Dict[str, Optional[str]]:
    """
    Obtener todas las IPs del servidor
    """
    # Detect actual port and protocol
    port = os.getenv("PORT", None)
    protocol = os.getenv("PROTOCOL", None)
    if port is None:
        if SSL_CERT.exists():
            port = "16443"
            protocol = "https"
        else:
            port = "16000"
            protocol = "http"
    elif protocol is None:
        protocol = "https" if port in ("443", "16443") else "http"

    return {
        "local":    get_local_ip(),
        "public":   get_public_ip(),
        "port":     port,
        "protocol": protocol,
    }

if __name__ == "__main__":
    ips = get_server_ips()
    print(f"Local IP: {ips['local']}")
    print(f"Public IP: {ips['public']}")
    print(f"Port: {ips['port']}")
