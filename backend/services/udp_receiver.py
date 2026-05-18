"""
Servidor UDP para recibir video streams de cámaras
Corre en: Servidor central
Recibe: Video de múltiples cámaras por UDP
Envía: Frames a la pipeline de detección (FASE 1-3)
"""

import logging
import socket
import threading
import time
import struct
import json
from typing import Dict, Optional, Callable
from collections import defaultdict
from dataclasses import dataclass
import numpy as np
import cv2

logger = logging.getLogger(__name__)


@dataclass
class StreamMetadata:
    """Metadata de stream de cámara"""
    camera_id: str
    total_frames_received: int = 0
    bytes_received: int = 0
    last_frame_time: float = 0
    connection_time: float = 0
    is_active: bool = True


class UDPStreamReceiver:
    """
    Receptor UDP para múltiples streams de cámara
    
    Características:
    - Recibe frames comprimidos por UDP
    - Maneja múltiples cámaras en paralelo
    - Reconoce frames fragmentados
    - Integración fácil con pipeline de detección
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",  # nosec B104
        port: int = 5005,
        buffer_size: int = 65536,
        frame_callback: Optional[Callable] = None
    ):
        """
        Inicializar receptor UDP
        
        Args:
            host: IP a escuchar
            port: Puerto UDP
            buffer_size: Tamaño de buffer
            frame_callback: Función para procesar cada frame recibido
        """
        
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.frame_callback = frame_callback
        
        # Socket
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.receiver_thread: Optional[threading.Thread] = None
        
        # Streams activos
        self.streams: Dict[str, StreamMetadata] = {}
        
        # Buffers para frames fragmentados
        self.reassembly_buffers: Dict[str, Dict] = defaultdict(dict)
        
        # Stats globales
        self.total_frames_received = 0
        self.total_bytes_received = 0
        self.start_time = time.time()
        
        logger.info(f" UDPStreamReceiver initialized: {host}:{port}")
    
    def start(self) -> bool:
        """Iniciar servidor UDP"""
        
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            self.socket.bind((self.host, self.port))
            
            logger.info(f" UDP socket listening on {self.host}:{self.port}")
        
        except Exception as e:
            logger.error(f" Failed to create socket: {e}")
            return False
        
        # Start receiver thread
        self.running = True
        self.receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self.receiver_thread.start()
        
        logger.info(" UDP receiver started")
        return True
    
    def stop(self):
        """Detener servidor"""
        
        self.running = False
        
        if self.receiver_thread:
            self.receiver_thread.join(timeout=2)
        
        if self.socket:
            self.socket.close()
        
        logger.info(" UDP receiver stopped")
    
    def _receiver_loop(self):
        """Loop principal de recepción"""
        
        while self.running:
            try:
                # Receive packet
                packet, client_address = self.socket.recvfrom(self.buffer_size)
                
                if len(packet) < 4:
                    continue
                
                # Try to parse as regular packet or chunked packet
                self._process_packet(packet, client_address)
            
            except socket.timeout:
                continue
            
            except Exception as e:
                logger.warning(f"️ Receiver error: {e}")
    
    def _process_packet(self, packet: bytes, client_address: tuple):
        """
        Procesar packet recibido
        Detecta si es frame completo o fragmento
        """
        
        try:
            # Try to parse as regular packet first
            result = self._parse_regular_packet(packet)
            
            if result:
                camera_id = result['metadata']['camera_id']
                frame = result['frame']
                
                # Update metadata
                if camera_id not in self.streams:
                    self.streams[camera_id] = StreamMetadata(
                        camera_id=camera_id,
                        connection_time=time.time()
                    )
                
                stream = self.streams[camera_id]
                stream.total_frames_received += 1
                stream.bytes_received += len(packet)
                stream.last_frame_time = time.time()
                
                self.total_frames_received += 1
                self.total_bytes_received += len(packet)
                
                logger.debug(f"📥 Frame from {camera_id}: {len(packet)} bytes")
                
                # Call callback
                if self.frame_callback and frame is not None:
                    self.frame_callback(
                        camera_id=camera_id,
                        frame=frame,
                        metadata=result['metadata']
                    )
            
            else:
                # Try as chunked packet
                result = self._parse_chunked_packet(packet, client_address)
                
                if result and result['is_complete']:
                    # Complete frame reassembled
                    camera_id = result['camera_id']
                    frame = result['frame']
                    
                    if camera_id not in self.streams:
                        self.streams[camera_id] = StreamMetadata(
                            camera_id=camera_id,
                            connection_time=time.time()
                        )
                    
                    stream = self.streams[camera_id]
                    stream.total_frames_received += 1
                    stream.bytes_received += len(result['data'])
                    stream.last_frame_time = time.time()
                    
                    logger.debug(f"📥 Chunked frame complete from {camera_id}")
                    
                    if self.frame_callback and frame is not None:
                        self.frame_callback(
                            camera_id=camera_id,
                            frame=frame,
                            metadata=result['metadata']
                        )
        
        except Exception as e:
            logger.debug(f"Error processing packet: {e}")
    
    def _parse_regular_packet(self, packet: bytes) -> Optional[Dict]:
        """
        Parsear packet regular (frame completo)
        
        Estructura:
        [metadata_len: 4 bytes][metadata JSON][frame data]
        """
        
        try:
            if len(packet) < 4:
                return None
            
            # Extract metadata length
            metadata_len = struct.unpack('!I', packet[:4])[0]
            
            if len(packet) < 4 + metadata_len:
                return None
            
            # Extract metadata
            metadata_bytes = packet[4:4+metadata_len]
            metadata = json.loads(metadata_bytes.decode('utf-8'))
            
            # Extract frame data
            frame_data = packet[4+metadata_len:]
            
            # Decompress frame
            try:
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except:
                frame = None
            
            return {
                'metadata': metadata,
                'frame_data': frame_data,
                'frame': frame
            }
        
        except Exception as e:
            logger.debug(f"Not a regular packet: {e}")
            return None
    
    def _parse_chunked_packet(self, packet: bytes, client_address: tuple) -> Optional[Dict]:
        """
        Parsear packet fragmentado (chunk de frame grande)
        
        Estructura:
        [frame_id: 4 bytes][chunk_idx: 2 bytes][total_chunks: 2 bytes][payload]
        """
        
        try:
            if len(packet) < 8:
                return None
            
            # Extract chunk header
            frame_id, chunk_idx, total_chunks = struct.unpack('!IHH', packet[:8])
            payload = packet[8:]
            
            # Get camera_id from map (client address -> camera)
            camera_id = f"unknown_{client_address[0]}"
            
            # Initialize frame buffer if needed
            reassembly_key = f"{camera_id}_{frame_id}"
            
            if reassembly_key not in self.reassembly_buffers[camera_id]:
                self.reassembly_buffers[camera_id][reassembly_key] = {
                    'chunks': {},
                    'total_chunks': total_chunks,
                    'created_at': time.time()
                }
            
            # Store chunk
            self.reassembly_buffers[camera_id][reassembly_key]['chunks'][chunk_idx] = payload
            
            # Check if complete
            buffer = self.reassembly_buffers[camera_id][reassembly_key]
            
            if len(buffer['chunks']) == total_chunks:
                # Reassemble
                chunks = buffer['chunks']
                complete_data = b''.join(chunks[i] for i in range(total_chunks))
                
                # Decompress
                try:
                    nparr = np.frombuffer(complete_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                except:
                    frame = None
                
                # Cleanup
                del self.reassembly_buffers[camera_id][reassembly_key]
                
                return {
                    'is_complete': True,
                    'camera_id': camera_id,
                    'frame_id': frame_id,
                    'data': complete_data,
                    'frame': frame,
                    'metadata': {'camera_id': camera_id, 'frame_id': frame_id}
                }
            
            # Cleanup old frames (>5 seconds)
            current_time = time.time()
            for key in list(self.reassembly_buffers[camera_id].keys()):
                if current_time - self.reassembly_buffers[camera_id][key]['created_at'] > 5:
                    del self.reassembly_buffers[camera_id][key]
            
            return {
                'is_complete': False,
                'frame_id': frame_id
            }
        
        except Exception as e:
            logger.debug(f"Not a chunked packet: {e}")
            return None
    
    def register_frame_callback(self, callback: Callable):
        """Registrar callback para procesar frames"""
        self.frame_callback = callback
    
    def get_active_streams(self) -> Dict:
        """Obtener streams activos"""
        return {
            camera_id: {
                'frames': stream.total_frames_received,
                'bytes': stream.bytes_received,
                'last_frame_age': time.time() - stream.last_frame_time,
                'connection_age': time.time() - stream.connection_time
            }
            for camera_id, stream in self.streams.items()
        }
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas globales"""
        
        elapsed = time.time() - self.start_time
        
        return {
            'total_frames': self.total_frames_received,
            'total_bytes': self.total_bytes_received,
            'active_streams': len(self.streams),
            'elapsed_seconds': int(elapsed),
            'bytes_per_second': self.total_bytes_received / elapsed if elapsed > 0 else 0,
            'streams': self.get_active_streams()
        }
    
    def print_stats(self):
        """Imprimir estadísticas"""
        
        stats = self.get_stats()
        
        logger.info(f"""
╔════════════════════════════════════════════════════╗
║ 📥 UDP STREAM RECEIVER STATS
╠════════════════════════════════════════════════════╣
║ Active Streams:   {stats['active_streams']}
║ Total Frames:     {stats['total_frames']}
║ Total Data:       {stats['total_bytes'] / (1024*1024):.2f} MB
║ Elapsed:          {stats['elapsed_seconds']} sec
║ Bandwidth:        {stats['bytes_per_second'] / (1024*1024):.2f} MB/s
╠════════════════════════════════════════════════════╣
║ Streams:
|-|
        """)
        
        for camera_id, info in stats['streams'].items():
            logger.info(f"║   {camera_id}: {info['frames']} frames, {info['bytes']/1024:.1f}KB, age: {info['last_frame_age']:.1f}s")
        
        logger.info("╚════════════════════════════════════════════════════╝")


def create_receiver_with_pipeline(
    pipeline,  # SurveillancePipeline instance
    host: str = "0.0.0.0",  # nosec B104
    port: int = 5005
) -> UDPStreamReceiver:
    """
    Crear receptor UDP integrado con pipeline de detección
    
    Args:
        pipeline: Instancia de SurveillancePipeline
        host: IP a escuchar
        port: Puerto UDP
    
    Returns:
        UDPStreamReceiver configurado
    """
    
    def frame_callback(camera_id: str, frame: np.ndarray, metadata: Dict):
        """Callback que procesa cada frame con la pipeline"""
        
        try:
            # Process with full pipeline
            analysis, _ = pipeline.process_frame(frame)
            
            if analysis:
                logger.debug(f" Processed {len(analysis.detections)} detections from {camera_id}")
                
                # Store results in database, cache, or send to frontend
                # Ejemplo: enviar a base de datos o WebSocket
        
        except Exception as e:
            logger.error(f" Pipeline error: {e}")
    
    receiver = UDPStreamReceiver(
        host=host,
        port=port,
        frame_callback=frame_callback
    )
    
    return receiver
