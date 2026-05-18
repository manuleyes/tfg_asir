"""
routes/websocket_routes.py - WebSocket para actualizaciones en tiempo real
Permite que el dashboard reciba eventos sin polling constante
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from models.database import get_db, SessionLocal
from models.alert import Alert
from models.camera import Camera
from models.person import Person
from models.vehicle import Vehicle
from auth.session_handler import validate_session_cookie, SESSION_COOKIE_NAME
from itsdangerous import BadSignature, SignatureExpired
import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Gestor de conexiones WebSocket activas"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket conectado. Total conexiones: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket desconectado. Total conexiones: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Enviar mensaje a todas las conexiones activas"""
        if not self.active_connections:
            return
        payload = json.dumps(message, default=str)
        dead: Set[WebSocket] = set()
        async with self._lock:
            connections_snapshot = set(self.active_connections)
        for connection in connections_snapshot:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.add(connection)
        # Limpiar conexiones muertas
        if dead:
            async with self._lock:
                self.active_connections -= dead

    async def send_to(self, websocket: WebSocket, message: Dict[str, Any]):
        """Enviar mensaje a una conexión específica"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error enviando mensaje WS: {e}")


# Instancia global del manager
manager = ConnectionManager()


def _validate_ws_session(websocket: WebSocket) -> bool:
    """Validar sesión de cookie en WebSocket"""
    try:
        cookie_header = websocket.cookies.get(SESSION_COOKIE_NAME)
        if not cookie_header:
            return False
        validate_session_cookie(cookie_header)
        return True
    except (BadSignature, SignatureExpired, Exception):
        return False


async def _get_stats_snapshot() -> Dict[str, Any]:
    """Obtener snapshot de estadísticas actuales (abre y cierra su propia sesión BD)"""
    db = SessionLocal()
    try:
        cameras_total = db.query(Camera).count()
        cameras_active = db.query(Camera).filter(Camera.is_active == True).count()
        persons_total = db.query(Person).count()
        vehicles_total = db.query(Vehicle).count()
        alerts_total = db.query(Alert).count()
        alerts_unread = db.query(Alert).filter(Alert.is_read == False).count()
        alerts_critical = db.query(Alert).filter(
            Alert.severity == "critical", Alert.is_read == False
        ).count()

        # Última alerta
        last_alert = (
            db.query(Alert).order_by(Alert.created_at.desc()).first()
        )

        return {
            "type": "stats_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "cameras": {"total": cameras_total, "active": cameras_active},
                "persons": {"total": persons_total},
                "vehicles": {"total": vehicles_total},
                "alerts": {
                    "total": alerts_total,
                    "unread": alerts_unread,
                    "critical": alerts_critical,
                },
                "last_alert": {
                    "id": last_alert.id if last_alert else None,
                    "type": last_alert.alert_type if last_alert else None,
                    "title": last_alert.title if last_alert else None,
                    "severity": last_alert.severity if last_alert else None,
                    "created_at": last_alert.created_at.isoformat() if last_alert else None,
                } if last_alert else None,
            },
        }
    except Exception as e:
        logger.error(f"Error obteniendo stats snapshot: {e}")
        return {"type": "error", "message": str(e)}
    finally:
        db.close()


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint para el dashboard.
    Envía actualizaciones de estadísticas cada 5 segundos y eventos en tiempo real.

    Mensajes enviados:
    - stats_update: Estadísticas del sistema
    - alert_new: Nueva alerta creada
    - ping: Keep-alive

    Mensajes aceptados del cliente:
    - ping: Solicitar stats inmediatas
    - subscribe: Suscribirse a canales específicos
    """
    # Validar sesión
    if not _validate_ws_session(websocket):
        await websocket.close(code=4001, reason="No autenticado")
        return

    await manager.connect(websocket)

    # Enviar snapshot inicial
    try:
        initial = await _get_stats_snapshot()
        await manager.send_to(websocket, initial)
    except Exception as e:
        logger.error(f"Error en snapshot inicial WS: {e}")

    ping_counter = 0

    try:
        while True:
            # Esperar mensaje del cliente (con timeout de 5s para enviar stats)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                msg = json.loads(data)

                if msg.get("type") == "ping":
                    await manager.send_to(websocket, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})

                elif msg.get("type") == "request_stats":
                    stats = await _get_stats_snapshot()
                    await manager.send_to(websocket, stats)

            except asyncio.TimeoutError:
                # Timeout: enviar actualización periódica
                ping_counter += 1
                stats = await _get_stats_snapshot()
                await manager.send_to(websocket, stats)

                # Keep-alive cada 30s
                if ping_counter % 6 == 0:
                    await manager.send_to(websocket, {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat(),
                        "connections": len(manager.active_connections),
                    })

            except json.JSONDecodeError:
                pass  # Ignorar mensajes mal formados

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
    finally:
        await manager.disconnect(websocket)


async def broadcast_new_alert(alert_data: Dict[str, Any]):
    """
    Función para broadcast de nueva alerta desde otros módulos.
    Llamar cuando se crea una alerta crítica.
    """
    await manager.broadcast({
        "type": "alert_new",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data,
    })


async def broadcast_detection(detection_data: Dict[str, Any]):
    """Broadcast de nueva detección"""
    await manager.broadcast({
        "type": "detection_new",
        "timestamp": datetime.utcnow().isoformat(),
        "data": detection_data,
    })
