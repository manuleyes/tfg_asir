"""
Ejemplo: Multi-cámara local
Corre cliente y servidor en la misma máquina para testing
"""

import time
import threading
import logging
from pathlib import Path

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_client_demo():
    """Correr cliente de cámara"""
    
    try:
        from cliente import CameraClient, config
        
        # Configurar cliente
        config.CAMERA_SOURCE = 0  # Webcam
        config.CAMERA_ID = "DEMO_CAMERA_01"
        config.SERVER_HOST = "127.0.0.1"
        config.SERVER_PORT = 5005
        config.RESOLUTION = (640, 480)
        config.FPS = 15
        config.JPEG_QUALITY = 70
        
        # Crear cliente
        client = CameraClient(
            camera_id=config.CAMERA_ID,
            camera_source=config.CAMERA_SOURCE,
            server_host=config.SERVER_HOST,
            server_port=config.SERVER_PORT
        )
        
        # Iniciar
        if not client.start():
            logger.error(" Failed to start client")
            return
        
        logger.info(" Client started, streaming...")
        
        # Loop de stats
        while True:
            time.sleep(10)
            client.print_stats()
    
    except ImportError as e:
        logger.error(f" Import error: {e}")
        logger.info("   Asegúrate de estar en la carpeta correcta")
    
    except KeyboardInterrupt:
        logger.info("🛑 Client stopped")
        if 'client' in locals():
            client.stop()


def run_server_demo():
    """Correr servidor UDP"""
    
    try:
        from backend.services.udp_receiver import UDPStreamReceiver
        from backend.services.detection_pipeline import get_surveillance_pipeline
        
        logger.info("Initializing detection pipeline...")
        pipeline = get_surveillance_pipeline(camera_id="DEMO_CAMERA_01")
        
        # Callback para procesar frames
        def on_frame_received(camera_id, frame, metadata):
            """Procesar cada frame recibido"""
            
            if frame is None:
                logger.warning(f"️ Invalid frame from {camera_id}")
                return
            
            try:
                # Procesar con pipeline
                analysis, _ = pipeline.process_frame(frame)
                
                if analysis:
                    logger.info(f"""
╔════════════════════════════════════════════╗
║ 📊 FRAME ANALYSIS - {camera_id}
╠════════════════════════════════════════════╣
║ Frame ID:     {analysis.frame_id}
║ Detections:   {len(analysis.detections)}
║ Anomalies:    {len(analysis.anomalies)}
║ Alerts:       {len(analysis.alerts)}
║ Processing:   {analysis.processing_time_ms:.1f}ms
╚════════════════════════════════════════════╝
                    """)
                    
                    # Print detections
                    if analysis.detections:
                        logger.info("  Detections:")
                        for det in analysis.detections:
                            logger.info(f"    - {det.class_name} ({det.confidence:.2f})")
                    
                    # Print alerts
                    if analysis.alerts:
                        logger.warning("  🚨 ALERTS:")
                        for alert in analysis.alerts:
                            logger.warning(f"    - {alert['type']}: {alert}")
            
            except Exception as e:
                logger.error(f" Pipeline error: {e}")
        
        # Crear receptor
        receiver = UDPStreamReceiver(
            host="0.0.0.0",
            port=5005,
            frame_callback=on_frame_received
        )
        
        # Iniciar
        if not receiver.start():
            logger.error(" Failed to start receiver")
            return
        
        logger.info(" Server started, listening on port 5005...")
        
        # Loop de stats
        while True:
            time.sleep(10)
            receiver.print_stats()
    
    except ImportError as e:
        logger.error(f" Import error: {e}")
        logger.info("   Asegúrate de que backend está en PYTHONPATH")
    
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped")
        if 'receiver' in locals():
            receiver.stop()


def run_demo_both():
    """Correr cliente y servidor en threads separados"""
    
    logger.info("""
╔══════════════════════════════════════════════════════╗
║          🎬 CAMERA CLIENT/SERVER DEMO
╚══════════════════════════════════════════════════════╝
    """)
    
    # Thread para servidor
    server_thread = threading.Thread(
        target=run_server_demo,
        name="ServerThread",
        daemon=True
    )
    server_thread.start()
    
    # Wait para servidor iniciar
    time.sleep(2)
    
    # Thread para cliente
    client_thread = threading.Thread(
        target=run_client_demo,
        name="ClientThread",
        daemon=True
    )
    client_thread.start()
    
    try:
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping demo...")
        # Los threads son daemon, van a cerrarse


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "client":
            run_client_demo()
        elif sys.argv[1] == "server":
            run_server_demo()
        else:
            print("Usage:")
            print("  python demo.py client   - Run client only")
            print("  python demo.py server   - Run server only")
            print("  python demo.py both     - Run both (default)")
    else:
        run_demo_both()
