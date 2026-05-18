"""
Cliente de Cámara para Vigilancia Distribuida
Streaming de video por UDP al servidor central
"""

from .camera_streaming_client import CameraClient
from .utils import (
    compress_frame,
    decompress_frame,
    serialize_packet,
    deserialize_packet,
    deserialize_chunked_packet,
    get_frame_info
)

__version__ = "1.0.0"
__all__ = [
    'CameraClient',
    'compress_frame',
    'decompress_frame',
    'serialize_packet',
    'deserialize_packet',
    'deserialize_chunked_packet',
    'get_frame_info'
]
