document.addEventListener('DOMContentLoaded', async () => {
    await requireAuth?.();

    // ── Helpers datetime-local ──────────────────────────────────────────────
    function toLocal(dt) {
        // dt: Date → "YYYY-MM-DDTHH:MM" in local timezone for datetime-local input
        const pad = n => String(n).padStart(2, '0');
        return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
    }
    function setRange(since, until) {
        document.getElementById('tlSince').value = toLocal(since);
        document.getElementById('tlUntil').value = toLocal(until);
    }

    // Presets
    const presets = {
        '1h':       () => { const n=new Date(); setRange(new Date(n-3600000), n); },
        '6h':       () => { const n=new Date(); setRange(new Date(n-6*3600000), n); },
        '24h':      () => { const n=new Date(); setRange(new Date(n-86400000), n); },
        'today':    () => { const n=new Date(); const s=new Date(n); s.setHours(0,0,0,0); setRange(s, n); },
        'yesterday':() => {
            const n=new Date(); n.setHours(0,0,0,0);
            const s=new Date(n); s.setDate(s.getDate()-1);
            const e=new Date(n); e.setSeconds(-1);
            setRange(s, e);
        },
        '7d': () => { const n=new Date(); setRange(new Date(n-7*86400000), n); },
    };

    document.querySelectorAll('.tl-chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tl-chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            presets[btn.dataset.preset]?.();
        });
    });

    // Default: last 24h
    presets['24h']();
    document.querySelector('[data-preset="24h"]').classList.add('active');

    // ── Search ──────────────────────────────────────────────────────────────
    document.getElementById('tlSearch').addEventListener('click', doSearch);

    async function doSearch() {
        const since = document.getElementById('tlSince').value;
        const until = document.getElementById('tlUntil').value;
        if (!since || !until) { alert('Selecciona fecha de inicio y fin'); return; }

        const types = [];
        if (document.getElementById('cbAlertas').checked)   types.push('alertas');
        if (document.getElementById('cbPersonas').checked)  types.push('personas');
        if (document.getElementById('cbVehiculos').checked) types.push('vehiculos');
        if (!types.length) { alert('Selecciona al menos un tipo de evento'); return; }

        const btn = document.getElementById('tlSearch');
        btn.disabled = true;
        btn.textContent = 'Buscando...';

        document.getElementById('tlResults').innerHTML = '<div class="tl-loading">Cargando eventos...</div>';
        document.getElementById('tlSummary').style.display = 'none';

        try {
            // Convert local datetime-local value (YYYY-MM-DDTHH:MM) to ISO string for backend
            const sinceISO = since + ':00';
            const untilISO = until + ':00';

            const res = await fetch(
                `/api/timeline?since=${encodeURIComponent(sinceISO)}&until=${encodeURIComponent(untilISO)}&types=${types.join(',')}`,
                { credentials: 'include' }
            );

            if (!res.ok) {
                const err = await res.json().catch(()=>({detail:'Error desconocido'}));
                document.getElementById('tlResults').innerHTML = `<div class="tl-empty" style="color:#e74c3c;">Error: ${err.detail || res.status}</div>`;
                return;
            }

            const data = await res.json();
            renderResults(data);
        } catch (e) {
            document.getElementById('tlResults').innerHTML = `<div class="tl-empty" style="color:#e74c3c;">Error de conexión: ${e.message}</div>`;
        } finally {
            btn.disabled = false;
            btn.textContent = '🔍 Buscar';
        }
    }

    // ── Render ───────────────────────────────────────────────────────────────
    function renderResults(data) {
        const summaryEl = document.getElementById('tlSummary');
        const resultsEl = document.getElementById('tlResults');

        if (!data.events || data.events.length === 0) {
            summaryEl.style.display = 'none';
            resultsEl.innerHTML = `
                <div class="tl-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 11H11V7h2v6zm0 4h-2v-2h2v2z"/></svg>
                    No se encontraron eventos en el rango seleccionado
                </div>`;
            return;
        }

        // Summary counts
        const counts = {};
        data.events.forEach(e => {
            const key = e.type === 'alerta' ? `alerta-${e.severity}` : e.type;
            counts[key] = (counts[key] || 0) + 1;
        });

        const badgeCfg = [
            { key: 'alerta-critical', dot: 'dot-alerta-critical', label: '🔴 Críticas' },
            { key: 'alerta-warning',  dot: 'dot-alerta-warning',  label: '🟠 Advertencias' },
            { key: 'alerta-info',     dot: 'dot-alerta-info',     label: '🔵 Informativas' },
            { key: 'persona',         dot: 'dot-persona',         label: '🟢 Personas' },
            { key: 'vehiculo',        dot: 'dot-vehiculo',        label: '🟣 Vehículos' },
        ];
        summaryEl.innerHTML = badgeCfg
            .filter(b => counts[b.key])
            .map(b => `<div class="tl-summary-badge"><span class="dot ${b.dot}"></span>${b.label}: <strong>${counts[b.key]}</strong></div>`)
            .join('') +
            `<div class="tl-summary-badge">Total: <strong>${data.total}</strong></div>`;
        summaryEl.style.display = 'flex';

        // Group by date
        const groups = {};
        data.events.forEach(e => {
            const d = e.ts ? e.ts.slice(0, 10) : 'Sin fecha';
            if (!groups[d]) groups[d] = [];
            groups[d].push(e);
        });

        let html = '';
        Object.keys(groups).sort().reverse().forEach(day => {
            const label = formatDay(day);
            html += `<div style="font-size:12px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.06em; margin: 18px 0 8px 0;">${label}</div>`;
            html += '<div class="tl-list">';
            groups[day].slice().reverse().forEach(e => {
                const time = e.ts ? e.ts.slice(11, 16) : '--:--';
                const typeKey = e.type === 'alerta' ? `alerta-${e.severity}` : e.type;
                const tagClass = `tag-${typeKey}`;
                const tagLabel = e.type === 'alerta'
                    ? (e.severity === 'critical' ? '🔴 CRÍTICA' : e.severity === 'warning' ? '🟠 AVISO' : '🔵 INFO')
                    : e.type === 'persona' ? '🟢 PERSONA' : '🟣 VEHÍCULO';

                html += `
                <div class="tl-item" data-type="${e.type}" data-sev="${e.severity || ''}">
                    <div class="tl-item-header">
                        <span class="tl-item-time">${time}</span>
                        <span class="tl-item-tag ${tagClass}">${tagLabel}</span>
                    </div>
                    <div class="tl-item-title">${escHtml(e.title)}</div>
                    ${e.detail ? `<div class="tl-item-detail">${escHtml(e.detail)}</div>` : ''}
                </div>`;
            });
            html += '</div>';
        });

        resultsEl.innerHTML = html;
    }

    function formatDay(dateStr) {
        if (dateStr === 'Sin fecha') return dateStr;
        const d = new Date(dateStr + 'T12:00:00');
        const today = new Date(); today.setHours(0,0,0,0);
        const yesterday = new Date(today); yesterday.setDate(yesterday.getDate()-1);
        if (d >= today) return 'Hoy — ' + d.toLocaleDateString('es-ES', {weekday:'long', day:'numeric', month:'long'});
        if (d >= yesterday) return 'Ayer — ' + d.toLocaleDateString('es-ES', {weekday:'long', day:'numeric', month:'long'});
        return d.toLocaleDateString('es-ES', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
    }

    function escHtml(str) {
        return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    // Profile/logout
    document.getElementById('profileBtn')?.addEventListener('click', () => {
        document.getElementById('profileDropdown')?.classList.toggle('hidden');
    });
    document.getElementById('logoutBtn')?.addEventListener('click', async () => {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
        window.location.href = '/';
    });
    document.addEventListener('click', e => {
        if (!e.target.closest('#profileBtn')) document.getElementById('profileDropdown')?.classList.add('hidden');
        if (!e.target.closest('#languageBtn')) document.getElementById('languageDropdown')?.classList.add('hidden');
    });
});
