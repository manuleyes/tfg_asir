/**
 * test-buttons.js - Prueba que los 3 botones funcionen correctamente
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('=== TEST BUTTONS ===');
    
    // Verificar que los elementos existan
    const languageBtn = document.getElementById('languageBtn');
    const darkModeToggle = document.getElementById('darkModeToggle');
    const profileBtn = document.getElementById('profileBtn');
    
    const languageDropdown = document.getElementById('languageDropdown');
    const profileDropdown = document.getElementById('profileDropdown');
    
    console.log('[TEST] languageBtn:', languageBtn ? '✓' : '✗');
    console.log('[TEST] darkModeToggle:', darkModeToggle ? '✓' : '✗');
    console.log('[TEST] profileBtn:', profileBtn ? '✓' : '✗');
    console.log('[TEST] languageDropdown:', languageDropdown ? '✓' : '✗');
    console.log('[TEST] profileDropdown:', profileDropdown ? '✓' : '✗');
    
    // Verificar que los scripts necesarios existan
    console.log('[TEST] i18n:', typeof i18n !== 'undefined' ? '✓' : '✗');
    console.log('[TEST] window.sessionManager:', typeof window.sessionManager !== 'undefined' ? '✓' : '✗');
    
    // Probar click del botón de idioma
    if (languageBtn) {
        languageBtn.addEventListener('click', () => {
            console.log('[TEST-CLICK] Botón idioma clickeado');
            console.log('[TEST-CLICK] Dropdown activo:', languageDropdown?.classList.contains('active'));
        });
    }
    
    // Probar click del botón de tema
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            console.log('[TEST-CLICK] Botón tema clickeado');
            console.log('[TEST-CLICK] Dark mode:', document.body.classList.contains('dark-mode'));
        });
    }
    
    // Probar click del botón de perfil
    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            console.log('[TEST-CLICK] Botón perfil clickeado');
            console.log('[TEST-CLICK] Dropdown activo:', profileDropdown?.classList.contains('active'));
        });
    }
    
    console.log('[TEST] Tests completados - Abre la consola (F12) para ver los resultados');
});
