#!/usr/bin/env python3
"""
AUTORUN - Sistema de Vigilancia
Arranca todo desde cero: venv, dependencias, BD, servidor y navegador.
Uso: python autorun/startup.py
"""

import os
import sys
import subprocess
import time
import webbrowser
import urllib.request
import urllib.error
import socket
from pathlib import Path

# Rutas
PROJECT_DIR  = Path(__file__).resolve().parent.parent
BACKEND_DIR  = PROJECT_DIR / "backend"
VENV_DIR     = PROJECT_DIR / ".venv"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
REQ_LITE     = BACKEND_DIR / "requirements_lite.txt"
DB_FILE      = BACKEND_DIR / "vigilancia.db"

SERVER_HOST  = "127.0.0.1"
SERVER_PORT  = 16000
SERVER_URL   = f"http://{SERVER_HOST}:{SERVER_PORT}"
HEALTH_URL   = f"{SERVER_URL}/api/health"

# Helpers

def banner(msg, char="="):
    line = char * 60
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

def wait_server(url, timeout=60, interval=1):
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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# Pasos

def step_venv():
    banner("PASO 1 -- Entorno virtual")
    if VENV_DIR.exists():
        ok(f"Venv encontrado en {VENV_DIR}")
        return True
    info("Creando entorno virtual (.venv) ...")
    if run([sys.executable, "-m", "venv", str(VENV_DIR)]):
        ok("Venv creado")
        return True
    err("No se pudo crear el venv")
    return False

def step_deps(python_exe):
    banner("PASO 2 -- Dependencias")
    req = REQ_LITE if REQ_LITE.exists() else REQUIREMENTS
    if not req.exists():
        err(f"No se encontro requirements en {BACKEND_DIR}")
        return False
    info(f"Instalando desde {req.name} (puede tardar en la primera ejecucion) ...")
    run([str(python_exe), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    ok_flag = run([str(python_exe), "-m", "pip", "install", "--quiet", "-r", str(req)])
    if ok_flag:
        ok("Dependencias instaladas")
    else:
        info("Algunos paquetes pueden haber fallado, continuando de todos modos ...")
    return True

def step_database(python_exe):
    banner("PASO 3 -- Base de datos")
    if DB_FILE.exists():
        ok(f"Base de datos encontrada: {DB_FILE.name}")
        return True
    info("Inicializando base de datos y creando usuario admin ...")
    setup_script = BACKEND_DIR / "setup_admin.py"
    if setup_script.exists():
        if run([str(python_exe), str(setup_script)], cwd=BACKEND_DIR):
            ok("Base de datos inicializada con usuario admin (admin/admin)")
        else:
            info("setup_admin.py fallo, intentando con init_db.py ...")
            init_script = PROJECT_DIR / "utilidades" / "init_db.py"
            if init_script.exists():
                run([str(python_exe), str(init_script)], cwd=PROJECT_DIR)
    else:
        info("setup_admin.py no encontrado, el servidor creara la BD al arrancar")
    return True

def step_server(python_exe):
    banner("PASO 4 -- Servidor FastAPI (HTTP :16000)")
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            if r.status == 200:
                ok(f"Servidor ya esta corriendo en {SERVER_URL}")
                return None
    except Exception:
        pass

    info("Arrancando uvicorn ...")
    log_file = open(PROJECT_DIR / "autorun" / "server.log", "w")
    proc = subprocess.Popen(
        [
            str(python_exe), "-m", "uvicorn", "app:app",
            "--host", "0.0.0.0",
            "--port", str(SERVER_PORT),
            "--log-level", "info"
        ],
        cwd=BACKEND_DIR,
        stdout=log_file,
        stderr=log_file
    )
    ok(f"Servidor iniciado (PID {proc.pid}) -- log: autorun/server.log")
    return proc

def step_ready(proc):
    banner("PASO 5 -- Verificar servidor listo")
    if not wait_server(HEALTH_URL, timeout=90):
        err("El servidor no respondio en 90s. Revisa autorun/server.log")
        if proc:
            proc.terminate()
        sys.exit(1)
    print()
    ok(f"Servidor listo en {SERVER_URL}")

_tunnel_url = None

def step_tunnel():
    global _tunnel_url
    banner("PASO 6 -- Tunel publico")
    try:
        tunnel_module = PROJECT_DIR / "autorun" / "tunnel.py"
        if not tunnel_module.exists():
            info("tunnel.py no encontrado -- saltando tunel")
            return None
        import importlib.util
        spec = importlib.util.spec_from_file_location("tunnel", tunnel_module)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        proc, url = mod.start_tunnel(SERVER_PORT)
        if url:
            _tunnel_url = url
            ok(f"Tunel activo: {url}")
            ok(f"Camara publica: {url}/camara-cliente")
        else:
            info("Tunel iniciado, esperando URL...")
        return proc
    except Exception as e:
        info(f"Tunel no disponible: {e}")
        return None

def step_browser():
    banner("PASO 7 -- Abrir navegador")
    info(f"Abriendo {SERVER_URL} ...")
    webbrowser.open(SERVER_URL)
    ok("Navegador abierto")

def step_summary():
    local_ip = get_local_ip()
    banner("SISTEMA LISTO", char="*")
    tunnel_line = f"  Tunel publico:      {_tunnel_url}" if _tunnel_url else ""
    tunnel_cam  = f"  Camara (internet):  {_tunnel_url}/camara-cliente" if _tunnel_url else "  Tunel: no activo"
    print(f"""
  Panel local:        {SERVER_URL}
  Red LAN:            http://{local_ip}:{SERVER_PORT}
{tunnel_line}

  Camara LAN:         http://{local_ip}:{SERVER_PORT}/camara-cliente
{tunnel_cam}
  API docs:           {SERVER_URL}/api/docs

  Credenciales:       admin / admin

  Presiona Ctrl+C para detener todo.
""")

# Main

def main():
    banner("AUTORUN -- SISTEMA DE VIGILANCIA", char="*")

    # Paso 1 - Venv
    if not step_venv():
        sys.exit(1)

    python_exe = get_python()
    if not python_exe.exists():
        err(f"Python del venv no encontrado: {python_exe}")
        sys.exit(1)
    ok(f"Python: {python_exe}")

    # Paso 2 - Dependencias
    step_deps(python_exe)

    # Paso 3 - Base de datos
    step_database(python_exe)

    # Paso 4 - Servidor
    proc = step_server(python_exe)

    # Paso 5 - Esperar
    step_ready(proc)

    # Paso 6 - Tunel
    proc_tunnel = step_tunnel()

    # Paso 7 - Navegador
    step_browser()

    # Resumen
    step_summary()

    # Mantener vivo
    if proc is not None:
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n\n  Deteniendo servidor ...")
            proc.terminate()
            if proc_tunnel:
                proc_tunnel.terminate()
            print("  Servidor detenido. Hasta pronto.")


if __name__ == "__main__":
    main()
