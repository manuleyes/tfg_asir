/**
 * Enhanced Dashboard - Chart.js + Dark Mode + Auto-Refresh
 */

// ============ CHARTS — gráfico de líneas en tiempo real ============
let realtimeChart = null;
let _rtInterval = null;

// Ventana deslizante: últimos 30 puntos (cada ~3s = ~90s de historial)
const RT_MAX_POINTS = 30;
const _rtLabels = [];
const _rtPersons = [];
const _rtVehicles = [];
let _rtLastPersons = 0;
let _rtLastVehicles = 0;

function _rtTimeLabel() {
    const d = new Date();
    return d.getHours().toString().padStart(2,'0') + ':' +
           d.getMinutes().toString().padStart(2,'0') + ':' +
           d.getSeconds().toString().padStart(2,'0');
}

function _buildRealtimeChart() {
    const ctx = document.getElementById('realtimeChart');
    if (!ctx) return;
    if (realtimeChart) realtimeChart.destroy();
    const dark = document.body.classList.contains('dark-mode');
    const gridClr = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.07)';
    const tickClr = dark ? '#9ca3af' : '#6b7280';
    realtimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: _rtLabels,
            datasets: [
                {
                    label: 'Personas',
                    data: _rtPersons,
                    borderColor: '#60a5fa',
                    backgroundColor: 'rgba(96,165,250,0.10)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Vehículos',
                    data: _rtVehicles,
                    borderColor: '#34d399',
                    backgroundColor: 'rgba(52,211,153,0.10)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            plugins: {
                legend: { labels: { color: tickClr, font: { size: 12 } } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMin: 0,
                    ticks: { color: tickClr, precision: 0 },
                    grid: { color: gridClr }
                },
                x: {
                    ticks: { color: tickClr, maxTicksLimit: 10, maxRotation: 0 },
                    grid: { color: gridClr }
                }
            }
        }
    });
}

async function _rtTick() {
    try {
        // Datos de detección acumulados por cámara (active-list)
        const res = await fetch('/api/v2/camera/active-list', { credentials: 'include' });
        if (!res.ok) return;
        const data = await res.json();
        const cameras = data.cameras || [];

        // Sumar totales de todas las cámaras
        let persons = 0, vehicles = 0;
        for (const c of cameras) {
            persons  += (c.persons_total  || 0);
            vehicles += (c.cars_total || 0);
        }

        // Calcular incremento desde el tick anterior (detecciones nuevas)
        const newPersons  = Math.max(0, persons  - _rtLastPersons);
        const newVehicles = Math.max(0, vehicles - _rtLastVehicles);
        _rtLastPersons  = persons;
        _rtLastVehicles = vehicles;

        // Añadir punto
        _rtLabels.push(_rtTimeLabel());
        _rtPersons.push(newPersons);
        _rtVehicles.push(newVehicles);

        // Mantener ventana de RT_MAX_POINTS
        if (_rtLabels.length > RT_MAX_POINTS) {
            _rtLabels.shift();
            _rtPersons.shift();
            _rtVehicles.shift();
        }

        if (!realtimeChart) _buildRealtimeChart();
        else realtimeChart.update('none');  // sin animación para smooth scroll

        // Actualizar estado
        const statusEl = document.getElementById('rt-chart-status');
        if (statusEl) {
            const totalActive = cameras.filter(c => c.active).length;
            statusEl.textContent = totalActive > 0
                ? `${totalActive} cámara(s) activa(s) — actualizado ${_rtTimeLabel()}`
                : `Sin cámaras activas — ${_rtTimeLabel()}`;
        }
    } catch(e) {
        // silencioso, reintentará en el próximo tick
    }
}

function initCharts() {
    if (!realtimeChart) _buildRealtimeChart();
    if (!_rtInterval) {
        _rtTick(); // primer punto inmediato
        _rtInterval = setInterval(_rtTick, 3000);
    }
}

// Stub: el gráfico de líneas reemplaza los charts individuales
function personnesChart() {}
function vehiclesChart() {}

// ============ AUTO-REFRESH ============
let refreshInterval = null;

// ── Server stats polling ───────────────────────────────────────────────────
let _srvInterval = null;
let _srvPrevNet = null;
let _srvPrevDisk = null;
let _srvPrevTs = null;

function _fmtSpd(kb) {
    if (kb < 0) kb = 0;
    return kb > 1024 ? (kb / 1024).toFixed(2) + ' MB/s' : kb.toFixed(1) + ' KB/s';
}

function _fmtUptime(sec) {
    const d = Math.floor(sec / 86400);
    const h = Math.floor((sec % 86400) / 3600);
    const m = Math.floor((sec % 3600) / 60);
    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}

function _barClr(pct) {
    return pct >= 90 ? '#f87171' : pct >= 70 ? '#fbbf24' : '#60a5fa';
}

async function _loadServerStats() {
    try {
        const res = await fetch('/api/v2/server/stats', { credentials: 'include' });
        if (!res.ok) return;
        const d = await res.json();
        const now = Date.now();

        // CPU
        const cpuEl = document.getElementById('srv-cpu-pct');
        const cpuBar = document.getElementById('srv-cpu-bar');
        const cpuCores = document.getElementById('srv-cpu-cores');
        if (cpuEl) cpuEl.textContent = d.cpu.percent.toFixed(1);
        if (cpuBar) { cpuBar.style.width = d.cpu.percent + '%'; cpuBar.style.background = _barClr(d.cpu.percent); }
        if (cpuCores) cpuCores.textContent = `${d.cpu.cores} núcleos`;

        // RAM sistema
        const ramEl = document.getElementById('srv-ram-pct');
        const ramBar = document.getElementById('srv-ram-bar');
        if (ramEl) ramEl.textContent = d.ram.percent.toFixed(1);
        if (ramBar) { ramBar.style.width = d.ram.percent + '%'; ramBar.style.background = _barClr(d.ram.percent); }

        // RAM sistema — detail
        const ramDetailEl = document.getElementById('srv-ram-detail');
        if (ramDetailEl) ramDetailEl.textContent = `${d.ram.used_mb} MB / ${d.ram.total_mb} MB`;

        // RAM proceso
        const procRam = document.getElementById('srv-proc-ram');
        if (procRam) procRam.textContent = d.process.ram_mb;

        // CPU proceso
        const procCpuEl = document.getElementById('srv-proc-cpu');
        if (procCpuEl) procCpuEl.textContent = d.process.cpu_percent != null ? d.process.cpu_percent.toFixed(1) : '—';

        // Disco
        const diskEl = document.getElementById('srv-disk-pct');
        const diskBar = document.getElementById('srv-disk-bar');
        const diskDetailEl = document.getElementById('srv-disk-detail');
        if (diskEl) diskEl.textContent = d.disk.percent.toFixed(1);
        if (diskBar) { diskBar.style.width = d.disk.percent + '%'; diskBar.style.background = _barClr(d.disk.percent); }
        if (diskDetailEl) diskDetailEl.textContent = `${d.disk.used_gb} GB usados · ${d.disk.free_gb} GB libres`;

        // Red — totales
        const sentEl = document.getElementById('srv-net-sent');
        const recvEl = document.getElementById('srv-net-recv');
        const sentSpdEl = document.getElementById('srv-net-sent-spd');
        const recvSpdEl = document.getElementById('srv-net-recv-spd');
        if (sentEl) sentEl.textContent = d.network.sent_mb.toFixed(1);
        if (recvEl) recvEl.textContent = d.network.recv_mb.toFixed(1);

        // Red — velocidad KB/s (calculada entre muestras)
        if (_srvPrevNet && _srvPrevTs) {
            const dt = (now - _srvPrevTs) / 1000;
            if (dt > 0) {
                const sentKbs = (d.network.sent_mb - _srvPrevNet.sent_mb) * 1024 / dt;
                const recvKbs = (d.network.recv_mb - _srvPrevNet.recv_mb) * 1024 / dt;
                if (sentSpdEl) sentSpdEl.textContent = '↑ ' + _fmtSpd(sentKbs);
                if (recvSpdEl) recvSpdEl.textContent = '↓ ' + _fmtSpd(recvKbs);
            }
        }
        _srvPrevNet = { sent_mb: d.network.sent_mb, recv_mb: d.network.recv_mb };

        // Disco E/S — velocidad KB/s
        if (d.disk.io_read_mb != null) {
            const diskReadSpdEl = document.getElementById('srv-disk-read-spd');
            const diskWriteSpdEl = document.getElementById('srv-disk-write-spd');
            if (_srvPrevDisk && _srvPrevTs) {
                const dt = (now - _srvPrevTs) / 1000;
                if (dt > 0) {
                    const rKbs = (d.disk.io_read_mb - _srvPrevDisk.read_mb) * 1024 / dt;
                    const wKbs = (d.disk.io_write_mb - _srvPrevDisk.write_mb) * 1024 / dt;
                    if (diskReadSpdEl) diskReadSpdEl.textContent = '↓ lectura: ' + _fmtSpd(rKbs);
                    if (diskWriteSpdEl) diskWriteSpdEl.textContent = '↑ escritura: ' + _fmtSpd(wKbs);
                }
            } else if (diskReadSpdEl) {
                diskReadSpdEl.textContent = `Total leído: ${d.disk.io_read_mb} MB`;
                if (diskWriteSpdEl) diskWriteSpdEl.textContent = `Total escrito: ${d.disk.io_write_mb} MB`;
            }
            _srvPrevDisk = { read_mb: d.disk.io_read_mb, write_mb: d.disk.io_write_mb };
        }

        _srvPrevTs = now;

        // Cola YOLO
        const queueEl = document.getElementById('srv-queue');
        if (queueEl) {
            const totalQ = Object.values(d.cameras.queue_pending).reduce((a, b) => a + b, 0);
            queueEl.textContent = totalQ;
        }
        const framesTotalEl = document.getElementById('srv-frames-total');
        if (framesTotalEl) framesTotalEl.textContent = `${d.cameras.frames_received} frames procesados`;

        // Threads
        const thEl = document.getElementById('srv-threads');
        if (thEl) thEl.textContent = d.cpu.threads;

        // Uptime sistema
        const uptimeEl = document.getElementById('srv-uptime');
        if (uptimeEl && d.uptime_sec != null) uptimeEl.textContent = 'Activo: ' + _fmtUptime(d.uptime_sec);

        // Fecha/Hora
        const now2 = new Date();
        const timeEl = document.getElementById('srv-time');
        const dateEl = document.getElementById('srv-date');
        if (timeEl) timeEl.textContent = now2.toLocaleTimeString('es-ES');
        if (dateEl) dateEl.textContent = now2.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' });

    } catch (e) { /* silent */ }
}

function startServerStatsPolling() {
    _loadServerStats();
    if (!_srvInterval) _srvInterval = setInterval(_loadServerStats, 1500);
}

function stopServerStatsPolling() {
    if (_srvInterval) { clearInterval(_srvInterval); _srvInterval = null; }
}

async function srvExportJSON() {
    try {
        const res = await fetch('/api/v2/server/stats', { credentials: 'include' });
        if (!res.ok) throw new Error('Error ' + res.status);
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'server-stats-' + new Date().toISOString().slice(0, 19).replace(/:/g, '-') + '.json';
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('No se pudo exportar: ' + e.message);
    }
}

function startAutoRefresh() {
    // Refrescar cada 5 segundos
    refreshInterval = setInterval(() => {
        initCharts();
        // loadStatistics() and loadLastDetections() removed - handled by loadDashboardData in auth.js
    }, 5000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

function manualRefresh() {
    initCharts();
    _loadServerStats();
    showNotification('Datos actualizados', 'success');
}

// ============ EXPORT CSV ============
function exportToCSV(type) {
    let data = [];
    let filename = '';

    if (type === 'detecciones' || type === 'personas' || type === 'vehiculos') {
        filename = 'detecciones.csv';
        const rows = document.querySelectorAll('#deteccionesList tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length > 1) {
                data.push([
                    cells[1].textContent.trim(),  // Tipo
                    cells[2].textContent.trim(),  // ID/Descripción
                    cells[3].textContent.trim(),  // Cámara
                    cells[4].textContent.trim(),  // Confianza
                    cells[5].textContent.trim(),  // Veces
                    cells[6].textContent.trim()   // Fecha
                ]);
            }
        });
    }

    if (data.length === 0) {
        showNotification('No hay datos para exportar', 'warning');
        return;
    }

    const header = ['Tipo', 'ID/Descripción', 'Cámara', 'Confianza', 'Veces visto', 'Fecha y Hora'];
    let csv = [header, ...data].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);

    showNotification('CSV descargado correctamente', 'success');
}

// ============ EXPORT EXCEL ============
function exportToExcel(type) {
    const tbodyId = 'deteccionesList';
    const filename = 'detecciones.xls';
    const headers = ['Tipo', 'ID/Descripción', 'Cámara', 'Confianza', 'Veces visto', 'Fecha y Hora'];

    const rows = document.querySelectorAll(`#${tbodyId} tr`);
    const dataRows = [];
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 1) {
            // Skip photo cell (index 0), take the rest as text
            const rowData = Array.from(cells).slice(1).map(c => c.textContent.trim());
            dataRows.push(rowData);
        }
    });

    if (!dataRows.length) { showNotification('No hay datos para exportar', 'warning'); return; }

    // Build minimal XLS (HTML table wrapped in Excel namespace)
    const headerRow = headers.map(h => `<th>${h}</th>`).join('');
    const bodyRows = dataRows.map(r => '<tr>' + r.map(c => `<td>${c}</td>`).join('') + '</tr>').join('');
    const xls = `<html xmlns:o="urn:schemas-microsoft-com:office:office"
        xmlns:x="urn:schemas-microsoft-com:office:excel"
        xmlns="http://www.w3.org/TR/REC-html40">
        <head><meta charset="UTF-8"></head>
        <body><table><thead><tr>${headerRow}</tr></thead><tbody>${bodyRows}</tbody></table></body>
        </html>`;

    const blob = new Blob([xls], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
    showNotification('Excel descargado correctamente', 'success');
}

// ============ EXPORT JSON ============
function exportToJSON(type) {
    const endpoint = '/api/v2/search/items?limit=1000';
    const filename = 'detecciones.json';

    fetch(endpoint, { credentials: 'include' })
        .then(r => r.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = filename; a.click();
            URL.revokeObjectURL(url);
            showNotification('JSON descargado correctamente', 'success');
        })
        .catch(() => showNotification('Error al exportar JSON', 'error'));
}

// ============ NOTIFICATIONS ============
// Note: showNotification is defined in utils.js (loaded before this file)
// Do not redefine here.

// ============ SIDEBAR COLLAPSE ============
function initSidebarCollapse() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    let hideTimeout;
    
    // Mostrar navbar cuando el mouse se acerca al borde izquierdo
    document.addEventListener('mousemove', (e) => {
        clearTimeout(hideTimeout);
        
        // Si el mouse está muy cerca de la izquierda
        if (e.clientX < 30) {
            sidebar.classList.add('expanded');
        } 
        // Si el mouse se aleja bastante (más allá del sidebar abierto)
        else if (e.clientX > 280) {
            // Pequeño delay para evitar parpadeos
            hideTimeout = setTimeout(() => {
                sidebar.classList.remove('expanded');
            }, 150);
        }
    });
    
    // Colapsar cuando el mouse sale de la ventana
    document.addEventListener('mouseleave', () => {
        sidebar.classList.remove('expanded');
    });
}

// ============ INITIALIZE ============
document.addEventListener('DOMContentLoaded', () => {
    // Sidebar collapse behavior
    initSidebarCollapse();
    
    // Gráficos iniciales
    initCharts();
    
    // Auto-refresh
    startAutoRefresh();
    
    // Botón refresh manual
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', manualRefresh);
    }
    
    // Limpiar cuando se cierre la sesión
    window.addEventListener('beforeunload', stopAutoRefresh);
});

// CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    body.dark-mode {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }
    
    body.dark-mode .card {
        background-color: #2d2d2d;
        border-color: #3a3a3a;
    }
    
    body.dark-mode .top-bar {
        background-color: #2d2d2d;
        border-color: #3a3a3a;
    }
    
    body.dark-mode .sidebar {
        background-color: #1f1f1f;
        border-color: #3a3a3a;
    }
    
    body.dark-mode .table {
        color: #e0e0e0;
    }
    
    body.dark-mode .table tbody tr:hover {
        background-color: #3a3a3a;
    }
    
    body.dark-mode .input,
    body.dark-mode .input-search,
    body.dark-mode .input-textarea {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border-color: #4a4a4a;
    }
    
    .btn-dark-mode,
    .btn-refresh {
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        padding: 8px;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .btn-dark-mode:hover,
    .btn-refresh:hover {
        background-color: rgba(0,0,0,0.1);
        transform: scale(1.1);
    }
    
    body.dark-mode .btn-dark-mode:hover,
    body.dark-mode .btn-refresh:hover {
        background-color: rgba(255,255,255,0.1);
    }
`;
document.head.appendChild(style);
