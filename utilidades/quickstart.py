#!/usr/bin/env python3
"""
Quick Start Script - Configuración rápida del sistema
"""
import sys
import os
from pathlib import Path
import subprocess
import platform

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_python():
    """Verificar versión de Python"""
    print_header("1. Verificando Python")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f" Python 3.10+ requerido, tienes {version.major}.{version.minor}")
        return False
    
    print(f" Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_git():
    """Verificar Git"""
    print_header("2. Verificando Git")
    
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f" {result.stdout.strip()}")
            return True
    except:
        pass
    
    print(" Git no instalado")
    print("   Windows: https://git-scm.com/download/win")
    print("   macOS: brew install git")
    print("   Linux: apt install git")
    return False

def create_venv():
    """Crear entorno virtual"""
    print_header("3. Creando Entorno Virtual")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print(" Entorno virtual ya existe")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print(" Entorno virtual creado")
        return True
    except Exception as e:
        print(f" Error: {e}")
        return False

def install_dependencies():
    """Instalar dependencias"""
    print_header("4. Instalando Dependencias")
    
    # Determinar ejecutable pip
    if platform.system() == "Windows":
        pip_cmd = ["venv\\Scripts\\pip"]
    else:
        pip_cmd = ["venv/bin/pip"]
    
    try:
        print("⏳ Instalando packages... (esto puede tomar 5-10 minutos)")
        subprocess.run(pip_cmd + ["install", "-r", "backend/requirements.txt"], check=True)
        print(" Dependencias instaladas")
        return True
    except Exception as e:
        print(f" Error: {e}")
        return False

def init_database():
    """Inicializar base de datos"""
    print_header("5. Inicializando Base de Datos")
    
    python_cmd = Path("venv/Scripts/python" if platform.system() == "Windows" else "venv/bin/python")
    
    try:
        print("⏳ Creando tablas y datos de prueba...")
        subprocess.run([str(python_cmd), "init_db.py"], check=True)
        print(" Base de datos inicializada")
        return True
    except Exception as e:
        print(f" Error: {e}")
        return False

def run_tests():
    """Ejecutar tests"""
    print_header("6. Ejecutando Tests")
    
    python_cmd = Path("venv/Scripts/python" if platform.system() == "Windows" else "venv/bin/python")
    
    try:
        print("⏳ Corriendo suite de tests...")
        subprocess.run([str(python_cmd), "test_suite.py"], check=True)
        print(" Todos los tests pasaron")
        return True
    except Exception as e:
        print(f" Error en tests: {e}")
        return False

def show_next_steps():
    """Mostrar próximos pasos"""
    print_header("7. Próximos Pasos")
    
    activate_cmd = "venv\\Scripts\\activate" if platform.system() == "Windows" else "source venv/bin/activate"
    
    print(f"""
Para empezar a usar el sistema:

1. Activar entorno virtual:
   {activate_cmd}

2. Iniciar servidor backend:
   cd backend
   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

3. Abrir en navegador:
   http://localhost:8000/dashboard

4. Credenciales de demo:
   Usuario: admin
   Contraseña: admin123

📚 Documentación:
   - INSTALL.md       - Instalación detallada
   - USER_MANUAL.md   - Manual de usuario
   - TECHNICAL_GUIDE.md - Guía técnica
   - DEPLOYMENT_GUIDE.md - Deployment/Docker

🧪 Tests:
   python test_api.py              # Tests API rápidos
   python test_yolo_detection.py   # Test detección
   python test_pdf_reports.py      # Test reportes
   python test_suite.py            # Suite completa

¡Bienvenido al Sistema de Vigilancia Inteligente! 🎥
""")

def main():
    """Ejecutar configuración"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*18 + "SISTEMA DE VIGILANCIA - QUICK START" + " "*14 + "║")
    print("╚" + "="*68 + "╝")
    
    steps = [
        ("Python", check_python),
        ("Git", check_git),
        ("Venv", create_venv),
        ("Dependencies", install_dependencies),
        ("Database", init_database),
        ("Tests", run_tests),
    ]
    
    for i, (name, func) in enumerate(steps, 1):
        try:
            if not func():
                print(f"\n Error en paso {i}: {name}")
                print("\nPara más información, ver:")
                print("  - INSTALL.md")
                print("  - TECHNICAL_GUIDE.md")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n Instalación cancelada por usuario")
            sys.exit(0)
    
    show_next_steps()
    
    print("\n Instalación completada exitosamente!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
