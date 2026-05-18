#!/usr/bin/env python3
"""
setup.py - Instalador automático del Sistema de Vigilancia Inteligente
=======================================================================
Ejecutar UNA sola vez tras clonar el repositorio:

    python setup.py

Realiza automáticamente:
  1. Crea el entorno virtual (.venv)
  2. Instala todas las dependencias
  3. Descarga el modelo YOLOv8x (~131 MB)
  4. Inicializa la base de datos con usuario admin
  5. Arranca el servidor y abre el navegador

Requisitos previos: Python 3.10+ y conexión a internet.
"""

import os
import sys
import subprocess
import time
import webbrowser
import urllib.request
import urllib.error
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
PROJECT_DIR  = Path(__file__).resolve().parent
BACKEND_DIR  = PROJECT_DIR / "backend"
VENV_DIR     = PROJECT_DIR / ".venv"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
MODEL_PATH   = BACKEND_DIR / "yolov8x.pt"
DB_FILE      = BACKEND_DIR / "vigilancia.db"

SERVER_HOST  = "127.0.0.1"
SERVER_PORT  = 16000
SERVER_URL   = f"http://{SERVER_HOST}:{SERVER_PORT}"
HEALTH_URL   = f"{SERVER_URL}/api/health"

# ─── Helpers ──────────────────────────────────────────────────────────────────
def banner(msg, char="="):
    line = char * 62
    print(f"\n{line}\n  {msg}\n{line}")

def ok(msg):   print(f"  [OK]  {msg}")
def err(msg):  print(f"  [ERR] {msg}")
def info(msg): print(f"        {msg}")

def get_python():
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def run(cmd, cwd=None, capture=False):
    try:
        kw = dict(cwd=cwd or PROJECT_DIR, text=True)
        if capture:
            kw.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = subprocess.run(cmd, **kw)
        return result.returncode == 0
    except Exception as e:
        err(f"Error ejecutando {cmd[0]}: {e}")
        return False

def wait_server(url, timeout=90, interval=1):
    info(f"Esperando servidor en {url} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(interval)
        print(".", end="", flush=True)
    print()
    return False

# ─── Pasos ────────────────────────────────────────────────────────────────────

def step_check_python():
    banner("PASO 0 — Verificar Python")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        err(f"Python 3.10+ requerido. Tienes {v.major}.{v.minor}.")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


def step_venv():
    banner("PASO 1 — Entorno virtual")
    if VENV_DIR.exists():
        ok(f"Ya existe: {VENV_DIR}")
        return
    info("Creando .venv ...")
    if run([sys.executable, "-m", "venv", str(VENV_DIR)]):
        ok(".venv creado")
    else:
        err("No se pudo crear el entorno virtual")
        sys.exit(1)


def step_deps():
    banner("PASO 2 — Dependencias")
    python_exe = get_python()
    if not REQUIREMENTS.exists():
        err(f"No se encontró {REQUIREMENTS}")
        sys.exit(1)
    info("Actualizando pip ...")
    run([str(python_exe), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    info(f"Instalando desde {REQUIREMENTS.name} (puede tardar varios minutos) ...")
    if run([str(python_exe), "-m", "pip", "install", "--quiet", "-r", str(REQUIREMENTS)]):
        ok("Dependencias instaladas")
    else:
        info("Algunos paquetes pueden haber fallado — continuando de todos modos")


def step_download_model():
    banner("PASO 3 — Modelo YOLOv8x")
    if MODEL_PATH.exists():
        size_mb = MODEL_PATH.stat().st_size / 1_048_576
        ok(f"Modelo ya presente ({size_mb:.0f} MB): {MODEL_PATH.name}")
        return

    info("Descargando yolov8x.pt mediante ultralytics (~131 MB) ...")
    python_exe = get_python()

    # ultralytics descarga automáticamente el modelo al importarlo con el nombre
    code = (
        "from ultralytics import YOLO; "
        f"import shutil, pathlib; "
        f"m = YOLO('yolov8x.pt'); "  # descarga a ~/.cache/ultralytics si no existe
        f"src = pathlib.Path(m.ckpt_path); "
        f"dst = pathlib.Path(r'{MODEL_PATH}'); "
        f"dst.parent.mkdir(parents=True, exist_ok=True); "
        f"shutil.copy(src, dst); "
        f"print('Copiado a', dst)"
    )

    if run([str(python_exe), "-c", code]):
        if MODEL_PATH.exists():
            ok(f"Modelo descargado: {MODEL_PATH.name}")
        else:
            err("El archivo no apareció en backend/. Revisa la salida de ultralytics.")
    else:
        err("Descarga fallida. Asegúrate de tener conexión a internet y ultralytics instalado.")
        info("Puedes intentarlo manualmente después:")
        info("  python -c \"from ultralytics import YOLO; YOLO('yolov8x.pt')\"")
        info(f"  Y copiar el .pt a {MODEL_PATH}")


def step_database():
    banner("PASO 4 — Base de datos")
    python_exe = get_python()
    if DB_FILE.exists():
        ok(f"Base de datos ya existe: {DB_FILE.name}")
        return
    info("Inicializando BD y creando usuario admin ...")
    setup_script = BACKEND_DIR / "setup_admin.py"
    if setup_script.exists():
        if run([str(python_exe), str(setup_script)], cwd=BACKEND_DIR):
            ok("BD inicializada — usuario: admin / contraseña: admin")
        else:
            info("setup_admin.py falló; el servidor creará la BD al arrancar")
    else:
        info("setup_admin.py no encontrado; el servidor creará la BD al arrancar")


def step_server():
    banner("PASO 5 — Servidor")
    python_exe = get_python()

    # Comprobar si ya corre
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            if r.status == 200:
                ok(f"Servidor ya en marcha: {SERVER_URL}")
                return None
    except Exception:
        pass

    info("Arrancando uvicorn en background ...")
    log_file = open(PROJECT_DIR / "server.log", "w")
    proc = subprocess.Popen(
        [
            str(python_exe), "-m", "uvicorn", "app:app",
            "--host", "0.0.0.0",
            "--port", str(SERVER_PORT),
            "--log-level", "info",
        ],
        cwd=BACKEND_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    if wait_server(HEALTH_URL, timeout=90):
        ok(f"Servidor listo en {SERVER_URL}")
    else:
        err("El servidor no respondió en 90s. Revisa server.log")

    return proc


def step_open_browser():
    banner("PASO 6 — Navegador")
    url = f"{SERVER_URL}/dashboard"
    info(f"Abriendo {url} ...")
    webbrowser.open(url)
    ok("Listo")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 62)
    print("   SISTEMA DE VIGILANCIA INTELIGENTE — Instalación completa")
    print("=" * 62)

    step_check_python()
    step_venv()
    step_deps()
    step_download_model()
    step_database()
    proc = step_server()

    print("\n" + "=" * 62)
    print("  INSTALACIÓN COMPLETADA")
    print(f"  Dashboard : {SERVER_URL}/dashboard")
    print(f"  API Docs  : {SERVER_URL}/api/docs")
    print(f"  Login     : admin / admin  (cámbialo tras el primer acceso)")
    print("=" * 62 + "\n")

    step_open_browser()

    if proc:
        try:
            proc.wait()
        except KeyboardInterrupt:
            info("Deteniendo servidor...")
            proc.terminate()


if __name__ == "__main__":
    main()
