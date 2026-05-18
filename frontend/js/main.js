/**
 * main.js - Lógica principal y funciones de páginas
 */

// ── Lightbox para fotos de detección ─────────────────────────────────────────
function _openLightbox(src, caption) {
    let lb = document.getElementById('_det-lightbox');
    if (!lb) {
        lb = document.createElement('div');
        lb.id = '_det-lightbox';
        lb.style.cssText = [
            'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.85)',
            'display:flex;flex-direction:column;align-items:center;justify-content:center',
            'cursor:zoom-out;padding:24px;box-sizing:border-box'
        ].join(';');
        lb.innerHTML = `
            <img id="_det-lb-img" style="max-width:90vw;max-height:80vh;border-radius:8px;box-shadow:0 8px 40px rgba(0,0,0,.6);object-fit:contain;">
            <p id="_det-lb-cap" style="color:#e5e7eb;margin-top:12px;font-size:14px;text-align:center;max-width:80vw;word-break:break-all;"></p>
            <button onclick="document.getElementById('_det-lightbox').style.display='none'"
                style="margin-top:12px;background:rgba(255,255,255,.15);border:none;color:#fff;padding:8px 22px;border-radius:20px;cursor:pointer;font-size:14px;">✕ Cerrar</button>`;
        lb.addEventListener('click', e => { if (e.target === lb) lb.style.display = 'none'; });
        document.body.appendChild(lb);
        document.addEventListener('keydown', e => { if (e.key === 'Escape') lb.style.display = 'none'; });
    }
    document.getElementById('_det-lb-img').src = src;
    document.getElementById('_det-lb-cap').textContent = caption || '';
    lb.style.display = 'flex';
}

/**
 * Mostrar formulario de agregar cámara
 */
function showAddCameraForm() {
    const name = prompt('Nombre de la cámara:');
    if (!name) return;

    const url = prompt('URL/ruta de la cámara:');
    if (!url) return;

    const location = prompt('Ubicación:');

    addCamera({ name, url, location });
}

/**
 * Agregar cámara
 */
async function addCamera(data) {
    try {
        const response = await apiCreateCamera(data);
        if (response) {
            showNotification('Cámara agregada correctamente', 'success');
            loadCameras();
        }
    } catch (error) {
        showNotification(error.message || 'Error al agregar cámara', 'error');
    }
}

/**
 * Editar cámara
 */
function editCamera(id) {
    showNotification('Función de edición en desarrollo', 'info');
}

/**
 * Eliminar cámara
 */
async function deleteCamera(id) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta cámara?')) return;

    try {
        await apiDeleteCamera(id);
        showNotification('Cámara eliminada correctamente', 'success');
        loadCameras();
    } catch (error) {
        showNotification(error.message || 'Error al eliminar cámara', 'error');
    }
}

/**
 * Ejecutar query SQL
 */
async function executeQuery() {
    const queryText = document.getElementById('sqlQuery').value.trim();

    if (!queryText) {
        showNotification('Por favor, ingresa una query', 'warning');
        return;
    }

    try {
        const result = await apiExecuteQuery(queryText);
        displayQueryResult(result);
    } catch (error) {
        showNotification(error.message || 'Error al ejecutar query', 'error');
    }
}

/**
 * Mostrar resultado de query
 */
function displayQueryResult(result) {
    const resultDiv = document.getElementById('queryResult');
    const contentDiv = document.getElementById('queryResultContent');

    if (result) {
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(result, null, 2);
        contentDiv.innerHTML = '';
        contentDiv.appendChild(pre);
        resultDiv.style.display = 'block';
    }
}

/**
 * Generar reporte
 */
// ── Reportes helpers ─────────────────────────────────────────────────────────
function _repDateRange() {
    const desde = document.getElementById('repDesde')?.value;
    const hasta = document.getElementById('repHasta')?.value;
    const params = new URLSearchParams({ limit: 500 });
    if (desde) params.set('desde', desde);
    if (hasta) params.set('hasta', hasta);
    return params;
}

function _repSetPreset(hours) {
    const now = new Date();
    const from = new Date(now.getTime() - hours * 3600 * 1000);
    const fmt = d => {
        const pad = n => String(n).padStart(2,'0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };
    document.getElementById('repDesde').value = fmt(from);
    document.getElementById('repHasta').value = fmt(now);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.rep-preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.rep-preset-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const p = btn.dataset.p;
            const map = { '1h': 1, '6h': 6, '24h': 24, '7d': 168, '30d': 720 };
            if (map[p]) _repSetPreset(map[p]);
        });
    });
    // Default: last 24h
    const defBtn = document.querySelector('.rep-preset-btn[data-p="24h"]');
    if (defBtn) defBtn.click();
});

async function repPreview() {
    const type = document.getElementById('reportType').value;
    const params = _repDateRange();
    const card = document.getElementById('rep-preview-card');
    const title = document.getElementById('rep-preview-title');
    const count = document.getElementById('rep-preview-count');
    const thead = document.getElementById('rep-preview-thead');
    const tbody = document.getElementById('rep-preview-tbody');

    try {
        let rows = [], cols = [];
        if (type === 'persons') {
            const r = await fetch('/api/v2/search/persons?' + params, { credentials: 'include' });
            const d = await r.json();
            rows = d.persons || d.results || d || [];
            cols = ['ID', 'Nombre', 'Confianza', 'Cámara', 'Visto'];
        } else if (type === 'vehicles') {
            const r = await fetch('/api/v2/search/vehicles?' + params, { credentials: 'include' });
            const d = await r.json();
            rows = d.vehicles || d.results || d || [];
            cols = ['ID', 'Placa', 'Tipo', 'Confianza', 'Cámara', 'Visto'];
        } else if (type === 'alerts') {
            const r = await fetch('/api/alerts?' + params, { credentials: 'include' });
            const d = await r.json();
            rows = d.alerts || d.results || d || [];
            cols = ['ID', 'Tipo', 'Mensaje', 'Cámara', 'Fecha'];
        } else {
            // summary: persons + vehicles count
            const [rp, rv] = await Promise.all([
                fetch('/api/v2/search/persons?' + params, { credentials: 'include' }).then(r=>r.json()),
                fetch('/api/v2/search/vehicles?' + params, { credentials: 'include' }).then(r=>r.json())
            ]);
            rows = [{ tipo: 'Personas', total: (rp.persons||rp.results||rp||[]).length },
                    { tipo: 'Vehículos', total: (rv.vehicles||rv.results||rv||[]).length }];
            cols = ['Tipo', 'Total'];
        }

        title.textContent = { persons:'Personas', vehicles:'Vehículos', alerts:'Alertas', summary:'Resumen' }[type];
        count.textContent = rows.length + ' registros';
        thead.innerHTML = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
        tbody.innerHTML = rows.slice(0, 50).map(row => {
            if (type === 'persons') return `<tr><td>${row.id||''}</td><td>${row.name||row.label||'-'}</td><td>${row.confidence!=null?(row.confidence*100).toFixed(1)+'%':'-'}</td><td>${row.camera_id||'-'}</td><td>${row.last_seen||row.created_at||'-'}</td></tr>`;
            if (type === 'vehicles') return `<tr><td>${row.id||''}</td><td>${row.plate||'-'}</td><td>${row.vehicle_type||'-'}</td><td>${row.confidence!=null?(row.confidence*100).toFixed(1)+'%':'-'}</td><td>${row.camera_id||'-'}</td><td>${row.last_seen||row.created_at||'-'}</td></tr>`;
            if (type === 'alerts') return `<tr><td>${row.id||''}</td><td>${row.type||row.alert_type||'-'}</td><td>${row.message||'-'}</td><td>${row.camera_id||'-'}</td><td>${row.created_at||'-'}</td></tr>`;
            return `<tr><td>${row.tipo||''}</td><td>${row.total||0}</td></tr>`;
        }).join('') || '<tr><td colspan="10" style="text-align:center;color:var(--text-muted)">Sin datos en el rango seleccionado</td></tr>';
        card.style.display = '';
    } catch (e) {
        showNotification('Error al obtener vista previa: ' + e.message, 'error');
    }
}

async function generateReport() {
    const type = document.getElementById('reportType').value;
    const format = document.getElementById('reportFormat').value;
    const params = _repDateRange();
    params.set('format', format);

    if (!type || !format) {
        showNotification('Por favor, selecciona tipo y formato', 'warning');
        return;
    }

    try {
        showNotification('Generando reporte...', 'info');
        // Try export endpoint first, fallback to search data
        const exportUrl = `/api/v2/export/${type}?` + params;
        const r = await fetch(exportUrl, { credentials: 'include' });
        if (r.ok) {
            const blob = await r.blob();
            const ext = format === 'pdf' ? 'pdf' : format === 'csv' ? 'csv' : 'json';
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `reporte_${type}_${Date.now()}.${ext}`; a.click();
            URL.revokeObjectURL(url);
            showNotification('Reporte descargado', 'success');
        } else {
            // Fallback: download search results as JSON/CSV
            await repPreview();
            showNotification('Endpoint de exportación no disponible; usa vista previa', 'warning');
        }
    } catch (error) {
        showNotification(error.message || 'Error al generar reporte', 'error');
    }
}

/**
 * Buscar detecciones — live search listener
 */
document.addEventListener('DOMContentLoaded', () => {
    const deteccionSearch = document.getElementById('deteccionSearch');
    if (deteccionSearch) {
        let searchTimeout;
        deteccionSearch.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => loadDetecciones(), 350);
        });
    }

    const alertFilter = document.getElementById('alertFilter');
    if (alertFilter) {
        alertFilter.addEventListener('change', () => {
            loadAlerts();
        });
    }
});

// Inicializar cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Cargar configuración del servidor
    loadServerConfig();

    // Si el dashboard está visible al arrancar, lanzar polling de stats
    if (document.getElementById('page-dashboard')?.classList.contains('active')) {
        if (typeof startServerStatsPolling === 'function') startServerStatsPolling();
    }

    const alertFilter = document.getElementById('alertFilter');
    if (alertFilter) {
        alertFilter.addEventListener('change', () => {
            loadAlerts();
        });
    }
});

/**
 * Cargar configuración del servidor para clientes remotos
 */
async function loadServerConfig() {
    try {
        const response = await fetch('/api/v2/camera/config');
        if (response.ok) {
            const config = await response.json();
            
            // Actualizar elementos URL REMOTA en el dashboard (formato IP:PUERTO)
            const remoteUrl = document.getElementById('remote-url');
            if (remoteUrl) remoteUrl.textContent = `${config.public_ip}:${config.router_port}`;
            
            // Actualizar elementos URL LOCAL en el dashboard (formato IP:PUERTO)
            const localUrl = document.getElementById('local-url');
            if (localUrl) localUrl.textContent = `${config.local_ip}:${config.local_port}`;
            
            console.log('Server config loaded:', config);
        }
    } catch (error) {
        console.error('Error loading server config:', error);
        // Usar valores locales por defecto
        const ip = window.location.hostname || 'localhost';
        const port = window.location.port || '8000';
        
        const remoteUrl = document.getElementById('remote-url');
        const localUrl = document.getElementById('local-url');
        
        if (remoteUrl) remoteUrl.textContent = `${ip}:${port}`;
        if (localUrl) localUrl.textContent = `${ip}:${port}`;
    }
}

/**
 * Copiar texto al clipboard
 */
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const text = element.textContent;
    
    // Usar Clipboard API si está disponible
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification(' Copiado al portapapeles', 'success');
        }).catch(err => {
            console.error('Error copying:', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        // Fallback para navegadores más antiguos
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback para copiar al clipboard (navegadores antiguos)
 */
function fallbackCopyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showNotification(' Copiado al portapapeles', 'success');
    } catch (err) {
        console.error('Fallback copy failed:', err);
        showNotification(' Error al copiar', 'error');
    }
    document.body.removeChild(textarea);
}

// Cargar configuración del servidor cuando la página carga
document.addEventListener('DOMContentLoaded', () => {
    loadServerConfig();
    initCopyButtons();
});

/**
 * Inicializar event listeners para botones de copiar
 */
function initCopyButtons() {
    const btnCopyRemote = document.getElementById('btn-copy-remote');
    const btnCopyLocal = document.getElementById('btn-copy-local');
    
    if (btnCopyRemote) {
        btnCopyRemote.addEventListener('click', () => copyToClipboard('remote-url-full'));
    }
    
    if (btnCopyLocal) {
        btnCopyLocal.addEventListener('click', () => copyToClipboard('local-url-full'));
    }
}

/**
 * FUNCIONES DE CARGA DE DATOS PARA ROUTER
 * Estas funciones son llamadas por router.js cuando se navega a cada sección
 */

/**
 * Cargar cámaras
 */
async function loadCameras() {
    if (typeof camLoadRegistered === 'function') camLoadRegistered();
}

/**
 * Cargar detecciones unificadas (personas + vehículos)
 */
async function loadDetecciones() {
    const list = document.getElementById('deteccionesList');
    if (!list) return;
    const typeFilter = document.getElementById('deteccionTypeFilter')?.value || '';
    const searchTerm = document.getElementById('deteccionSearch')?.value?.toLowerCase() || '';
    try {
        const url = `/api/v2/search/items?limit=200${typeFilter ? '&type=' + typeFilter : ''}`;
        const res = await fetch(url, { credentials: 'include' });
        const data = await res.json();
        let items = data.results || [];
        if (searchTerm) {
            items = items.filter(i =>
                (i.item_id || '').toLowerCase().includes(searchTerm) ||
                (i.label || '').toLowerCase().includes(searchTerm)
            );
        }
        if (!items.length) {
            list.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Sin detecciones aún</td></tr>';
            return;
        }
        list.innerHTML = items.map(item => {
            const ts = item.detected_at ? new Date(item.detected_at).toLocaleString('es-ES') : '—';
            const conf = item.confidence ? (item.confidence * 100).toFixed(1) + '%' : '—';
            const label = item.label || item.item_id || item.id;
            const caption = `${label} • ${conf} • ${ts}`;
            const img = item.image_path
                ? `<img src="${item.image_path}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;border:1px solid var(--border);cursor:zoom-in;" loading="lazy"
                       onclick="_openLightbox('${item.image_path}','${caption.replace(/'/g, "\\'")}')"
                       onerror="this.src='/static/img/no-photo.svg';this.style.cursor='default'">`
                : `<img src="/static/img/no-photo.svg" style="width:48px;height:48px;border-radius:6px;opacity:0.4;">`;
            const typeBadge = item.type === 'person'
                ? '<span class="badge badge-info">Persona</span>'
                : '<span class="badge badge-warning">Vehículo</span>';
            const times = item.times_detected || 1;
            const pctColor = item.confidence >= 0.8 ? '#34d399' : item.confidence >= 0.6 ? '#fbbf24' : '#f87171';
            return `
                <tr>
                    <td>${img}</td>
                    <td>${typeBadge}</td>
                    <td style="font-size:12px;"><strong>${item.item_id || item.id}</strong>${item.label ? '<br><span class="text-muted">' + item.label + '</span>' : ''}</td>
                    <td style="font-size:12px;">Cam ID ${item.camera_id}</td>
                    <td><span style="font-weight:700;color:${pctColor};">${conf}</span></td>
                    <td><span class="badge badge-success">${times}</span></td>
                    <td style="font-size:12px;">${ts}</td>
                </tr>`;
        }).join('');
    } catch (error) {
        console.error('Error cargando detecciones:', error);
        if (list) list.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Error al cargar</td></tr>';
    }
}

// Keep legacy aliases so any stray calls don't break
function loadPersons() { loadDetecciones(); }
function loadVehicles() { loadDetecciones(); }

/**
 * Cargar alertas
 */
async function loadAlerts() {
    try {
        console.log('Cargando alertas...');
        const filter = document.getElementById('alertFilter')?.value || null;
        const alerts = await apiGetAlerts(filter);
        
        const alertsList = document.getElementById('alertsList');
        if (alertsList && alerts && Array.isArray(alerts)) {
            if (alerts.length > 0) {
                alertsList.innerHTML = alerts.map(alert => `
                    <div class="alert alert-${alert.severity || 'info'}">
                        <div class="alert-header">
                            <h4>${alert.title || 'Alerta'}</h4>
                            <span class="alert-time">${formatTimeAgo(alert.created_at)}</span>
                        </div>
                        <p>${alert.message || 'Sin descripción'}</p>
                    </div>
                `).join('');
            } else {
                alertsList.innerHTML = '<p class="text-center text-muted">No hay alertas</p>';
            }
        }
    } catch (error) {
        console.error('Error cargando alertas:', error);
        showNotification('Error al cargar alertas', 'error');
    }
}

/**
 * Cargar estadísticas (para dashboard)
 */
async function loadStatistics() {
    try {
        const response = await fetch('/api/estadisticas');
        const data = await response.json();
        
        // Actualizar widgets del dashboard
        const totalCameras = document.getElementById('totalCameras');
        const totalPersons = document.getElementById('totalPersons');
        const totalVehicles = document.getElementById('totalVehicles');
        const totalAlerts = document.getElementById('totalAlerts');
        
        if (totalCameras) totalCameras.textContent = data.cameras || 0;
        if (totalPersons) totalPersons.textContent = data.persons || 0;
        if (totalVehicles) totalVehicles.textContent = data.vehicles || 0;
        if (totalAlerts) totalAlerts.textContent = data.alerts || 0;
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

/**
 * Cargar últimas detecciones (para dashboard)
 */
async function loadLastDetections() {
    try {
        // Cargar últimas personas y vehículos detectados
        const persons = await apiGetPersons(5);
        const vehicles = await apiGetVehicles(5);
        
        // Actualizar UI si es necesario
        console.log('Últimas detecciones cargadas');
    } catch (error) {
        console.error('Error cargando últimas detecciones:', error);
    }
}

// ── MARKER: main.js loaded ───────────────────────────────────────────────────
window.__mainJsLoaded = true;
console.log('[main.js] Loaded.');
