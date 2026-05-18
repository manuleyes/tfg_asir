/**
 * router.js - Enrutador con History API (sin hash)
 * Maneja navegación limpia entre páginas del dashboard
 */

class DashboardRouter {
    constructor() {
        this.currentPage = 'dashboard';
        this.pagePages = ['dashboard', 'camaras', 'detecciones', 'personas', 'vehiculos', 'alertas', 'bd', 'reportes', 'live-detection', 'diagnostico'];
        this.isInitialized = false;
        
        console.log('[Router] Creando instancia del router');
        
        // Inicializar
        this.init();
    }
    
    /**
     * Inicializar router
     */
    init() {
        if (this.isInitialized) {
            console.log('[Router] Ya está inicializado');
            return;
        }
        this.isInitialized = true;
        
        console.log('[Router] Iniciando...');
        
        // Detectar página actual desde URL
        this.detectCurrentPage();
        console.log('[Router] Página detectada:', this.currentPage);
        
        // Mostrar página actual
        this.showPage(this.currentPage);
        
        // Listeners para nav items
        this.setupNavItemListeners();
        
        // Listener para botón atrás/adelante del navegador
        window.addEventListener('popstate', () => {
            console.log('[Router] Evento popstate detectado');
            this.detectCurrentPage();
            this.showPage(this.currentPage);
        });
        
        console.log('[Router] Inicialización completada ✓');
    }
    
    /**
     * Detectar página actual desde pathname
     */
    detectCurrentPage() {
        const pathname = window.location.pathname;
        
        // Extraer el nombre de la página del pathname
        // /dashboard → dashboard
        // /camaras → camaras
        // etc.
        const match = pathname.match(/^\/([a-z-]+)\/?$/);
        
        if (match && this.pagePages.includes(match[1])) {
            this.currentPage = match[1];
        } else {
            this.currentPage = 'dashboard';
        }
        
        console.log('[Router] Página actual detectada:', this.currentPage);
    }
    
    /**
     * Mostrar página específica
     */
    showPage(pageName) {
        // Redirigir legacy routes al nuevo nombre
        if (pageName === 'personas' || pageName === 'vehiculos') pageName = 'detecciones';
        console.log('[Router] Mostrando página:', pageName);
        
        // Ocultar todas las páginas
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        // Detener polling de feeds si salimos de cámaras
        if (typeof camStopFeedPolling === 'function') camStopFeedPolling();
        // Detener polling de stats del servidor si salimos del dashboard
        if (typeof stopServerStatsPolling === 'function') stopServerStatsPolling();

        // Resetear scroll al tope para que el contenido aparezca arriba
        const contentEl = document.querySelector('.content');
        if (contentEl) contentEl.scrollTop = 0;
        
        // Mostrar página solicitada
        const pageElement = document.getElementById(`page-${pageName}`);
        if (pageElement) {
            pageElement.classList.add('active');
            console.log(`[Router] Página #page-${pageName} mostrada`);
        } else {
            console.warn(`[Router] No se encontró elemento #page-${pageName}`);
        }
        
        // Actualizar nav items activos
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`.nav-item[data-page="${pageName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
            console.log(`[Router] Nav item para ${pageName} marcado como activo`);
        }
        
        // Actualizar título de la página
        this.updatePageTitle(pageName);
        
        // Cargar datos específicos de la página
        this.loadPageData(pageName);
    }
    
    /**
     * Actualizar título de la página
     */
    updatePageTitle(pageName) {
        const titles = {
            'dashboard': 'Dashboard',
            'camaras': 'Cámaras',
            'detecciones': 'Detecciones',
            'personas': 'Detecciones',
            'vehiculos': 'Detecciones',
            'alertas': 'Alertas del Sistema',
            'bd': 'Base de Datos',
            'reportes': 'Reportes',
            'live-detection': 'Detección en Vivo',
            'diagnostico': 'Diagnóstico del Sistema'
        };
        
        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
            pageTitle.textContent = titles[pageName] || 'Dashboard';
        }
    }
    
    /**
     * Cargar datos específicos de la página
     */
    loadPageData(pageName) {
        switch(pageName) {
            case 'dashboard':
                // Arrancar polling de estadísticas del servidor
                if (typeof startServerStatsPolling === 'function') startServerStatsPolling();
                break;
            case 'camaras':
                if (typeof loadCameras === 'function') {
                    loadCameras();
                }
                break;
            case 'detecciones':
            case 'personas':   // legacy redirect
            case 'vehiculos':  // legacy redirect
                if (typeof loadDetecciones === 'function') {
                    loadDetecciones();
                }
                break;
            case 'alertas':
                if (typeof loadAlerts === 'function') {
                    loadAlerts();
                }
                break;
            case 'bd':
                // Auto-cargar tablas al entrar en BD
                if (typeof bdLoadTables === 'function') {
                    setTimeout(bdLoadTables, 100);
                }
                break;
            case 'reportes':
                // Reportes no requieren cargar datos automáticamente
                break;
            case 'live-detection':
                // Lazy-load iframe
                (function() {
                    const fr = document.getElementById('live-detection-frame');
                    if (fr && fr.dataset.src && fr.src !== fr.dataset.src && !fr.src.includes(fr.dataset.src.replace(/\.html$/, ''))) {
                        fr.src = fr.dataset.src;
                    }
                })();
                break;
            case 'diagnostico':
                // Lazy-load iframe
                (function() {
                    const fr = document.getElementById('diagnostico-frame');
                    if (fr && fr.dataset.src && fr.src !== fr.dataset.src && !fr.src.includes(fr.dataset.src.replace(/\.html$/, ''))) {
                        fr.src = fr.dataset.src;
                    }
                })();
                break;
        }
    }
    
    /**
     * Navegar a una página
     */
    navigate(pageName) {
        if (!this.pagePages.includes(pageName)) {
            pageName = 'dashboard';
        }
        
        console.log(`[Router] Navegando a: ${pageName}`);
        
        // Actualizar history
        window.history.pushState(
            { page: pageName },
            `${pageName} - Dashboard`,
            `/${pageName}`
        );
        
        // Mostrar página
        this.currentPage = pageName;
        this.showPage(pageName);
        
        console.log(`[Router] Navegación completada ✓`);
    }
    
    /**
     * Setup listeners para nav items con event delegation
     */
    setupNavItemListeners() {
        // Usar event delegation en el contenedor nav-menu
        const navMenu = document.querySelector('.nav-menu');
        if (!navMenu) {
            console.warn('[Router] .nav-menu no encontrado - reintentando en 500ms');
            setTimeout(() => this.setupNavItemListeners(), 500);
            return;
        }
        
        navMenu.addEventListener('click', (e) => {
            // Buscar el .nav-item más cercano
            const navItem = e.target.closest('.nav-item');
            if (navItem) {
                e.preventDefault();
                console.log('[Router] Click en nav-item detectado');
                
                const pageName = navItem.getAttribute('data-page');
                console.log('[Router] data-page:', pageName);
                
                if (pageName) {
                    this.navigate(pageName);
                    
                    // Cerrar sidebar si es mobile
                    const sidebar = document.querySelector('.sidebar');
                    if (sidebar && window.innerWidth < 768) {
                        sidebar.classList.remove('expanded');
                    }
                }
            }
        }, { passive: false });
        
        console.log('[Router] Event delegation configurado para .nav-menu ✓');
    }
}

// Inicializar router
function initializeRouter() {
    console.log('[Init] initializeRouter() llamado');
    
    if (window.dashboardRouter) {
        console.log('[Init] Router ya existe');
        return;
    }
    
    if (typeof DashboardRouter === 'undefined') {
        console.error('[Init] DashboardRouter class no está definida');
        return;
    }
    
    try {
        window.dashboardRouter = new DashboardRouter();
        console.log('[Init] ✓ Router inicializado exitosamente');
    } catch (error) {
        console.error('[Init] ✗ Error inicializando router:', error);
    }
}

// Marcar que router.js fue cargado
window.routerJsLoaded = true;
console.log('[Scripts] router.js cargado ✓');

// Detectar estado del documento e inicializar
if (document.readyState === 'loading') {
    console.log('[Init] Documento en estado "loading" - esperando DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[Init] DOMContentLoaded disparado');
        initializeRouter();
    });
} else {
    console.log('[Init] Documento ya en estado "' + document.readyState + '" - inicializando inmediatamente');
    initializeRouter();
}
