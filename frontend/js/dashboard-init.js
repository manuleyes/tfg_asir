/**
 * dashboard-init.js - Inicialización del dashboard
 */

console.log('[Dashboard] Script de inicialización cargado');

/**
 * Esperar a que router esté disponible
 */
async function waitForRouter() {
    return new Promise((resolve) => {
        if (window.dashboardRouter) {
            resolve();
            return;
        }
        
        let attempts = 0;
        const checkRouter = setInterval(() => {
            attempts++;
            if (window.dashboardRouter) {
                clearInterval(checkRouter);
                console.log('[Dashboard] Router detectado');
                resolve();
            }
            if (attempts > 50) { // 5 segundos
                clearInterval(checkRouter);
                console.warn('[Dashboard] Timeout esperando router');
                resolve();
            }
        }, 100);
    });
}

/**
 * Actualizar nombre de usuario en UI
 */
function updateUserName() {
    try {
        // Obtener nombre del usuario desde sessionStorage o localStorage
        const userName = sessionStorage.getItem('userName') || localStorage.getItem('userName') || 'Usuario';
        const userNameDropdown = document.getElementById('userNameDropdown');
        if (userNameDropdown) {
            userNameDropdown.textContent = userName;
            console.log('[Dashboard] Nombre de usuario actualizado:', userName);
        }
    } catch (error) {
        console.warn('[Dashboard] Error actualizando nombre de usuario:', error);
    }
}

/**
 * Inicializar dashboard
 */
async function initDashboard() {
    console.log('[Dashboard] Iniciando...');
    
    try {
        // Esperar router
        await waitForRouter();
        
        // Validar autenticación
        if (typeof requireAuth === 'function') {
            await requireAuth();
        }
        
        // Inicializar sesión UI
        if (typeof initSessionUI === 'function') {
            await initSessionUI();
        }
        
        // Actualizar nombre de usuario
        updateUserName();
        
        console.log('[Dashboard] Inicialización completada ✓');
    } catch (error) {
        console.error('[Dashboard] Error:', error);
    }
}

/**
 * Setup del botón logout
 */
function setupLogoutButton() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn && window.sessionManager) {
        logoutBtn.addEventListener('click', () => {
            console.log('[Dashboard] Logout clicked');
            window.sessionManager.logout();
        });
    }
}

// Iniciar cuando DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initDashboard();
        setupLogoutButton();
    });
} else {
    initDashboard();
    setupLogoutButton();
}
