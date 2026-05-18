// ── BD: Tab switching ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.bd-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.bd-tab').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.bd-panel').forEach(p => { p.style.display='none'; p.classList.remove('active'); });
            btn.classList.add('active');
            const panel = document.getElementById(btn.dataset.tab);
            if (panel) { panel.style.display='block'; panel.classList.add('active'); }
            if (btn.dataset.tab === 'bd-tablas') bdLoadTables();
        });
    });
    // Preset fechas consulta simplificada (últimas 24h por defecto)
    qsPreset(24);
});

// También cargar tablas cuando se navegue a /bd
window.addEventListener('pageChange', (e) => {
    if (e.detail && e.detail.page === 'bd') bdLoadTables();
});

// ── BD: TABLAS ─────────────────────────────────────────────────────────────
let _bdCurrentTable = null;
let _bdCurrentPage  = 1;

async function bdLoadTables() {
    const wrap = document.getElementById('bd-tables-list');
    if (!wrap) return;
    wrap.innerHTML = '<span style="color:var(--text-muted);font-size:13px;">Cargando tablas...</span>';
    try {
        const res = await fetch('/api/db/tables', { credentials:'include' });
        const data = await res.json();
        wrap.innerHTML = '';
        (data.tables || []).forEach(t => {
            const chip = document.createElement('button');
            chip.className = 'table-chip';
            chip.innerHTML = `${t.name} <span class="chip-count">(${t.rows >= 0 ? t.rows : '?'})</span>`;
            chip.onclick = () => { bdOpenTable(t.name); document.querySelectorAll('.table-chip').forEach(c=>c.classList.remove('active')); chip.classList.add('active'); };
            wrap.appendChild(chip);
        });
    } catch(e) {
        wrap.innerHTML = '<span style="color:#e74c3c;">Error cargando tablas</span>';
    }
}

async function bdOpenTable(name, page=1) {
    _bdCurrentTable = name;
    _bdCurrentPage  = page;
    const wrap = document.getElementById('bd-table-content');
    const thead = document.getElementById('bd-data-thead');
    const tbody = document.getElementById('bd-data-tbody');
    const title = document.getElementById('bd-table-title');
    const info  = document.getElementById('bd-table-info');
    wrap.style.display = 'block';
    tbody.innerHTML = '<tr><td colspan="99" style="text-align:center;color:var(--text-muted);">Cargando...</td></tr>';
    try {
        const res  = await fetch(`/api/db/table/${name}?page=${page}&page_size=50`, { credentials:'include' });
        const data = await res.json();
        title.textContent = name;
        info.textContent  = `${data.total} filas · Página ${data.page}/${data.pages}`;
        document.getElementById('bd-prev-btn').disabled = page <= 1;
        document.getElementById('bd-next-btn').disabled = page >= data.pages;
        // Header
        thead.innerHTML = '<tr>' + (data.columns||[]).map(c=>`<th>${c}</th>`).join('') + '</tr>';
        // Body
        tbody.innerHTML = '';
        (data.rows||[]).forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = (data.columns||[]).map(c=>{
                const v = row[c];
                return `<td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${String(v??'').replace(/"/g,'&quot;')}">${v===null?'<span style="color:var(--text-muted);font-style:italic;">NULL</span>':String(v)}</td>`;
            }).join('');
            tbody.appendChild(tr);
        });
    } catch(e) {
        tbody.innerHTML = '<tr><td colspan="99" style="color:#e74c3c;">Error cargando datos</td></tr>';
    }
}

function bdTablePage(dir) {
    if (_bdCurrentTable) bdOpenTable(_bdCurrentTable, Math.max(1, _bdCurrentPage + dir));
}

// ── BD: SQL ────────────────────────────────────────────────────────────────
function bdSetSQL(sql) { document.getElementById('sqlQuery').value = sql; }

async function bdExecSQL() {
    const sql = (document.getElementById('sqlQuery')?.value || '').trim();
    const resWrap  = document.getElementById('bd-sql-result');
    const errWrap  = document.getElementById('bd-sql-error');
    const countEl  = document.getElementById('bd-sql-count');
    const thead    = document.getElementById('bd-sql-thead');
    const tbody    = document.getElementById('bd-sql-tbody');
    resWrap.style.display = 'none';
    errWrap.style.display = 'none';
    if (!sql) return;
    try {
        const res  = await fetch('/api/db/query', { method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify({sql}) });
        const data = await res.json();
        if (!res.ok) { errWrap.textContent = data.detail || 'Error'; errWrap.style.display='block'; return; }
        countEl.textContent = `${data.count} fila(s)`;
        thead.innerHTML = '<tr>' + (data.columns||[]).map(c=>`<th>${c}</th>`).join('') + '</tr>';
        tbody.innerHTML = '';
        (data.rows||[]).forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = (data.columns||[]).map(c=>{
                const v = row[c];
                return `<td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${String(v??'').replace(/"/g,'&quot;')}">${v===null?'<span style="color:var(--text-muted);font-style:italic;">NULL</span>':String(v)}</td>`;
            }).join('');
            tbody.appendChild(tr);
        });
        resWrap.style.display = 'block';
    } catch(e) { errWrap.textContent = 'Error de conexión'; errWrap.style.display='block'; }
}

// ── BD: CONSULTAS SIMPLIFICADAS ────────────────────────────────────────────
function qsPreset(hours) {
    const until = new Date();
    const since = new Date(until.getTime() - hours * 3600000);
    const fmt = d => d.toISOString().slice(0,16);
    document.getElementById('qs-since').value = fmt(since);
    document.getElementById('qs-until').value = fmt(until);
}

let _qsLastData = [];

async function qsSearch() {
    const since = document.getElementById('qs-since').value;
    const until = document.getElementById('qs-until').value;
    const errWrap = document.getElementById('qs-error');
    errWrap.style.display = 'none';
    if (!since || !until) { errWrap.textContent='Selecciona fecha y hora de inicio y fin'; errWrap.style.display='block'; return; }
    const types = [];
    if (document.getElementById('qs-alertas').checked)  types.push('alertas');
    if (document.getElementById('qs-personas').checked) types.push('personas');
    if (document.getElementById('qs-vehiculos').checked) types.push('vehiculos');
    if (!types.length) { errWrap.textContent='Selecciona al menos un tipo de evento'; errWrap.style.display='block'; return; }
    const limit = document.getElementById('qs-limit').value;
    const sevCritical = document.getElementById('qs-sev-critical').checked;
    const sevWarning  = document.getElementById('qs-sev-warning').checked;
    const sevInfo     = document.getElementById('qs-sev-info').checked;
    const allowedSev  = new Set();
    if (sevCritical) allowedSev.add('critical');
    if (sevWarning)  allowedSev.add('warning');
    if (sevInfo)     allowedSev.add('info');

    const url = `/api/timeline?since=${encodeURIComponent(since)}&until=${encodeURIComponent(until)}&types=${types.join(',')}&limit=${limit}`;
    const timeline = document.getElementById('qs-timeline');
    const resWrap  = document.getElementById('qs-results-wrap');
    timeline.innerHTML = '<p style="color:var(--text-muted);">Buscando...</p>';
    resWrap.style.display = 'block';
    try {
        const res  = await fetch(url, { credentials:'include' });
        const data = await res.json();
        if (!res.ok) { errWrap.textContent = data.detail || 'Error'; errWrap.style.display='block'; resWrap.style.display='none'; return; }
        let events = data.events || [];
        // Filtrar por severidad (solo alertas tienen severity)
        events = events.filter(ev => {
            if (ev.type === 'alerta') return allowedSev.has(ev.severity);
            return true;
        });
        _qsLastData = events;
        document.getElementById('qs-count').textContent = `${events.length} resultado(s)`;
        if (!events.length) { timeline.innerHTML='<p style="color:var(--text-muted);">Sin resultados para este rango.</p>'; return; }
        timeline.innerHTML = '';
        events.forEach(ev => {
            const dotClass = ev.type === 'alerta' ? `qs-dot-alerta-${ev.severity||'info'}` : `qs-dot-${ev.type}`;
            const ts = ev.ts ? new Date(ev.ts).toLocaleString('es-ES') : '—';
            const div = document.createElement('div');
            div.className = 'qs-event';
            div.innerHTML = `
                <div class="qs-dot ${dotClass}"></div>
                <div class="qs-body">
                    <div class="qs-title">${ev.title||'Evento'}</div>
                    ${ev.detail?`<div class="qs-detail">${ev.detail}</div>`:''}
                </div>
                <div class="qs-ts">${ts}</div>`;
            timeline.appendChild(div);
        });
    } catch(e) { errWrap.textContent='Error de conexión'; errWrap.style.display='block'; resWrap.style.display='none'; }
}

function qsExportCSV() {
    if (!_qsLastData.length) { alert('Primero realiza una búsqueda'); return; }
    const cols = ['type','ts','title','detail','severity'];
    const rows = [cols.join(','), ..._qsLastData.map(ev => cols.map(c => `"${String(ev[c]??'').replace(/"/g,'""')}"`).join(','))];
    const blob = new Blob([rows.join('\n')], {type:'text/csv;charset=utf-8;'});
    const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='consulta.csv'; a.click();
}
