
// ── Historial real de clientes ──
// Translation helper (reads from language.js global)
function _camT(key, fallback) {
  try { return (translations && translations[currentLang] && translations[currentLang][key]) || fallback; }
  catch(e) { return fallback; }
}

let _camActiveIds = new Set();
let _camFeedInterval = null;
let _camRefreshMs = 400;

async function camLoadRegistered() {
    const tbody = document.getElementById('cam-registered-list');
    try {
        const res = await fetch('/api/v2/camera/active-list', { credentials: 'include' });
        const data = res.ok ? await res.json() : { cameras: [] };
        const cameras = data.cameras || [];
        if (!cameras.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Ningún dispositivo ha transmitido en esta sesión</td></tr>';
            return;
        }
        tbody.innerHTML = cameras.map(c => {
            const live = c.active;
            const badge = live
                ? `<span style="font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;background:#064e3b;color:#34d399;">● Activo</span>`
                : `<span style="font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;background:#374151;color:#9ca3af;">Inactivo</span>`;
            return `<tr>
                <td>${badge}</td>
                <td style="font-weight:600;">${c.camera_id}</td>
                <td style="font-size:12px;font-family:monospace;">${c.client_ip || '—'}</td>
                <td style="font-size:12px;color:var(--text-muted);">${c.first_seen || '—'}</td>
                <td style="font-size:12px;color:var(--text-muted);">${c.last_seen || '—'}</td>
                <td style="font-size:12px;">${c.frames}</td>
                <td style="font-size:12px;">${c.fps}</td>
            </tr>`;
        }).join('');
    } catch(e) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Error al cargar</td></tr>';
    }
}

// Auto-refresh cada 8s
setInterval(() => { camLoadRegistered(); }, 8000);

// Iniciar polling de feeds al cargar
camStartFeedPolling();

// ── Streaming en tiempo real ──
async function camLoadStreaming() {
    const wrap = document.getElementById('cam-streaming-list');
    try {
        const res = await fetch('/api/v2/camera/active-list', { credentials:'include' });
        const data = await res.json();
        if (!data.cameras.length) {
            wrap.innerHTML = '<p class="text-muted" style="padding:16px;">Ninguna cámara streaming activa.</p>'; return;
        }
        wrap.innerHTML = data.cameras.map(c => {
            const live = c.active;
            return `<div class="cam-stream-row">
                <div class="cam-dot ${live?'live':'offline'}"></div>
                <div style="flex:1;font-weight:600;">${c.camera_id}</div>
                <div style="display:flex;gap:16px;font-size:12px;color:var(--text-muted);">
                    <span><b style="color:var(--text-primary);">${c.fps}</b> fps</span>
                    <span><b style="color:var(--text-primary);">${c.resolution}</b></span>
                    <span><b style="color:var(--text-primary);">${c.frames}</b> frames</span>
                    <span>Personas: <b style="color:var(--text-primary);">${c.persons_total}</b></span>
                    <span>Vehículos: <b style="color:var(--text-primary);">${c.cars_total}</b></span>
                </div>
                <span style="font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;${live?'background:#064e3b;color:#34d399':'background:#374151;color:#9ca3af'}">${live?'En directo':'Inactiva'}</span>
            </div>`;
        }).join('');
    } catch(e) { wrap.innerHTML='<p class="text-muted" style="padding:16px;">Error al cargar.</p>'; }
}

// ── Feeds en directo ──  // poll cada 400ms ≈ 2.5fps en el dashboard

function camSetRefreshRate(ms) { _camRefreshMs = +ms; if(_camFeedInterval) { camStopFeedPolling(); camStartFeedPolling(); } }

async function camRefreshFeeds() {
    const grid = document.getElementById('cam-feeds-grid');
    const noFeeds = document.getElementById('cam-no-feeds');
    try {
        const res = await fetch('/api/v2/camera/active-list', { credentials:'include' });
        const data = await res.json();
        const actives = data.cameras.filter(c => c.has_frame || c.active);
        if (!actives.length) { noFeeds.style.display='block'; grid.innerHTML=''; return; }
        noFeeds.style.display='none';
        // Crear cards para cámaras nuevas, actualizar stats en existentes
        const existing = new Set(Array.from(grid.querySelectorAll('.cam-feed-card')).map(el=>el.dataset.camId));
        actives.forEach(c => {
            const key = c.camera_id.replace(/[^a-z0-9]/gi,'_');
            if (!existing.has(c.camera_id)) {
                const card = document.createElement('div');
                card.className='cam-feed-card'; card.dataset.camId=c.camera_id;
                // Dos streams MJPEG por cámara: directo (raw) y IA (YOLO anotado)
                card.innerHTML=`
                    <div class="cam-feed-header">
                        <span class="cam-feed-title">${c.camera_id}</span>
                        <span class="cam-feed-badge ${c.active?'live':'offline'}" id="cam-badge-${key}">${c.active?`◎◎ ${_camT('camFeedLive','En directo')}`:`${_camT('twoFaInactivo','Inactiva')}`}</span>
                    </div>
                    <div class="cam-dual-streams">
                        <div class="cam-stream-panel">
                            <div class="cam-stream-label">${_camT('camFeedLive','En directo')}</div>
                            <div class="cam-zoom-viewport" id="vp-live-${key}">
                                <img class="cam-feed-img cam-zoomable" id="cam-img-${key}"
                                    src="/api/v2/camera/stream/${encodeURIComponent(c.camera_id)}"
                                    alt="Feed ${c.camera_id}"
                                    onerror="this.style.opacity='.3'">
                            </div>
                            <div class="cam-zoom-hint">${_camT('camFeedZoomHint','Rueda: zoom · Doble clic: reset')}</div>
                        </div>
                        <div class="cam-stream-panel">
                            <div class="cam-stream-label cam-stream-label-ai">${_camT('camFeedAI','IA · YOLO')}</div>
                            <div class="cam-zoom-viewport" id="vp-ai-${key}">
                                <img class="cam-feed-img cam-zoomable" id="cam-ai-${key}"
                                    src="/api/v2/camera/stream-ai/${encodeURIComponent(c.camera_id)}"
                                    alt="IA Feed ${c.camera_id}"
                                    onerror="this.style.opacity='.3'">
                            </div>
                            <div class="cam-zoom-hint">${_camT('camFeedZoomHint','Rueda: zoom · Doble clic: reset')}</div>
                        </div>
                    </div>
                    <div class="cam-feed-stats">
                        <div class="cam-feed-stat"><span>FPS</span><span id="cam-fps-${key}">${c.fps}</span></div>
                        <div class="cam-feed-stat"><span>Resolución</span><span>${c.resolution}</span></div>
                        <div class="cam-feed-stat"><span>Personas</span><span id="cam-pers-${key}">${c.persons_total}</span></div>
                        <div class="cam-feed-stat"><span>Vehículos</span><span id="cam-veh-${key}">${c.cars_total}</span></div>
                    </div>`;
                grid.appendChild(card);
                // Inicializar zoom en ambos viewports
                _camInitZoom('vp-live-'+key);
                _camInitZoom('vp-ai-'+key);
            } else {
                // Solo actualizar stats — NO tocar img.src (MJPEG gestiona el stream)
                const fps = document.getElementById('cam-fps-'+key);
                if (fps) fps.textContent=c.fps;
                const pers = document.getElementById('cam-pers-'+key);
                if (pers) pers.textContent=c.persons_total;
                const veh = document.getElementById('cam-veh-'+key);
                if (veh) veh.textContent=c.cars_total;
                const badge = document.getElementById('cam-badge-'+key);
                if (badge) { badge.textContent=c.active?`◎◎ ${_camT('camFeedLive','En directo')}`:`${_camT('twoFaInactivo','Inactiva')}`; badge.className='cam-feed-badge '+(c.active?'live':'offline'); }
            }
        });
        // Quitar cards de cámaras que ya no tienen frames ni están activas
        const activeIds = new Set(actives.map(c=>c.camera_id));
        grid.querySelectorAll('.cam-feed-card').forEach(el => {
            if(!activeIds.has(el.dataset.camId)) {
                // Detener ambos streams MJPEG antes de quitar el card
                el.querySelectorAll('img').forEach(img => { img.src = ''; });
                el.remove();
            }
        });
    } catch(e) {}
}

function camStartFeedPolling() {
    camRefreshFeeds();
    // Poll solo para actualizar stats (fps, personas…), no para las imágenes
    _camFeedInterval = setInterval(camRefreshFeeds, Math.max(_camRefreshMs, 2000));
}
function camStopFeedPolling() {
    if (_camFeedInterval) { clearInterval(_camFeedInterval); _camFeedInterval=null; }
}

// ── Zoom con rueda de ratón y pellizco táctil ──────────────────────────────
function _camInitZoom(viewportId) {
    const vp = document.getElementById(viewportId);
    if (!vp || vp._zoomInited) return;
    vp._zoomInited = true;
    const img = vp.querySelector('img');
    if (!img) return;

    let scale = 1, originX = 50, originY = 50;
    let startDist = 0, startScale = 1;

    function applyZoom() {
        img.style.transformOrigin = `${originX}% ${originY}%`;
        img.style.transform = scale === 1 ? '' : `scale(${scale})`;
    }

    // Zoom con rueda — centrado en el cursor
    vp.addEventListener('wheel', e => {
        e.preventDefault();
        const rect = vp.getBoundingClientRect();
        originX = ((e.clientX - rect.left) / rect.width) * 100;
        originY = ((e.clientY - rect.top) / rect.height) * 100;
        scale = Math.min(6, Math.max(1, scale * (e.deltaY < 0 ? 1.12 : 0.89)));
        applyZoom();
    }, { passive: false });

    // Pellizco táctil
    vp.addEventListener('touchstart', e => {
        if (e.touches.length === 2) {
            startDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            startScale = scale;
        }
    }, { passive: true });
    vp.addEventListener('touchmove', e => {
        if (e.touches.length === 2) {
            const dist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            scale = Math.min(6, Math.max(1, startScale * (dist / startDist)));
            applyZoom();
        }
    }, { passive: true });

    // Doble clic → reset zoom
    vp.addEventListener('dblclick', () => {
        scale = 1; originX = 50; originY = 50;
        applyZoom();
    });
}
