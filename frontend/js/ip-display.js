/**
 * ip-display.js — Carga IPs, genera QRs y conecta botones de copiar/abrir
 */

// ── URLs almacenadas en variables (no depender de leer el DOM) ────────────────
let _camLocalUrl  = '';
let _camRemoteUrl = '';
let _localUrlFull = '';
let _remoteUrlFull = '';

// ── Utilidades ────────────────────────────────────────────────────────────────

function _setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function _makeQR(containerId, url) {
    if (!url) return;
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    container.style.display = 'inline-block';
    if (typeof QRCode !== 'undefined') {
        new QRCode(container, {
            text: url,
            width: 88,
            height: 88,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M
        });
    } else {
        // Fallback: Google Charts QR (muy fiable, no requiere cookies)
        const img = document.createElement('img');
        img.alt = 'QR';
        img.style.cssText = 'width:88px;height:88px;display:block;';
        img.src = 'https://chart.googleapis.com/chart?chs=88x88&cht=qr&chl=' + encodeURIComponent(url) + '&choe=UTF-8';
        img.onerror = () => { container.style.display = 'none'; };
        container.appendChild(img);
    }
}

function _copyText(text, btn) {
    if (!text || text === 'Cargando...' || text === 'No disponible' || text === '') return;
    const original = btn ? btn.textContent : '';
    const done = () => {
        if (btn) {
            btn.textContent = 'Copiado';
            setTimeout(() => { btn.textContent = original; }, 2000);
        }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(() => _fallbackCopy(text, done));
    } else {
        _fallbackCopy(text, done);
    }
}

function _fallbackCopy(text, done) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0;width:1px;height:1px;';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try { document.execCommand('copy'); done(); } catch (_) {}
    document.body.removeChild(ta);
}

function _wireBtn(id, action) {
    const btn = document.getElementById(id);
    if (btn) btn.addEventListener('click', () => action(btn));
}

// ── Principal ─────────────────────────────────────────────────────────────────

async function loadServerIPs() {
    try {
        const res  = await fetch('/api/server-ips', { credentials: 'include' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();

        const publicPort     = String(data.port || '16000');
        const remoteProtocol = data.protocol || (
            (publicPort === '443' || publicPort === '16443') ? 'https' : 'http'
        );

        if (data.tunnel_url) {
            // Tunnel is active — use the tunnel URL (always works publicly)
            _remoteUrlFull = data.tunnel_url;
            _camRemoteUrl  = `${data.tunnel_url}/camara-cliente`;
        } else if (data.public_ip) {
            _remoteUrlFull = `${remoteProtocol}://${data.public_ip}:${publicPort}`;
            _camRemoteUrl  = `${_remoteUrlFull}/camara-cliente`;
        }

        if (_remoteUrlFull) {
            _setText('remote-url',      data.tunnel_url ? data.tunnel_url : data.public_ip);
            _setText('remote-url-full', _remoteUrlFull);
            _makeQR('qr-server-remote', _remoteUrlFull);

            _setText('cam-client-remote', _camRemoteUrl);
            _makeQR('qr-cam-remote', _camRemoteUrl);
        } else {
            _setText('remote-url',        'No disponible');
            _setText('remote-url-full',   'No disponible');
            _setText('cam-client-remote', 'No disponible');
        }

    } catch (e) {
        console.error('[IPs] Error cargando IPs del servidor:', e);
        _setText('remote-url',        'Error');
        _setText('remote-url-full',   'Error al cargar');
        _setText('cam-client-remote', 'Error al cargar');
    }
}

function setupButtons() {
    _wireBtn('btn-copy-remote',     btn => _copyText(_remoteUrlFull, btn));
    _wireBtn('btn-open-cam-remote', () => {
        if (_camRemoteUrl) window.open(_camRemoteUrl, '_blank');
        else alert('URL no disponible aún.');
    });
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    setupButtons();
    loadServerIPs();
});


