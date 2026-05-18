#!/usr/bin/env python3
"""
control.py — Consola de control del Sistema de Vigilancia
==========================================
Comandos disponibles:
  start   — Inicia el servidor (+ túnel opcional)
  stop    — Para el servidor y el túnel
  restart — Para y vuelve a iniciar
  status  — Muestra el estado actual
  log     — Muestra las últimas líneas del log del servidor
  tunnel  — Inicia/detiene el túnel SSH por separado
  help    — Muestra esta ayuda
  exit    — Sale de la consola
"""

import os
import sys
import time
import signal
import socket
import threading
import subprocess
import importlib.util
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────
#  Rutas
# ─────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_DIR / "backend"
VENV_DIR    = PROJECT_DIR / ".venv"
REQ_LITE    = BACKEND_DIR / "requirements_lite.txt"
REQUIREMENTS= BACKEND_DIR / "requirements.txt"
SSL_CERT    = BACKEND_DIR / "ssl" / "cert.pem"
SSL_KEY     = BACKEND_DIR / "ssl" / "key.pem"
DB_FILE     = BACKEND_DIR / "vigilancia.db"
LOG_FILE    = PROJECT_DIR / "autorun" / "server_https.log"
TUNNEL_PY   = PROJECT_DIR / "autorun" / "tunnel.py"

SERVER_HOST = "127.0.0.1"
HTTP_PORT   = 16000
HTTPS_PORT  = 16443

# ─────────────────────────────────────────
#  Estado global
# ─────────────────────────────────────────
_server_proc: subprocess.Popen = None
_tunnel_proc: subprocess.Popen = None
_tunnel_url: str = None

# ─────────────────────────────────────────
#  Colores ANSI (Windows 10+ los soporta)
# ─────────────────────────────────────────
if sys.platform == "win32":
    os.system("")  # habilita secuencias ANSI en Windows

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"

def ok(msg):   print(f"  {C.GREEN}[OK]{C.RESET}  {msg}")
def err(msg):  print(f"  {C.RED}[ERR]{C.RESET} {msg}")
def info(msg): print(f"  {C.CYAN}[..]{C.RESET}  {msg}")
def warn(msg): print(f"  {C.YELLOW}[!]{C.RESET}   {msg}")

def banner():
    print(f"""
{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════╗
║     SISTEMA DE VIGILANCIA INTELIGENTE — CONTROL      ║
╚══════════════════════════════════════════════════════╝{C.RESET}
  Escribe {C.BOLD}help{C.RESET} para ver los comandos disponibles.
""")

# ─────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────
def get_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def server_responding() -> bool:
    """Comprueba si el servidor responde en HTTP o HTTPS."""
    for port, scheme in [(HTTPS_PORT, "https"), (HTTP_PORT, "http")]:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            url = f"{scheme}://{SERVER_HOST}:{port}/api/health"
            with urllib.request.urlopen(url, timeout=2, context=ctx if scheme=="https" else None):
                return True
        except Exception:
            pass
    return False

def wait_server(timeout=90) -> bool:
    start = time.time()
    print(f"  {C.GRAY}", end="", flush=True)
    while time.time() - start < timeout:
        if server_responding():
            print(f"{C.RESET}")
            return True
        print(".", end="", flush=True)
        time.sleep(1)
    print(f"{C.RESET}")
    return False

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

# ─────────────────────────────────────────
#  Acciones
# ─────────────────────────────────────────
def do_start(args: list):
    global _server_proc

    # ── Ya está corriendo ──
    if _server_proc and _server_proc.poll() is None:
        if server_responding():
            warn("El servidor ya está en ejecución.")
            _print_urls()
            return
        else:
            warn("Proceso registrado pero no responde — reiniciando.")
            _server_proc.terminate()
            _server_proc = None

    # ── Verificar venv ──
    python = get_python()
    if not python.exists():
        err("Entorno virtual no encontrado. Ejecuta primero: python -m venv .venv")
        info("O usa el script autorun/startup.py para la configuración inicial completa.")
        return

    # ── Base de datos ──
    if not DB_FILE.exists():
        info("Base de datos no encontrada — inicializando...")
        setup = BACKEND_DIR / "setup_admin.py"
        if setup.exists():
            subprocess.run([str(python), str(setup)], cwd=BACKEND_DIR,
                           capture_output=True)
            ok("Base de datos inicializada (admin / admin123)")
        else:
            info("setup_admin.py no encontrado — el servidor la creará al arrancar.")

    # ── Certificado SSL ──
    if not SSL_CERT.exists():
        info("Certificado SSL no encontrado — generando...")
        gen = BACKEND_DIR / "gen_cert.py"
        if gen.exists():
            subprocess.run([str(python), str(gen)], cwd=BACKEND_DIR,
                           capture_output=True)
            ok("Certificado generado.")

    # ── Comando uvicorn ──
    cmd = [
        str(python), "-m", "uvicorn", "app:app",
        "--host", "0.0.0.0",
        "--port", str(HTTPS_PORT),
        "--log-level", "warning",
    ]
    if SSL_CERT.exists() and SSL_KEY.exists():
        cmd += ["--ssl-certfile", str(SSL_CERT), "--ssl-keyfile", str(SSL_KEY)]
        mode = f"HTTPS :{HTTPS_PORT}"
    else:
        cmd[5] = str(HTTP_PORT)  # sin SSL → puerto 16000
        mode = f"HTTP :{HTTP_PORT}"

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(LOG_FILE, "a")
    log_fh.write(f"\n\n{'='*50}\n[{ts()}] START\n{'='*50}\n")
    log_fh.flush()

    info(f"Arrancando servidor {mode} ...")
    _server_proc = subprocess.Popen(cmd, cwd=BACKEND_DIR,
                                    stdout=log_fh, stderr=log_fh)
    ok(f"Proceso iniciado (PID {_server_proc.pid})")

    if wait_server():
        ok(f"Servidor listo.")
        _print_urls()
        # Túnel automático si se pasa --tunnel
        if "--tunnel" in args or "-t" in args:
            do_tunnel([])
    else:
        err("El servidor no respondió en 90 s. Revisa el log:")
        info(f"  {LOG_FILE}")


def do_stop(args: list):
    global _server_proc, _tunnel_proc, _tunnel_url

    stopped_any = False

    if _tunnel_proc and _tunnel_proc.poll() is None:
        _tunnel_proc.terminate()
        try:
            _tunnel_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _tunnel_proc.kill()
        _tunnel_proc = None
        _tunnel_url  = None
        # Remove tunnel URL file so backend stops advertising it
        try:
            tunnel_file = PROJECT_DIR / "autorun" / "tunnel_url.txt"
            if tunnel_file.exists():
                tunnel_file.unlink()
        except Exception:
            pass
        ok("Túnel SSH detenido.")
        stopped_any = True

    if _server_proc and _server_proc.poll() is None:
        info("Deteniendo servidor...")
        _server_proc.terminate()
        try:
            _server_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            warn("No respondió en 10 s — forzando kill.")
            _server_proc.kill()
        _server_proc = None
        ok("Servidor detenido.")
        stopped_any = True

    if not stopped_any:
        warn("No hay ningún proceso en ejecución registrado.")
        # Intento extra: matar uvicorn por puerto
        if sys.platform == "win32":
            for port in (HTTPS_PORT, HTTP_PORT):
                r = subprocess.run(
                    f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port}\') do taskkill /F /PID %a',
                    shell=True, capture_output=True
                )
                if r.returncode == 0:
                    ok(f"Proceso en :{port} terminado.")


def do_restart(args: list):
    do_stop([])
    time.sleep(1)
    do_start(args)


def do_status(args: list):
    global _server_proc, _tunnel_proc, _tunnel_url

    print()
    # Proceso servidor
    if _server_proc and _server_proc.poll() is None:
        alive = f"{C.GREEN}CORRIENDO{C.RESET} (PID {_server_proc.pid})"
    else:
        alive = f"{C.RED}DETENIDO{C.RESET}"

    # Conectividad real
    responding = server_responding()
    net_status = f"{C.GREEN}responde{C.RESET}" if responding else f"{C.RED}no responde{C.RESET}"

    # Túnel
    if _tunnel_proc and _tunnel_proc.poll() is None:
        t_status = f"{C.GREEN}ACTIVO{C.RESET}"
        t_url    = _tunnel_url or "URL desconocida"
    else:
        t_status = f"{C.GRAY}INACTIVO{C.RESET}"
        t_url    = "—"

    print(f"  Servidor  : {alive}  ({net_status})")
    print(f"  Túnel SSH : {t_status}  {t_url}")
    print(f"  Log       : {LOG_FILE}")
    if responding:
        _print_urls()
    print()


def do_log(args: list):
    lines = 30
    for a in args:
        if a.lstrip("-").isdigit():
            lines = int(a.lstrip("-"))

    if not LOG_FILE.exists():
        warn(f"Log no encontrado: {LOG_FILE}")
        return

    with open(LOG_FILE, "r", errors="replace") as f:
        content = f.readlines()

    tail = content[-lines:]
    print(f"\n{C.GRAY}{'─'*54}")
    print(f"  LOG — últimas {len(tail)} líneas de {LOG_FILE.name}")
    print(f"{'─'*54}{C.RESET}")
    for line in tail:
        print(f"  {line}", end="")
    print(f"\n{C.GRAY}{'─'*54}{C.RESET}\n")


def do_tunnel(args: list):
    global _tunnel_proc, _tunnel_url

    # Detener túnel activo
    if "--stop" in args or "-s" in args:
        if _tunnel_proc and _tunnel_proc.poll() is None:
            _tunnel_proc.terminate()
            _tunnel_proc = None
            _tunnel_url  = None
            try:
                tunnel_file = PROJECT_DIR / "autorun" / "tunnel_url.txt"
                if tunnel_file.exists():
                    tunnel_file.unlink()
            except Exception:
                pass
            ok("Túnel detenido.")
        else:
            warn("No hay túnel activo.")
        return

    if _tunnel_proc and _tunnel_proc.poll() is None:
        warn(f"Túnel ya activo: {_tunnel_url or '(URL pendiente)'}")
        return

    if not TUNNEL_PY.exists():
        err(f"No se encontró tunnel.py en {TUNNEL_PY}")
        return

    spec = importlib.util.spec_from_file_location("tunnel", TUNNEL_PY)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    info("Iniciando túnel SSH → localhost.run ...")

    def _on_url(url: str):
        global _tunnel_url
        _tunnel_url = url
        # Write to file so the running backend can read it
        try:
            TUNNEL_URL_FILE = PROJECT_DIR / "autorun" / "tunnel_url.txt"
            TUNNEL_URL_FILE.write_text(url, encoding="utf-8")
        except Exception as exc:
            warn(f"No se pudo escribir tunnel_url.txt: {exc}")

    _tunnel_proc, url = mod.start_tunnel(HTTP_PORT, on_url=_on_url)
    if url:
        _tunnel_url = url
        ok(f"Túnel activo: {url}")
        ok(f"Cámara pública: {url}/camara-cliente")
    else:
        info("Túnel iniciado, esperando URL...")


def do_help(args: list):
    print(f"""
{C.BOLD}Comandos disponibles:{C.RESET}

  {C.GREEN}start{C.RESET}             Inicia el servidor FastAPI
  {C.GREEN}start --tunnel{C.RESET}    Inicia el servidor y el túnel SSH público
  {C.GREEN}stop{C.RESET}              Para el servidor (y el túnel si está activo)
  {C.GREEN}restart{C.RESET}           Para y reinicia el servidor
  {C.GREEN}status{C.RESET}            Muestra el estado actual
  {C.GREEN}log{C.RESET}               Muestra las últimas 30 líneas del log
  {C.GREEN}log 50{C.RESET}            Muestra las últimas N líneas del log
  {C.GREEN}tunnel{C.RESET}            Inicia el túnel SSH por separado
  {C.GREEN}tunnel --stop{C.RESET}     Detiene el túnel SSH
  {C.GREEN}help{C.RESET}              Muestra esta ayuda
  {C.GREEN}exit{C.RESET} / {C.GREEN}quit{C.RESET}      Sale de la consola
""")


def _print_urls():
    local_ip = _get_local_ip()
    t = _tunnel_url
    print(f"""
  {C.BOLD}URLs de acceso:{C.RESET}
    Local     →  https://{SERVER_HOST}:{HTTPS_PORT}
    Red local →  https://{local_ip}:{HTTPS_PORT}
    Público   →  {t if t else C.GRAY + '(túnel no activo)' + C.RESET}
    Dashboard →  https://{SERVER_HOST}:{HTTPS_PORT}/dashboard
    API docs  →  https://{SERVER_HOST}:{HTTPS_PORT}/api/docs
""")


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# ─────────────────────────────────────────
#  Dispatch de comandos
# ─────────────────────────────────────────
COMMANDS = {
    "start":   do_start,
    "stop":    do_stop,
    "restart": do_restart,
    "status":  do_status,
    "log":     do_log,
    "tunnel":  do_tunnel,
    "help":    do_help,
}

def dispatch(line: str):
    parts = line.strip().split()
    if not parts:
        return
    cmd  = parts[0].lower()
    args = parts[1:]

    if cmd in ("exit", "quit", "q"):
        _shutdown()
        sys.exit(0)

    fn = COMMANDS.get(cmd)
    if fn:
        try:
            fn(args)
        except KeyboardInterrupt:
            print()
            warn("Operación interrumpida.")
        except Exception as e:
            err(f"Error inesperado: {e}")
    else:
        warn(f"Comando desconocido: '{cmd}'. Escribe 'help' para ver los comandos.")


def _shutdown():
    global _server_proc, _tunnel_proc
    if _tunnel_proc and _tunnel_proc.poll() is None:
        _tunnel_proc.terminate()
    if _server_proc and _server_proc.poll() is None:
        info("Deteniendo servidor antes de salir...")
        _server_proc.terminate()
        try:
            _server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _server_proc.kill()
    ok("Hasta luego.")

# ─────────────────────────────────────────
#  Main loop
# ─────────────────────────────────────────
def main():
    banner()

    # Soporta argumentos directos: python control.py start
    if len(sys.argv) > 1:
        dispatch(" ".join(sys.argv[1:]))
        # Si es start/restart, quedarse en el loop interactivo
        if sys.argv[1].lower() not in ("start", "restart"):
            return

    try:
        while True:
            try:
                line = input(f"{C.BOLD}{C.CYAN}vigilancia>{C.RESET} ").strip()
            except EOFError:
                break
            if line:
                dispatch(line)
    except KeyboardInterrupt:
        print()
    finally:
        _shutdown()


if __name__ == "__main__":
    main()
