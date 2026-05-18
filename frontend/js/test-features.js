/**
 * test-features.js - Prueba de funcionalidades nuevas
 * Abre la consola (F12) para ver los logs
 */

console.log('='.repeat(60));
console.log('PRUEBAS DE FUNCIONALIDADES');
console.log('='.repeat(60));

// Test 1: Verificar que i18n está cargado
console.log('\n✓ Test 1: Sistema de Idiomas');
if (typeof i18n !== 'undefined') {
    console.log('  ✓ i18n.js cargado');
    console.log('  ✓ Idioma actual:', i18n.currentLanguage);
    console.log('  ✓ Traducciones disponibles:', Object.keys(i18n.translations));
    
    // Probar translaciones
    console.log('\n  Ejemplos de traducciones:');
    console.log('  - Dashboard (ES):', i18n.translations.es.dashboard);
    console.log('  - Dashboard (EN):', i18n.translations.en.dashboard);
    console.log('  - Dashboard (JP):', i18n.translations.jp.dashboard);
} else {
    console.log('  ✗ i18n.js NO cargado');
}

// Test 2: Verificar que router está cargado
console.log('\n✓ Test 2: Sistema de Rutas');
if (typeof DashboardRouter !== 'undefined') {
    console.log('  ✓ DashboardRouter class definida');
} else {
    console.log('  ✗ DashboardRouter NO definida');
}

if (window.dashboardRouter) {
    console.log('  ✓ Router instancia activa');
    console.log('  ✓ Páginas disponibles:', window.dashboardRouter.pagePages);
} else {
    console.log('  ✗ Router instancia NO activa');
}

// Test 3: Verificar elementos en DOM
console.log('\n✓ Test 3: Elementos en DOM');
const languageSelector = document.getElementById('languageSelector');
const darkModeBtn = document.getElementById('darkModeToggle');
const remoteUrl = document.getElementById('remote-url');
const localUrl = document.getElementById('local-url');

console.log('  ✓ Language selector:', languageSelector ? 'FOUND' : 'NOT FOUND');
console.log('  ✓ Dark mode button:', darkModeBtn ? 'FOUND' : 'NOT FOUND');
console.log('  ✓ Remote IP element:', remoteUrl ? 'FOUND' : 'NOT FOUND');
console.log('  ✓ Local IP element:', localUrl ? 'FOUND' : 'NOT FOUND');

// Test 4: Cambiar idioma
console.log('\n✓ Test 4: Cambio de Idioma');
console.log('  Instrucciones:');
console.log('  1. Abre la consola (F12)');
console.log('  2. Cambia el idioma usando el selector en la esquina inferior izquierda');
console.log('  3. Verifica que los textos del menú cambian');
console.log('  4. Ejecuta: i18n.currentLanguage');

// Test 5: Testing dark mode
console.log('\n✓ Test 5: Modo Oscuro');
console.log('  Instrucciones:');
console.log('  1. Haz clic en el botón de la luna (arriba a la derecha)');
console.log('  2. Verifica que los colores cambien significativamente');
console.log('  3. El fondo debe ser mucho más oscuro (#0a1929)');
console.log('  4. Las cards deben tener bordes azules más visibles');

// Test 6: Testing IPs
console.log('\n✓ Test 6: Sistema de IPs');
console.log('  Cargando IPs del servidor...');
fetch('/api/server-ips')
    .then(r => r.json())
    .then(data => {
        console.log('  ✓ Respuesta del servidor:');
        console.log('    Local IP:', data.local_ip);
        console.log('    Public IP:', data.public_ip || 'No disponible');
        console.log('    Puerto:', data.port);
    })
    .catch(err => {
        console.log('  ✗ Error:', err.message);
    });

console.log('\n' + '='.repeat(60));
console.log('PRUEBAS COMPLETADAS');
console.log('='.repeat(60));
