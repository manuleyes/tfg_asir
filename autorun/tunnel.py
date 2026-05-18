"""
tunnel.py - Tunel SSH hacia localhost.run.
URL HTTPS publica real sin instalar nada extra (usa SSH de Windows).
URL tipo: https://xxxxxxxxxxxx.lhr.life
"""

import subprocess
import sys
import re
import time
import threading


def start_tunnel(port: int = 16000, on_url=None):
    print(f"[TUNNEL] Iniciando tunel SSH -> http://localhost:{port} ...")
    proc = subprocess.Popen(
        [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-R", f"80:localhost:{port}",
            "nokey@localhost.run"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    url_found = [None]

    def _read():
        pattern = re.compile(r'https://[\w\-]+\.lhr\.life')
        for line in proc.stdout:
            line = line.strip()
            if line:
                m = pattern.search(line)
                if m and not url_found[0]:
                    url_found[0] = m.group(0)
                    print(f"\n{'='*60}")
                    print(f"  TUNEL ACTIVO - URL PUBLICA HTTPS")
                    print(f"  URL:            {url_found[0]}")
                    print(f"  Cliente camara: {url_found[0]}/camara-cliente")
                    print(f"{'='*60}\n")
                    if on_url:
                        on_url(url_found[0])

    t = threading.Thread(target=_read, daemon=True)
    t.start()

    deadline = time.time() + 30
    while time.time() < deadline and not url_found[0]:
        time.sleep(0.3)

    if not url_found[0]:
        print("[TUNNEL] URL no detectada en 30s, puede seguir iniciando...")

    return proc, url_found[0]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=16000)
    parser.add_argument("--wait", action="store_true", help="Bloquear hasta Ctrl+C")
    args = parser.parse_args()

    proc, url = start_tunnel(args.port)
    if not proc:
        sys.exit(1)

    if url:
        print(f"Abre en el movil: {url}/camara-cliente")

    if args.wait:
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n[TUNNEL] Deteniendo tunel...")
            proc.terminate()
    else:
        print(f"[TUNNEL] Tunel corriendo en segundo plano (PID {proc.pid})")
        print("         Ctrl+C en startup.py para detenerlo todo.")
