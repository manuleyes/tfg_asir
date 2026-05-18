/**
 * language-switcher.js - Control de cambio de idioma
 */

// Ejecutar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Language] Inicializando selector de idiomas...');
    
    // Configurar botón de idiomas dropdown
    const languageBtn = document.getElementById('languageBtn');
    const languageDropdown = document.getElementById('languageDropdown');
    const langFlagDisplay = document.getElementById('langFlagDisplay');
    
    if (languageBtn && languageDropdown) {
        // Toggle dropdown
        languageBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = languageDropdown.classList.contains('active');
            if (isActive) {
                languageDropdown.classList.remove('active');
            } else {
                languageDropdown.classList.add('active');
                // Cerrar otros dropdowns
                document.getElementById('profileDropdown')?.classList.remove('active');
            }
        });
        
        // Opciones de idioma
        languageDropdown.querySelectorAll('.lang-flag-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const lang = btn.getAttribute('data-lang');
                console.log(`[Language] Cambiando a: ${lang}`);
                
                // Cambiar idioma
                i18n.setLanguage(lang);
                
                // Actualizar bandera en botón
                const flags = { es: '/static/img/es.svg', en: '/static/img/uk.svg', jp: '/static/img/jp.svg' };
                if (langFlagDisplay) {
                    langFlagDisplay.src = flags[lang];
                }
                
                // Cerrar dropdown
                languageDropdown.classList.remove('active');
            });
        });
        
        // Establecer bandera inicial
        const flags = { es: '/static/img/es.svg', en: '/static/img/uk.svg', jp: '/static/img/jp.svg' };
        if (langFlagDisplay) {
            langFlagDisplay.src = flags[i18n.currentLanguage] || '/static/img/es.svg';
        }
        
        console.log('[Language] Selector de idiomas configurado ✓');
    } else {
        console.warn('[Language] Elementos no encontrados');
    }
    
    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.top-bar-control')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
});

// Escuchar cambios de idioma
window.addEventListener('languageChanged', (e) => {
    console.log(`[Language] Idioma cambiado a: ${e.detail.language}`);
    const flags = { es: '/static/img/es.svg', en: '/static/img/uk.svg', jp: '/static/img/jp.svg' };
    const langFlagDisplay = document.getElementById('langFlagDisplay');
    if (langFlagDisplay) {
        langFlagDisplay.src = flags[e.detail.language] || '/static/img/es.svg';
    }
});
