/**
 * export-data.js - Funciones para exportar datos a CSV y Excel
 */

/**
 * Exportar datos de una entidad al formato indicado
 * @param {string} entity - 'personas' | 'vehiculos' | 'alertas' | 'camaras'
 * @param {string} format - 'csv' | 'excel'
 */
async function exportData(entity, format) {
    const endpoint = `/api/export/${entity}/${format}`;

    try {
        showExportSpinner(entity, format, true);

        const response = await fetch(endpoint, {
            method: 'GET',
            credentials: 'include',
        });

        if (response.status === 401 || response.status === 403) {
            if (typeof showNotification === 'function') {
                showNotification('Sin autorización para exportar', 'error');
            }
            return;
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(err.detail || 'Error exportando datos');
        }

        // Obtener nombre de archivo desde Content-Disposition
        const disposition = response.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : `${entity}_export.${format === 'excel' ? 'xlsx' : 'csv'}`;

        // Descargar el archivo
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        if (typeof showNotification === 'function') {
            showNotification(`Exportado: ${filename}`, 'success');
        }

    } catch (error) {
        console.error('[Export] Error:', error);
        if (typeof showNotification === 'function') {
            showNotification(error.message || 'Error al exportar', 'error');
        }
    } finally {
        showExportSpinner(entity, format, false);
    }
}

function showExportSpinner(entity, format, show) {
    const btnId = `export-btn-${entity}-${format}`;
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.disabled = show;
    btn.textContent = show ? 'Exportando...' : (format === 'excel' ? 'Excel' : 'CSV');
}

/**
 * Crear toolbar de exportación para una sección
 * @param {string} entity - entidad a exportar
 * @param {HTMLElement} container - contenedor donde insertar los botones
 */
function createExportToolbar(entity, container) {
    if (!container) return;

    // Evitar duplicados
    if (container.querySelector('.export-toolbar')) return;

    const toolbar = document.createElement('div');
    toolbar.className = 'export-toolbar';

    const csvBtn = document.createElement('button');
    csvBtn.id = `export-btn-${entity}-csv`;
    csvBtn.className = 'btn btn-sm btn-outline';
    csvBtn.textContent = 'CSV';
    csvBtn.title = `Descargar ${entity} en formato CSV`;
    csvBtn.addEventListener('click', () => exportData(entity, 'csv'));

    const excelBtn = document.createElement('button');
    excelBtn.id = `export-btn-${entity}-excel`;
    excelBtn.className = 'btn btn-sm btn-outline btn-excel';
    excelBtn.textContent = 'Excel';
    excelBtn.title = `Descargar ${entity} en formato Excel`;
    excelBtn.addEventListener('click', () => exportData(entity, 'excel'));

    const label = document.createElement('span');
    label.className = 'export-label';
    label.textContent = 'Exportar:';

    toolbar.appendChild(label);
    toolbar.appendChild(csvBtn);
    toolbar.appendChild(excelBtn);
    container.appendChild(toolbar);
}

// Auto-inicializar toolbars en card-headers cuando la página cambia
document.addEventListener('DOMContentLoaded', function () {
    // Mapa de páginas a entidades exportables
    const pageEntityMap = {
        'page-personas': 'personas',
        'page-vehiculos': 'vehiculos',
        'page-alertas': 'alertas',
        'page-camaras': 'camaras',
    };

    Object.entries(pageEntityMap).forEach(([pageId, entity]) => {
        const page = document.getElementById(pageId);
        if (!page) return;

        // Buscar el card-header de la primera card
        const cardHeader = page.querySelector('.card-header');
        if (cardHeader) {
            createExportToolbar(entity, cardHeader);
        }
    });
});
