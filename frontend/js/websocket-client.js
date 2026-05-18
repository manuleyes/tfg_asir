/**
 * websocket-client.js - Cliente WebSocket para actualizaciones en tiempo real
 * Se conecta a /ws/dashboard y actualiza stats sin polling manual
 */

(function () {
    'use strict';

    let ws = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT = 8;
    const RECONNECT_DELAY_BASE = 2000; // ms

    const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const WS_URL = `${WS_PROTOCOL}//${window.location.host}/ws/dashboard`;

    // Indicador visual de conexión
    function _updateConnectionBadge(state) {
        let badge = document.getElementById('ws-status-badge');
        if (!badge) return;
        badge.className = 'ws-badge ws-badge--' + state;
        const labels = { connected: 'En vivo', connecting: 'Conectando...', disconnected: 'Desconectado' };
        badge.textContent = labels[state] || state;
    }

    function _applyStats(data) {
        // Estadísticas de cards
        const cameras = data.cameras;
        const persons = data.persons;
        const vehicles = data.vehicles;
        const alerts = data.alerts;

        _setTextSafe('stat-cameras', cameras?.total ?? '-');
        _setTextSafe('stat-persons', persons?.total ?? '-');
        _setTextSafe('stat-vehicles', vehicles?.total ?? '-');
        _setTextSafe('stat-alerts', alerts?.total ?? '-');

        // Alertas sin leer en badge del sidebar
        const unread = alerts?.unread ?? 0;
        const alertBadge = document.getElementById('alerts-unread-badge');
        if (alertBadge) {
            alertBadge.textContent = unread > 0 ? unread : '';
            alertBadge.style.display = unread > 0 ? 'inline-flex' : 'none';
        }

        // Actualizar título del documento si hay alertas críticas
        const critical = alerts?.critical ?? 0;
        if (critical > 0) {
            document.title = `(${critical} crítica${critical > 1 ? 's' : ''}) Dashboard - Vigilancia`;
        } else {
            if (document.title.startsWith('(')) {
                document.title = 'Dashboard - Vigilancia Inteligente';
            }
        }
    }

    function _setTextSafe(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function _handleDetectionNew(data) {
        // Actualizar contador en vivo (cards del dashboard)
        if (data.persons > 0 || data.cars > 0) {
            const el = document.getElementById('live-detection-counter');
            if (el) {
                el.textContent = `Personas: ${data.persons}  |  Coches: ${data.cars}`;
                el.style.display = 'inline-block';
            }
        }

        // Refrescar tabla Personas si está visible
        if (document.getElementById('page-personas')?.classList.contains('active')) {
            if (typeof loadPersons === 'function') loadPersons();
        }
        // Refrescar tabla Vehículos si está visible
        if (document.getElementById('page-vehiculos')?.classList.contains('active')) {
            if (typeof loadVehicles === 'function') loadVehicles();
        }

        // Añadir fila al historial de detecciones en vivo
        const tbody = document.getElementById('live-detections-tbody');
        if (!tbody) return;

        // Quitar mensaje "Esperando detecciones..."
        const emptyRow = document.getElementById('live-detections-empty');
        if (emptyRow) emptyRow.remove();

        const ts = data.timestamp ? new Date(data.timestamp).toLocaleTimeString('es-ES') : '—';
        (data.boxes || []).forEach(box => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${ts}</td>
                <td>${data.camera_id}</td>
                <td><span class="badge badge-${box.type === 'person' ? 'blue' : 'green'}">${box.type === 'person' ? 'Persona' : 'Coche'}</span></td>
                <td>${(box.confidence * 100).toFixed(1)}%</td>
                <td style="font-size:11px;color:var(--text-muted)">[${box.x1},${box.y1}] → [${box.x2},${box.y2}]</td>`;
            tbody.insertBefore(tr, tbody.firstChild);
            // Limitar a 100 filas
            while (tbody.rows.length > 100) tbody.deleteRow(tbody.rows.length - 1);
        });
    }

    function _handleAlertNew(data) {
        // Toast de nueva alerta
        const severity = data.severity || 'info';
        const title = data.title || 'Nueva alerta';
        const severityLabels = { critical: 'CRÍTICA', warning: 'Advertencia', info: 'Info' };

        if (typeof showToast === 'function') {
            const toastType = severity === 'critical' ? 'error' : severity === 'warning' ? 'warning' : 'info';
            showToast(`[${severityLabels[severity] || severity}] ${title}`, toastType, 6000);
        } else if (typeof showNotification === 'function') {
            showNotification(`Nueva alerta: ${title}`, severity === 'critical' ? 'error' : 'info');
        }

        // Sonido de alerta para críticas (si hay Audio disponible)
        if (severity === 'critical') {
            _playAlertSound();
        }
    }

    function _playAlertSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, ctx.currentTime);
            oscillator.frequency.setValueAtTime(660, ctx.currentTime + 0.15);
            gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.4);
        } catch (_) { /* Sin sonido si no está disponible */ }
    }

    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) return;

        _updateConnectionBadge('connecting');

        try {
            ws = new WebSocket(WS_URL);
        } catch (e) {
            console.warn('[WS] No se pudo crear WebSocket:', e);
            _scheduleReconnect();
            return;
        }

        ws.onopen = function () {
            console.log('[WS] Conectado a', WS_URL);
            reconnectAttempts = 0;
            _updateConnectionBadge('connected');
        };

        ws.onmessage = function (event) {
            try {
                const msg = JSON.parse(event.data);
                switch (msg.type) {
                    case 'stats_update':
                        _applyStats(msg.data);
                        break;
                    case 'alert_new':
                        _handleAlertNew(msg.data);
                        break;
                    case 'detection_new':
                        _handleDetectionNew(msg.data);
                        break;
                    case 'ping':
                        ws.send(JSON.stringify({ type: 'ping' }));
                        break;
                    default:
                        break;
                }
            } catch (e) {
                console.warn('[WS] Error parseando mensaje:', e);
            }
        };

        ws.onclose = function (event) {
            console.log('[WS] Desconectado. Código:', event.code);
            _updateConnectionBadge('disconnected');
            if (event.code !== 4001) {
                // 4001 = no autenticado, no reconectar
                _scheduleReconnect();
            }
        };

        ws.onerror = function (error) {
            console.warn('[WS] Error:', error);
            _updateConnectionBadge('disconnected');
        };
    }

    function _scheduleReconnect() {
        if (reconnectAttempts >= MAX_RECONNECT) {
            console.warn('[WS] Máximo de reconexiones alcanzado');
            return;
        }
        reconnectAttempts++;
        const delay = RECONNECT_DELAY_BASE * Math.pow(1.5, reconnectAttempts - 1);
        console.log(`[WS] Reconectando en ${Math.round(delay / 1000)}s (intento ${reconnectAttempts})`);
        setTimeout(connect, delay);
    }

    function disconnect() {
        if (ws) {
            ws.close(1000, 'User logout');
            ws = null;
        }
    }

    function requestStats() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'request_stats' }));
        }
    }

    // Exponer API global
    window.WSClient = { connect, disconnect, requestStats };

    // Auto-conectar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', connect);
    } else {
        connect();
    }

    // Desconectar al cerrar sesión
    document.addEventListener('user-logout', disconnect);

})();
