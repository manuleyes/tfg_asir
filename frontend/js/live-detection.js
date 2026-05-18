// JavaScript para Live Detection

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const logDiv = document.querySelector('.log');

let stream = null;
let frameCount = 0;
let startTime = Date.now();
let lastLogEntries = [];

const API_BASE = window.location.origin;

// Agregar entrada de log
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logDiv.appendChild(entry);
    logDiv.scrollTop = logDiv.scrollHeight;
    lastLogEntries.push({message, type});
    if (lastLogEntries.length > 20) lastLogEntries.shift();
}

// Verificar estado del backend
async function checkBackendStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();
        document.getElementById('status').textContent = 'Sistema Activo ';
        document.getElementById('status').className = 'badge badge-success';
        addLog(' Conexión al backend exitosa', 'success');
        return true;
    } catch (e) {
        document.getElementById('status').textContent = 'Offline';
        document.getElementById('status').className = 'badge badge-danger';
        addLog('[ERROR] Backend no disponible', 'error');
        return false;
    }
}

// Iniciar video
async function startVideo() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({video: true});
        video.srcObject = stream;
        addLog('[LOG] Cámara iniciada', 'success');
        processFrameContinuous();
    } catch (e) {
        addLog(`[ERROR] Error cámara: ${e.message}`, 'error');
    }
}

// Detener video
function stopVideo() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        addLog('[LOG] Cámara detenida', 'warning');
    }
}

// Procesar frames continuamente
function processFrameContinuous() {
    if (!video.srcObject) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    frameCount++;
    
    // Actualizar FPS cada segundo
    const elapsed = (Date.now() - startTime) / 1000;
    if (elapsed > 0) {
        const fps = frameCount / elapsed;
        document.getElementById('fps').textContent = Math.round(fps);
    }
    
    document.getElementById('frameCount').textContent = frameCount;
    
    // Procesar cada 5 frames para no sobrecargar
    if (frameCount % 5 === 0) {
        captureAndDetect();
    }
    
    setTimeout(processFrameContinuous, 30);
}

// Capturar y procesar con IA
async function captureAndDetect() {
    if (canvas.width === 0) return;
    
    const startTime = Date.now();
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    
    try {
        // Procesar con Face Recognition
        const res = await fetch(`${API_BASE}/api/v2/reconocer-rostro`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({image_base64: imageData.split(',')[1]})
        });
        
        if (res.ok) {
            const result = await res.json();
            const latency = Date.now() - startTime;
            
            document.getElementById('latency').textContent = `${latency}ms`;
            document.getElementById('facesDetected').textContent = result.faces_detected || 0;
            document.getElementById('lastDetection').textContent = new Date().toLocaleTimeString();
            
            if (result.faces_detected > 0) {
                addLog(`[SUCCESS] ${result.faces_detected} caras detectadas (${latency}ms)`, 'success');
            }
        } else {
            addLog('[WARNING] Error en detección', 'warning');
        }
    } catch (e) {
        // Silenciar errores de conexión para no saturar logs
        if (frameCount % 50 === 0) {
            addLog(`[WARNING] Reintentar conexión...`, 'warning');
        }
    }
}

// Inicializar
window.addEventListener('load', async () => {
    await checkBackendStatus();
    addLog('[LOG] Sistema listo. Haz clic en "Iniciar Cámara"', 'info');
});
