"""
Dashboard mejorado con alertas de detección en tiempo real
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger(__name__)

# Crear router
router_dashboard = APIRouter(prefix="/api/v2", tags=["Dashboard"])

# Importar camera_stats desde camera_web_client
from .camera_web_client import camera_stats

@router_dashboard.get("/dashboard-v2", response_class=HTMLResponse)
async def dashboard_v2():
    """Dashboard mejorado con sistema de alertas y detecciones"""
    
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Vigilancia Inteligente v2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 40px;
            margin-bottom: 5px;
            color: #00ff88;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 16px;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .video-panel {
            position: relative;
            border-radius: 15px;
            overflow: hidden;
            background: rgba(0,0,0,0.5);
            border: 2px solid #00ff88;
        }
        
        .video-container {
            position: relative;
            width: 100%;
            padding-bottom: 66%;
            background: black;
        }
        
        .video-container img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .video-loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 10;
        }
        
        .spinner {
            border: 4px solid rgba(0,255,136,0.3);
            border-top: 4px solid #00ff88;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .overlay-counters {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #00ff88;
            font-size: 18px;
            font-weight: bold;
            z-index: 5;
            text-align: center;
        }
        
        .counter {
            margin: 8px 0;
            padding: 5px 10px;
            background: rgba(0,255,136,0.2);
            border-radius: 5px;
        }
        
        .counter-value {
            color: #00ff88;
            font-size: 24px;
        }
        
        .side-panel {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border: 2px solid #00ff88;
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .card-title {
            color: #00ff88;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            border-bottom: 2px solid #00ff88;
            padding-bottom: 10px;
        }
        
        .alert-item {
            background: rgba(255,50,50,0.1);
            border-left: 4px solid #ff3232;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            font-size: 13px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-10px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .alert-time {
            color: #ffaa00;
            font-weight: bold;
        }
        
        .alert-type {
            color: #00ff88;
        }
        
        .bottom-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .chart-placeholder {
            background: rgba(0,0,0,0.3);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            color: #00ff88;
        }
        
        .status-bar {
            background: rgba(0,255,136,0.1);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 20px;
        }
        
        .status-item {
            text-align: center;
        }
        
        .status-label {
            display: block;
            font-size: 12px;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .status-value {
            display: block;
            font-size: 20px;
            font-weight: bold;
            color: #00ff88;
        }
        
        .control-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        button {
            flex: 1;
            padding: 10px;
            background: linear-gradient(135deg, #00ff88 0%, #00cc6f 100%);
            color: black;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        button:hover {
            transform: scale(1.05);
        }
        
        .alert-sound {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VIGILANCIA INTELIGENTE IA</h1>
            <p>Dashboard en tiempo real con detección de rostros y objetos</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <span class="status-label">Personas Detectadas</span>
                <span class="status-value" id="total-persons">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">Vehículos Detectados</span>
                <span class="status-value" id="total-cars">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">Frames Procesados</span>
                <span class="status-value" id="total-frames">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">Último evento</span>
                <span class="status-value" id="last-event">--:--</span>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="video-panel">
                <div class="video-container">
                    <div class="video-loading" id="loading">
                        <div class="spinner"></div>
                        <div>Esperando video...</div>
                    </div>
                    <img id="video-frame" style="display: none;">
                </div>
            </div>
            
            <div class="side-panel">
                <div class="card">
                    <div class="card-title">ALERTAS EN VIVO</div>
                    <div id="alerts-list" style="max-height: 400px; overflow-y: auto;">
                        <div style="color: #888; text-align: center;">Esperando eventos...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="bottom-section">
            <div class="card">
                <div class="card-title">Estadísticas Detalladas</div>
                <div id="stats-detailed" style="font-size: 14px; line-height: 1.8;">
                    Cargando...
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Controles</div>
                <div class="control-buttons">
                    <button onclick="toggleAudio()">Sonido ON</button>
                    <button onclick="refreshData()">Actualizar</button>
                </div>
                <div style="margin-top: 15px; font-size: 13px; color: #aaa;">
                    <div>Auto-actualización: <span id="refresh-interval">500ms</span></div>
                    <div>Cámaras activas: <span id="active-cams">0</span></div>
                </div>
            </div>
        </div>
    </div>
    
    <audio id="alert-sound" class="alert-sound">
        <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj==" type="audio/wav">
    </audio>
    
    <script>
        const SERVER_URL = window.location.origin;
        let audioEnabled = true;
        let lastAlertTime = {};
        const ALERT_COOLDOWN = 3000; // 3 segundos entre alertas del mismo tipo
        
        function playAlertSound() {
            if (audioEnabled) {
                const audio = document.getElementById('alert-sound');
                audio.currentTime = 0;
                audio.play().catch(() => {});
            }
        }
        
        function toggleAudio() {
            audioEnabled = !audioEnabled;
            event.target.textContent = audioEnabled ? 'Sonido ON' : 'Sonido OFF';
            event.target.style.background = audioEnabled ? 
                'linear-gradient(135deg, #00ff88 0%, #00cc6f 100%)' : 
                'linear-gradient(135deg, #888 0%, #666 100%)';
        }
        
        async function loadFrame() {
            try {
                const response = await fetch(SERVER_URL + '/api/v2/camera/latest-frame?camera_id=mobile-1');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const img = document.getElementById('video-frame');
                    img.src = url;
                    img.style.display = 'block';
                    document.getElementById('loading').style.display = 'none';
                }
            } catch (err) {
                console.error('Frame error:', err);
            }
        }
        
        async function updateStats() {
            try {
                // Obtener estadísticas
                const statsResp = await fetch(SERVER_URL + '/api/v2/camera/stats');
                const stats = await statsResp.json();
                
                document.getElementById('total-frames').textContent = stats.total_frames;
                document.getElementById('active-cams').textContent = stats.num_cameras;
                
                // Obtener alertas
                const alertsResp = await fetch(SERVER_URL + '/api/v2/camera/alerts?limit=10');
                const alertsData = await alertsResp.json();
                
                // Procesar detecciones por tipo
                let totalPersons = 0;
                let totalCars = 0;
                
                if (stats.detection_stats && Object.keys(stats.detection_stats).length > 0) {
                    for (const [camId, camStats] of Object.entries(stats.detection_stats)) {
                        totalPersons += camStats.persons_total || 0;
                        totalCars += camStats.cars_total || 0;
                    }
                }
                
                document.getElementById('total-persons').textContent = totalPersons;
                document.getElementById('total-cars').textContent = totalCars;
                
                // Mostrar alertas recientes
                const alertsList = document.getElementById('alerts-list');
                if (alertsData.recent_alerts && alertsData.recent_alerts.length > 0) {
                    let html = '';
                    alertsData.recent_alerts.slice(-15).reverse().forEach(alert => {
                        const time = new Date(alert.timestamp).toLocaleTimeString();
                        const events = alert.events.map(e => e[0]).join(', ').toUpperCase();
                        html += '<div class="alert-item">';
                        html += '<span class="alert-time">' + time + '</span> - ';
                        html += '<span class="alert-type">' + events + '</span>';
                        html += '</div>';
                        
                        // Reproducir sonido si es nueva alerta
                        const eventKey = alert.camera_id + events;
                        if (!lastAlertTime[eventKey] || Date.now() - lastAlertTime[eventKey] > ALERT_COOLDOWN) {
                            playAlertSound();
                            lastAlertTime[eventKey] = Date.now();
                            document.getElementById('last-event').textContent = time;
                        }
                    });
                    alertsList.innerHTML = html;
                } else {
                    alertsList.innerHTML = '<div style="color: #888; text-align: center;">Sin eventos</div>';
                }
                
                // Estadísticas detalladas
                const statsHtml = 'Total Frames: ' + stats.total_frames + '<br>' +
                                'Datos: ' + stats.total_bytes_mb.toFixed(2) + ' MB<br>' +
                                'Personas Totales: ' + totalPersons + '<br>' +
                                'Vehículos Totales: ' + totalCars;
                document.getElementById('stats-detailed').innerHTML = statsHtml;
                
            } catch (err) {
                console.error('Stats error:', err);
            }
        }
        
        async function refreshData() {
            await Promise.all([loadFrame(), updateStats()]);
        }
        
        // Cargar datos iniciales
        refreshData();
        
        // Actualizar cada 500ms
        setInterval(refreshData, 500);
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)
