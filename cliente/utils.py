"""
Utilidades para cliente de cámara
- Compresión de frames
- Serialización de paquetes
- Manejo de metadata
"""

import cv2
import struct
import numpy as np
import json
import time
from typing import Dict, Tuple, Optional


def compress_frame(frame: np.ndarray, quality: int = 70) -> bytes:
    """
    Comprimir frame con JPEG
    
    Args:
        frame: Frame en formato BGR (OpenCV)
        quality: Calidad JPEG (0-100)
    
    Returns:
        Bytes comprimidos
    """
    
    success, compressed = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    
    if not success:
        raise ValueError("Failed to compress frame")
    
    return compressed.tobytes()


def decompress_frame(data: bytes) -> Optional[np.ndarray]:
    """
    Descomprimir frame JPEG
    
    Args:
        data: Bytes comprimidos
    
    Returns:
        Frame en BGR o None
    """
    
    try:
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    
    except Exception as e:
        print(f"Error decompressing frame: {e}")
        return None


def serialize_packet(
    camera_id: str,
    frame_id: int,
    timestamp: float,
    frame_data: bytes,
    resolution: Tuple[int, int]
) -> bytes:
    """
    Serializar frame en packet UDP
    
    Estructura:
    ┌─────────────────────────────────────────┐
    │ HEADER (variable length)                │
    ├─────────────────────────────────────────┤
    │ Metadata JSON (camera_id, frame_id, ts) │
    │ {                                       │
    │   "camera_id": "CAM_01",                │
    │   "frame_id": 1234,                     │
    │   "timestamp": 1234567890.123,          │
    │   "resolution": [640, 480],             │
    │   "frame_size": 15234                   │
    │ }                                       │
    ├─────────────────────────────────────────┤
    │ Payload (frame data)                    │
    └─────────────────────────────────────────┘
    
    Args:
        camera_id: ID de cámara
        frame_id: ID de frame
        timestamp: Timestamp
        frame_data: Bytes del frame comprimido
        resolution: (width, height)
    
    Returns:
        Bytes de packet
    """
    
    # Create metadata
    metadata = {
        'camera_id': camera_id,
        'frame_id': frame_id,
        'timestamp': timestamp,
        'resolution': list(resolution),
        'frame_size': len(frame_data)
    }
    
    # Serialize metadata as JSON
    metadata_json = json.dumps(metadata).encode('utf-8')
    
    # Create packet: [metadata_length: 4 bytes][metadata][frame_data]
    metadata_len = len(metadata_json)
    header = struct.pack('!I', metadata_len)
    
    packet = header + metadata_json + frame_data
    
    return packet


def deserialize_packet(packet: bytes) -> Optional[Dict]:
    """
    Deserializar packet UDP
    
    Returns:
        {
            'metadata': {...},
            'frame_data': bytes,
            'frame': np.ndarray o None
        }
    """
    
    try:
        # Extract metadata length
        metadata_len = struct.unpack('!I', packet[:4])[0]
        
        # Extract metadata
        metadata_bytes = packet[4:4+metadata_len]
        metadata = json.loads(metadata_bytes.decode('utf-8'))
        
        # Extract frame data
        frame_data = packet[4+metadata_len:]
        
        # Try to decompress frame
        frame = decompress_frame(frame_data)
        
        return {
            'metadata': metadata,
            'frame_data': frame_data,
            'frame': frame
        }
    
    except Exception as e:
        print(f"Error deserializing packet: {e}")
        return None


def deserialize_chunked_packet(
    packet: bytes,
    reassembly_buffer: Dict = None
) -> Optional[Dict]:
    """
    Deserializar packet UDP que es parte de un frame grande
    
    Estructura de chunk:
    [frame_id: 4 bytes][chunk_idx: 2 bytes][total_chunks: 2 bytes][payload]
    
    Args:
        packet: Bytes de packet
        reassembly_buffer: Dict para mantener chunks parciales
    
    Returns:
        {
            'is_complete': bool,
            'frame_id': int,
            'data': bytes o None (si está completo)
        }
    """
    
    if reassembly_buffer is None:
        reassembly_buffer = {}
    
    try:
        # Extract chunk header
        frame_id, chunk_idx, total_chunks = struct.unpack('!IHH', packet[:8])
        payload = packet[8:]
        
        # Initialize frame buffer if needed
        if frame_id not in reassembly_buffer:
            reassembly_buffer[frame_id] = {
                'chunks': {},
                'total_chunks': total_chunks,
                'created_at': time.time()
            }
        
        # Store chunk
        reassembly_buffer[frame_id]['chunks'][chunk_idx] = payload
        
        # Check if complete
        if len(reassembly_buffer[frame_id]['chunks']) == total_chunks:
            # Reassemble
            chunks = reassembly_buffer[frame_id]['chunks']
            complete_data = b''.join(chunks[i] for i in range(total_chunks))
            
            # Remove from buffer
            del reassembly_buffer[frame_id]
            
            return {
                'is_complete': True,
                'frame_id': frame_id,
                'data': complete_data
            }
        
        # Cleanup old frames (older than 5 seconds)
        current_time = time.time()
        for fid in list(reassembly_buffer.keys()):
            if current_time - reassembly_buffer[fid]['created_at'] > 5:
                del reassembly_buffer[fid]
        
        return {
            'is_complete': False,
            'frame_id': frame_id,
            'data': None
        }
    
    except Exception as e:
        print(f"Error deserializing chunked packet: {e}")
        return None


def get_frame_info(packet: bytes) -> Optional[Dict]:
    """
    Extraer información de frame sin deserializar completo
    """
    
    try:
        metadata_len = struct.unpack('!I', packet[:4])[0]
        metadata = json.loads(packet[4:4+metadata_len].decode('utf-8'))
        
        return {
            'camera_id': metadata.get('camera_id'),
            'frame_id': metadata.get('frame_id'),
            'timestamp': metadata.get('timestamp'),
            'resolution': tuple(metadata.get('resolution', [0, 0])),
            'frame_size': metadata.get('frame_size')
        }
    
    except Exception as e:
        print(f"Error getting frame info: {e}")
        return None
