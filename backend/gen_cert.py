"""
gen_cert.py — Genera un certificado SSL autofirmado válido para:
  - localhost
  - 127.0.0.1
  - IP local de la red (detectada automáticamente)
  - IP pública (si se proporciona)

Requiere: pip install cryptography  (ya incluida en requirements)
Uso:      python gen_cert.py
Salida:   backend/ssl/cert.pem  y  backend/ssl/key.pem
"""

import os
import socket
import datetime
import ipaddress
from pathlib import Path

# ── Importaciones de cryptography ─────────────────────────────────────────────
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

SSL_DIR  = Path(__file__).parent / "ssl"
CERT_FILE = SSL_DIR / "cert.pem"
KEY_FILE  = SSL_DIR / "key.pem"
DAYS_VALID = 825  # máximo aceptado por iOS/Android


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.0.1"


def generate_cert(extra_ips=None, extra_hosts=None):
    SSL_DIR.mkdir(exist_ok=True)

    local_ip = get_local_ip()
    print(f"  IP local detectada: {local_ip}")

    # ── Clave privada RSA 2048 ─────────────────────────────────────────────────
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # ── Subject / Issuer ───────────────────────────────────────────────────────
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Vigilancia Inteligente"),
        x509.NameAttribute(NameOID.COMMON_NAME, "vigilancia.local"),
    ])

    # ── SANs (Subject Alternative Names) ──────────────────────────────────────
    san_dns  = [x509.DNSName("localhost"), x509.DNSName("vigilancia.local")]
    san_ips  = [
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv4Address(local_ip)),
    ]

    if extra_hosts:
        for h in extra_hosts:
            san_dns.append(x509.DNSName(h))
    if extra_ips:
        for ip in extra_ips:
            try:
                san_ips.append(x509.IPAddress(ipaddress.IPv4Address(ip)))
            except Exception:
                pass

    san = x509.SubjectAlternativeName(san_dns + san_ips)

    # ── Certificado ───────────────────────────────────────────────────────────
    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=DAYS_VALID))
        .add_extension(san, critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_cert_sign=True, crl_sign=True,
                content_commitment=False, key_encipherment=True,
                data_encipherment=False, key_agreement=False,
                encipher_only=False, decipher_only=False
            ),
            critical=True
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                x509.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False
        )
        .sign(key, hashes.SHA256(), default_backend())
    )

    # ── Guardar archivos ──────────────────────────────────────────────────────
    with open(KEY_FILE, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"  Certificado generado:")
    print(f"    {CERT_FILE}")
    print(f"    {KEY_FILE}")
    print(f"  Válido hasta: {(now + datetime.timedelta(days=DAYS_VALID)).strftime('%Y-%m-%d')}")
    print(f"  SANs incluidos: localhost, 127.0.0.1, {local_ip}", end="")
    if extra_ips:
        print(f", {', '.join(extra_ips)}", end="")
    print()
    return str(CERT_FILE), str(KEY_FILE)


def install_cert_windows(cert_file: Path) -> bool:
    """Instala el certificado en el almacén raíz de confianza de Windows (requiere admin)."""
    import subprocess, sys
    if sys.platform != "win32":
        return False
    try:
        script = (
            f"Import-Certificate -FilePath '{cert_file}' "
            f"-CertStoreLocation 'Cert:\\LocalMachine\\Root'"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  Certificado instalado en almacén raíz de Windows (Chrome/Edge confiarán en él)")
            return True
        else:
            print(f"  No se pudo instalar automáticamente (necesita admin): {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  Error instalando certificado: {e}")
        return False


if __name__ == "__main__":
    import sys
    extra_ips = sys.argv[1:] if len(sys.argv) > 1 else []
    print("Generando certificado SSL autofirmado...")
    cert, key = generate_cert(extra_ips=extra_ips)
    print("\nInstalando en almacén de confianza de Windows...")
    installed = install_cert_windows(Path(cert))
    print("\nPara que el navegador confíe en el certificado sin aviso:")
    if not installed:
        print("  Windows: doble clic en cert.pem → Instalar → 'Entidades de certificación raíz de confianza'")
    print("  Android: Ajustes → Seguridad → Instalar certificado → cert.pem")
    print("  iOS:     Compartir cert.pem al iPhone → Ajustes → General → VPN y gestión → Instalar → Confiar")
