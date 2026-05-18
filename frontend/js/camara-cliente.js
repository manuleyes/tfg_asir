const SERVER = window.location.origin;  // same server
let stream = null;
let intervalId = null;
let frames = 0, errors = 0, bytes = 0;
let lastFpsTs = Date.now(), lastFpsFrames = 0;

const video   = document.getElementById('localVideo');
const canvas  = document.getElementById('captureCanvas');
const ctx     = canvas.getContext('2d');
const badge   = document.getElementById('statusBadge');
const logBox  = document.getElementById('logBox');

// ── Language switcher ────────────────────────────────────────────────────────
function switchLang(lang) {
    i18n.setLanguage(lang);
    document.documentElement.lang = lang === 'jp' ? 'ja' : lang;
    document.title = i18n.t('camaraClienteTitle');
    if (!stream) logBox.textContent = i18n.t('esperando');
    if (!intervalId && !stream) setBadge(i18n.t('inactivo'), '');
    ['Es', 'En', 'Jp'].forEach(l => {
        const btn = document.getElementById('lb' + l);
        if (btn) btn.classList.toggle('active-lang', l.toLowerCase() === lang);
    });
}

// ── Detect secure context ────────────────────────────────────────────────────
(function checkSecureContext() {
    const isSecure = window.isSecureContext;
    const isLocalhost = ['localhost', '127.0.0.1', '::1'].includes(location.hostname);
    if (!isSecure && !isLocalhost) {
        const warn = document.createElement('div');
        warn.style.cssText = 'background:#7f1d1d;color:#fca5a5;padding:14px 18px;border-radius:8px;font-size:13px;line-height:1.5;margin-bottom:4px;';
        warn.innerHTML = `
            <strong>${i18n.t('httpsWarningTitle')}</strong><br>
            ${i18n.t('httpsWarningBody')}<br>
            <strong>${i18n.t('httpsWarningSolLabel')}</strong><br>
            &bull; ${i18n.t('httpsWarningSol1')} <code style="background:#991b1b;padding:1px 5px;border-radius:3px;">http://localhost:16000/camara-cliente</code><br>
            &bull; ${i18n.t('httpsWarningSol2')}<br>
            <em style="font-size:11px;">${i18n.t('httpsWarningTech')}</em>
        `;
        const main = document.querySelector('.main');
        if (main) main.insertBefore(warn, main.firstChild);
        document.getElementById('btnStart').disabled = true;
        setBadge(i18n.t('httpsRequerido'), 'error');
    }
})();

document.getElementById('quality').addEventListener('input', e => {
    document.getElementById('qualityVal').textContent = e.target.value;
});
document.getElementById('fpsRange').addEventListener('input', e => {
    document.getElementById('fpsVal').textContent = e.target.value;
    if (intervalId) { clearInterval(intervalId); intervalId = setInterval(sendFrame, 1000 / +e.target.value); }
});

function log(msg) {
    const t = new Date().toLocaleTimeString();
    logBox.textContent = `[${t}] ${msg}`;
}

function setBadge(text, cls) {
    badge.className = 'badge ' + (cls || '');
    badge.textContent = text;
}

async function startStream() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setBadge(i18n.t('errorSinSoporte'), 'error');
        log(i18n.t('errorGetUserMedia'));
        return;
    }
    try {
        const facing = document.getElementById('facingMode').value;
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: facing, width: { ideal: 640 }, height: { ideal: 480 } },
            audio: false
        });
        video.srcObject = stream;
        setBadge(i18n.t('transmitiendo'), 'active');
        document.getElementById('btnStart').disabled = true;
        document.getElementById('btnStop').disabled = false;
        const fps = +document.getElementById('fpsRange').value;
        intervalId = setInterval(sendFrame, 1000 / fps);
        log(i18n.t('streamIniciado'));
    } catch(e) {
        setBadge(i18n.t('errorCamara'), 'error');
        if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
            log(i18n.t('permisoDenegado'));
        } else if (e.name === 'NotFoundError' || e.name === 'DevicesNotFoundError') {
            log(i18n.t('camaraNoEncontrada'));
        } else if (e.name === 'NotReadableError') {
            log(i18n.t('camaraEnUso'));
        } else {
            log('Error: ' + e.message);
        }
    }
}

function stopStream() {
    clearInterval(intervalId); intervalId = null;
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    video.srcObject = null;
    setBadge(i18n.t('inactivo'), '');
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
    log(i18n.t('streamDetenido'));
}

async function flipCamera() {
    const wasRunning = !!intervalId;
    if (wasRunning) stopStream();
    const sel = document.getElementById('facingMode');
    sel.value = sel.value === 'user' ? 'environment' : 'user';
    if (wasRunning) await startStream();
}

async function sendFrame() {
    if (!stream) return;
    const vt = stream.getVideoTracks()[0];
    if (!vt || vt.readyState !== 'live') return;

    const settings = vt.getSettings();
    canvas.width  = settings.width  || 640;
    canvas.height = settings.height || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const quality = +document.getElementById('quality').value / 100;
    const cameraId = document.getElementById('cameraId').value.trim() || 'mobile-1';

    canvas.toBlob(async blob => {
        if (!blob) return;
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');
        formData.append('camera_id', cameraId);
        try {
            const res = await fetch(`${SERVER}/api/v2/camera/upload?camera_id=${encodeURIComponent(cameraId)}`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                frames++;
                bytes += blob.size;
                document.getElementById('statFrames').textContent = frames;
                document.getElementById('statKb').textContent = (bytes / 1024).toFixed(0);
                const now = Date.now();
                if (now - lastFpsTs >= 2000) {
                    const fps = ((frames - lastFpsFrames) / ((now - lastFpsTs) / 1000)).toFixed(1);
                    document.getElementById('statFps').textContent = fps;
                    lastFpsTs = now; lastFpsFrames = frames;
                }
            } else {
                errors++;
                document.getElementById('statErr').textContent = errors;
                if (errors <= 3) log(i18n.t('errorHttp') + res.status);
            }
        } catch(e) {
            errors++;
            document.getElementById('statErr').textContent = errors;
            if (errors <= 3) log(i18n.t('errorRed') + e.message);
        }
    }, 'image/jpeg', quality);
}

// ── Init language state ───────────────────────────────────────────────────────
(function initLang() {
    const lang = i18n.currentLanguage;
    document.documentElement.lang = lang === 'jp' ? 'ja' : lang;
    document.title = i18n.t('camaraClienteTitle');
    logBox.textContent = i18n.t('esperando');
    setBadge(i18n.t('inactivo'), '');
    ['Es', 'En', 'Jp'].forEach(l => {
        const btn = document.getElementById('lb' + l);
        if (btn) btn.classList.toggle('active-lang', l.toLowerCase() === lang);
    });
})();
