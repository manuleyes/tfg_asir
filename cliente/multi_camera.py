#!/usr/bin/env python3
"""
Multi-Camera Client - Ejecutar múltiples clientes en paralelo
Útil para testing con varias cámaras simultáneamente
"""

import threading
import time
import logging
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiCameraStreamer:
    """Manejador de múltiples cámaras"""
    
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 5005):
        self.server_host = server_host
        self.server_port = server_port
        self.clients: List = []
        self.threads: List = []
    
    def add_camera(
        self,
        camera_id: str,
        camera_source,  # 0=webcam, "rtsp://..." = IP cam, "video.mp4" = file
        resolution=(640, 480),
        fps=15
    ):
        """Agregar cámara"""
        
        try:
            from cliente import CameraClient
            
            client = CameraClient(
                camera_id=camera_id,
                camera_source=camera_source,
                server_host=self.server_host,
                server_port=self.server_port,
                resolution=resolution,
                fps=fps
            )
            
            self.clients.append({
                'id': camera_id,
                'client': client,
                'source': camera_source
            })
            
            logger.info(f" Camera added: {camera_id}")
        
        except Exception as e:
            logger.error(f" Failed to add camera {camera_id}: {e}")
    
    def start_all(self):
        """Iniciar todos los clientes"""
        
        for camera in self.clients:
            def run(client_data):
                camera_id = client_data['id']
                client = client_data['client']
                
                logger.info(f"🎬 Starting {camera_id}...")
                
                if client.start():
                    logger.info(f" {camera_id} streaming")
                    
                    # Keep running
                    try:
                        while True:
                            time.sleep(30)
                            client.print_stats()
                    
                    except KeyboardInterrupt:
                        pass
                    
                    finally:
                        client.stop()
                        logger.info(f"⏹️ {camera_id} stopped")
                
                else:
                    logger.error(f" {camera_id} failed to start")
            
            thread = threading.Thread(
                target=run,
                args=(camera,),
                name=f"Camera-{camera['id']}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        
        logger.info(f" Started {len(self.threads)} camera threads")
    
    def stop_all(self):
        """Detener todos los clientes"""
        
        for camera in self.clients:
            camera['client'].stop()
        
        logger.info(" All cameras stopped")
    
    def print_all_stats(self):
        """Imprimir stats de todos"""
        
        logger.info("\n" + "="*60)
        logger.info("📊 MULTI-CAMERA STATS")
        logger.info("="*60)
        
        for camera in self.clients:
            stats = camera['client'].get_stats()
            logger.info(f"""
{camera['id']}:
  Frames: {stats['frames_sent']}
  Data: {stats['bytes_sent'] / (1024*1024):.2f} MB
  Avg FPS: {stats['avg_fps']}
  Queue: {stats['queue_size']}
            """)


def run_multi_camera_demo():
    """
    Ejemplo: 3 cámaras simultáneamente
    - Webcam local
    - Cámara IP (simulada con video file)
    - Otro video file
    """
    
    logger.info("""
╔════════════════════════════════════════════════════════╗
║     📹 MULTI-CAMERA STREAMING DEMO
╚════════════════════════════════════════════════════════╝
    """)
    
    streamer = MultiCameraStreamer(
        server_host="127.0.0.1",
        server_port=5005
    )
    
    # Agregar cámaras
    # Nota: Puedes cambiar los source según tus cámaras disponibles
    
    # Cámara 1: Webcam local
    streamer.add_camera(
        camera_id="WEBCAM_OFFICE",
        camera_source=0,  # Webcam
        resolution=(640, 480),
        fps=15
    )
    
    # Cámara 2: Archivo de video (si existe)
    import os
    if os.path.exists("sample.mp4"):
        streamer.add_camera(
            camera_id="RECORDED_LOBBY",
            camera_source="sample.mp4",
            resolution=(1280, 720),
            fps=30
        )
    
    # Cámara 3: Cámara IP (descomenta si tienes disponible)
    # streamer.add_camera(
    #     camera_id="HIKVISION_HALL",
    #     camera_source="rtsp://admin:password@192.168.1.50:554/stream1",
    #     resolution=(1920, 1080),
    #     fps=25
    # )
    
    # Iniciar streaming
    streamer.start_all()
    
    # Loop de monitoreo
    try:
        while True:
            time.sleep(30)
            streamer.print_all_stats()
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping...")
        streamer.stop_all()


# Configuración alternativa: Desde archivo
def load_cameras_from_config(config_file: str = "cameras.json"):
    """
    Cargar configuración de cámaras desde JSON
    
    Ejemplo cameras.json:
    {
        "server_host": "192.168.1.100",
        "server_port": 5005,
        "cameras": [
            {
                "id": "CAM_01",
                "source": 0,
                "resolution": [640, 480],
                "fps": 15
            },
            {
                "id": "CAM_02",
                "source": "rtsp://admin:pass@192.168.1.50/stream1",
                "resolution": [1280, 720],
                "fps": 25
            }
        ]
    }
    """
    
    import json
    
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        streamer = MultiCameraStreamer(
            server_host=config.get('server_host', '127.0.0.1'),
            server_port=config.get('server_port', 5005)
        )
        
        for cam_config in config.get('cameras', []):
            streamer.add_camera(
                camera_id=cam_config['id'],
                camera_source=cam_config['source'],
                resolution=tuple(cam_config.get('resolution', [640, 480])),
                fps=cam_config.get('fps', 15)
            )
        
        return streamer
    
    except Exception as e:
        logger.error(f" Failed to load config: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        # Cargar desde archivo
        config_file = sys.argv[2] if len(sys.argv) > 2 else "cameras.json"
        streamer = load_cameras_from_config(config_file)
        
        if streamer:
            streamer.start_all()
            
            try:
                while True:
                    time.sleep(30)
                    streamer.print_all_stats()
            except KeyboardInterrupt:
                streamer.stop_all()
    
    else:
        # Demo
        run_multi_camera_demo()
