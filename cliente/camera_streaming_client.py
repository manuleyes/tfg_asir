"""
Cliente de Cámara para Streaming por UDP
Corre en: Cámaras IP, móviles, webcams, etc.
Transmite: Video comprimido por UDP al servidor central
"""

import cv2
import socket
import struct
import time
import logging
import threading
import numpy as np
from typing import Optional, Tuple
from collections import deque

from . import config
from .utils import compress_frame, serialize_packet, deserialize_packet

# Setup logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CameraClient:
    """
    Cliente de cámara que:
    - Captura frames de fuente local
    - Comprime en tiempo real
    - Transmite por UDP al servidor
    - Maneja reconexión automática
    """
    
    def __init__(
        self,
        camera_id: str = config.CAMERA_ID,
        camera_source: int = config.CAMERA_SOURCE,
        server_host: str = config.SERVER_HOST,
        server_port: int = config.SERVER_PORT,
        resolution: Tuple[int, int] = config.RESOLUTION,
        fps: int = config.FPS
    ):
        """
        Inicializar cliente
        
        Args:
            camera_id: Identificador único de cámara
            camera_source: 0=webcam, "rtsp://..." = cámara IP, "video.mp4" = archivo
            server_host: IP del servidor central
            server_port: Puerto UDP
            resolution: (width, height)
            fps: Frames por segundo
        """
        
        self.camera_id = camera_id
        self.camera_source = camera_source
        self.server_host = server_host
        self.server_port = server_port
        self.resolution = resolution
        self.fps = fps
        
        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_connected = False
        
        # UDP socket
        self.socket: Optional[socket.socket] = None
        self.server_address = (server_host, server_port)
        
        # Stats
        self.frame_count = 0
        self.bytes_sent = 0
        self.start_time = time.time()
        self.fps_counter = deque(maxlen=30)  # Last 30 frames
        
        # Threading
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.send_thread: Optional[threading.Thread] = None
        self.frame_queue = deque(maxlen=3)  # Buffer 3 frames max
        
        logger.info(f" CameraClient initialized: {camera_id}")
    
    def connect(self) -> bool:
        """Conectar a servidor y fuente de video"""
        
        # Try to open camera source
        try:
            self.cap = cv2.VideoCapture(self.camera_source)
            
            if not self.cap.isOpened():
                logger.error(f" Failed to open camera source: {self.camera_source}")
                return False
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            logger.info(f" Camera opened: {self.camera_source}")
        
        except Exception as e:
            logger.error(f" Camera error: {e}")
            return False
        
        # Create UDP socket
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
            logger.info(f" UDP socket created → {self.server_host}:{self.server_port}")
        
        except Exception as e:
            logger.error(f" Socket error: {e}")
            return False
        
        self.is_connected = True
        return True
    
    def start(self):
        """Iniciar streaming"""
        
        if not self.connect():
            logger.error(" Failed to connect")
            return False
        
        self.running = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start send thread
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        
        logger.info(f" Streaming started: {self.camera_id}")
        return True
    
    def stop(self):
        """Detener streaming"""
        
        self.running = False
        
        # Wait for threads
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.send_thread:
            self.send_thread.join(timeout=2)
        
        # Close resources
        if self.cap:
            self.cap.release()
        if self.socket:
            self.socket.close()
        
        logger.info(f" Streaming stopped: {self.camera_id}")
    
    def _capture_loop(self):
        """Loop de captura de frames"""
        
        frame_time = 1.0 / self.fps
        last_frame_time = time.time()
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("️ Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                # Resize if needed
                frame = cv2.resize(frame, self.resolution)
                
                # Compress frame
                compressed = compress_frame(frame, quality=config.JPEG_QUALITY)
                
                # Add to queue (overwrite if full)
                if len(self.frame_queue) >= 3:
                    self.frame_queue.popleft()
                
                self.frame_queue.append({
                    'frame': compressed,
                    'timestamp': time.time(),
                    'frame_id': self.frame_count
                })
                
                # FPS timing
                elapsed = time.time() - last_frame_time
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                
                last_frame_time = time.time()
            
            except Exception as e:
                logger.error(f" Capture error: {e}")
                time.sleep(0.1)
    
    def _send_loop(self):
        """Loop de envío de frames"""
        
        while self.running:
            try:
                if not self.frame_queue:
                    time.sleep(0.01)
                    continue
                
                # Get latest frame
                frame_data = self.frame_queue[-1]
                
                # Serialize packet
                packet = serialize_packet(
                    camera_id=self.camera_id,
                    frame_id=frame_data['frame_id'],
                    timestamp=frame_data['timestamp'],
                    frame_data=frame_data['frame'],
                    resolution=self.resolution
                )
                
                # Split into UDP chunks if needed
                if len(packet) > config.MAX_PACKET_SIZE:
                    self._send_large_frame(packet, frame_data['frame_id'])
                else:
                    self.socket.sendto(packet, self.server_address)
                    self.bytes_sent += len(packet)
                
                self.frame_count += 1
                
                # FPS tracking
                current_time = time.time()
                self.fps_counter.append(current_time)
                
                if config.SHOW_FRAME_SIZE:
                    logger.debug(f"📤 Sent frame {self.frame_count}: {len(packet)} bytes")
            
            except Exception as e:
                logger.error(f" Send error: {e}")
                time.sleep(0.1)
    
    def _send_large_frame(self, packet: bytes, frame_id: int):
        """
        Enviar frame grande en múltiples paquetes UDP
        """
        
        max_payload = config.MAX_PACKET_SIZE - 20  # Reserve para header
        
        # Crear header
        header = struct.pack(
            '!I',  # Frame ID (4 bytes)
            frame_id
        )
        
        total_chunks = (len(packet) + max_payload - 1) // max_payload
        
        for chunk_idx in range(total_chunks):
            start = chunk_idx * max_payload
            end = min(start + max_payload, len(packet))
            chunk = packet[start:end]
            
            # Chunk header: [frame_id: 4 bytes][chunk_idx: 2 bytes][total_chunks: 2 bytes][payload]
            chunk_header = struct.pack(
                '!IHH',
                frame_id,
                chunk_idx,
                total_chunks
            )
            
            full_packet = chunk_header + chunk
            self.socket.sendto(full_packet, self.server_address)
            self.bytes_sent += len(full_packet)
    
    def get_stats(self) -> dict:
        """Obtener estadísticas"""
        
        elapsed = time.time() - self.start_time
        avg_fps = len(self.fps_counter) / elapsed if elapsed > 0 else 0
        
        return {
            'camera_id': self.camera_id,
            'frames_sent': self.frame_count,
            'bytes_sent': self.bytes_sent,
            'elapsed_seconds': int(elapsed),
            'avg_fps': round(avg_fps, 2),
            'connected': self.is_connected,
            'queue_size': len(self.frame_queue)
        }
    
    def print_stats(self):
        """Imprimir estadísticas"""
        
        stats = self.get_stats()
        logger.info(f"""
╔════════════════════════════════════════════════════╗
║ 📡 CAMERA CLIENT STATS
╠════════════════════════════════════════════════════╣
║ Camera ID:        {stats['camera_id']}
║ Frames Sent:      {stats['frames_sent']}
║ Data Sent:        {stats['bytes_sent'] / (1024*1024):.2f} MB
║ Elapsed:          {stats['elapsed_seconds']} sec
║ Avg FPS:          {stats['avg_fps']}
║ Connected:        {stats['connected']}
║ Queue Size:       {stats['queue_size']}
╚════════════════════════════════════════════════════╝
        """)


def main():
    """
    Ejemplo de uso
    """
    
    # Crear cliente
    camera_client = CameraClient(
        camera_id="CAMERA_OFICINA_01",
        camera_source=0,  # Webcam local
        server_host=config.SERVER_HOST,
        server_port=config.SERVER_PORT,
        resolution=config.RESOLUTION,
        fps=config.FPS
    )
    
    # Iniciar streaming
    if not camera_client.start():
        logger.error("Failed to start camera client")
        return
    
    try:
        # Streaming indefinidamente
        while True:
            time.sleep(10)
            camera_client.print_stats()
    
    except KeyboardInterrupt:
        logger.info("🛑 Stopping...")
    
    finally:
        camera_client.stop()


if __name__ == "__main__":
    main()
