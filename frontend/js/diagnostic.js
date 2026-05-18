/**
 * diagnostic.js - Diagnóstico completo del sistema de botones
 */

document.addEventListener('DOMContentLoaded', () => {
    console.clear();
    console.log('='.repeat(60));
    console.log('DIAGNOSTICO DEL SISTEMA DE BOTONES');
    console.log('='.repeat(60));
    
    const diagnostics = {
        elementos: {},
        scripts: {},
        css: {},
        imagenes: {},
        eventos: {}
    };
    
    // 1. VERIFICAR ELEMENTOS HTML
    console.log('\n1. VERIFICAR ELEMENTOS HTML');
    console.log('-'.repeat(60));
    
    const elementsToCheck = {
        languageBtn: document.getElementById('languageBtn'),
        darkModeToggle: document.getElementById('darkModeToggle'),
        profileBtn: document.getElementById('profileBtn'),
        languageDropdown: document.getElementById('languageDropdown'),
        profileDropdown: document.getElementById('profileDropdown'),
        langFlagDisplay: document.getElementById('langFlagDisplay'),
        themeIcon: document.getElementById('themeIcon'),
        topBarRight: document.querySelector('.top-bar-right'),
        topBarControl: document.querySelectorAll('.top-bar-control')
    };
    
    for (const [name, element] of Object.entries(elementsToCheck)) {
        const status = element ? '✓' : '✗';
        console.log(`${status} ${name}`);
        diagnostics.elementos[name] = !!element;
    }
    
    // 2. VERIFICAR SCRIPTS
    console.log('\n2. VERIFICAR SCRIPTS Y FUNCIONES');
    console.log('-'.repeat(60));
    
    const scriptsToCheck = {
        'i18n': typeof i18n !== 'undefined',
        'window.dashboardRouter': typeof window.dashboardRouter !== 'undefined',
        'window.sessionManager': typeof window.sessionManager !== 'undefined',
        'toggleDarkMode': typeof toggleDarkMode !== 'undefined',
        'copyToClipboard': typeof copyToClipboard !== 'undefined'
    };
    
    for (const [name, exists] of Object.entries(scriptsToCheck)) {
        const status = exists ? '✓' : '✗';
        console.log(`${status} ${name}`);
        diagnostics.scripts[name] = exists;
    }
    
    // 3. VERIFICAR ESTILOS CSS
    console.log('\n3. VERIFICAR ESTILOS CSS');
    console.log('-'.repeat(60));
    
    if (elementsToCheck.languageBtn) {
        const styles = window.getComputedStyle(elementsToCheck.languageBtn);
        console.log('languageBtn styles:');
        console.log(`  - width: ${styles.width}`);
        console.log(`  - height: ${styles.height}`);
        console.log(`  - border-radius: ${styles.borderRadius}`);
        console.log(`  - display: ${styles.display}`);
        console.log(`  - cursor: ${styles.cursor}`);
        diagnostics.css.languageBtn = {
            width: styles.width,
            height: styles.height,
            cursor: styles.cursor
        };
    }
    
    if (elementsToCheck.topBarRight) {
        const styles = window.getComputedStyle(elementsToCheck.topBarRight);
        console.log('topBarRight styles:');
        console.log(`  - display: ${styles.display}`);
        console.log(`  - gap: ${styles.gap}`);
        console.log(`  - justify-content: ${styles.justifyContent}`);
        console.log(`  - align-items: ${styles.alignItems}`);
        diagnostics.css.topBarRight = {
            display: styles.display,
            gap: styles.gap
        };
    }
    
    // 4. VERIFICAR IMÁGENES
    console.log('\n4. VERIFICAR IMAGENES');
    console.log('-'.repeat(60));
    
    if (elementsToCheck.langFlagDisplay) {
        console.log(`langFlagDisplay src: ${elementsToCheck.langFlagDisplay.src}`);
        console.log(`langFlagDisplay width: ${elementsToCheck.langFlagDisplay.width}`);
        console.log(`langFlagDisplay height: ${elementsToCheck.langFlagDisplay.height}`);
        diagnostics.imagenes.langFlagDisplay = elementsToCheck.langFlagDisplay.src;
    }
    
    if (elementsToCheck.themeIcon) {
        console.log(`themeIcon src: ${elementsToCheck.themeIcon.src}`);
        console.log(`themeIcon width: ${elementsToCheck.themeIcon.width}`);
        console.log(`themeIcon height: ${elementsToCheck.themeIcon.height}`);
        diagnostics.imagenes.themeIcon = elementsToCheck.themeIcon.src;
    }
    
    // 5. VERIFICAR EVENT LISTENERS
    console.log('\n5. PROBAR EVENTOS');
    console.log('-'.repeat(60));
    
    if (elementsToCheck.languageBtn) {
        elementsToCheck.languageBtn.addEventListener('click', () => {
            const isActive = elementsToCheck.languageDropdown?.classList.contains('active');
            console.log('[EVENT] languageBtn clicked - dropdown active:', isActive);
        }, { once: true });
        console.log('✓ Event listener agregado a languageBtn (próximo click se registrará)');
    }
    
    if (elementsToCheck.darkModeToggle) {
        elementsToCheck.darkModeToggle.addEventListener('click', () => {
            const isDark = document.body.classList.contains('dark-mode');
            console.log('[EVENT] darkModeToggle clicked - dark mode:', isDark);
        }, { once: true });
        console.log('✓ Event listener agregado a darkModeToggle (próximo click se registrará)');
    }
    
    if (elementsToCheck.profileBtn) {
        elementsToCheck.profileBtn.addEventListener('click', () => {
            const isActive = elementsToCheck.profileDropdown?.classList.contains('active');
            console.log('[EVENT] profileBtn clicked - dropdown active:', isActive);
        }, { once: true });
        console.log('✓ Event listener agregado a profileBtn (próximo click se registrará)');
    }
    
    // 6. RESUMEN
    console.log('\n' + '='.repeat(60));
    console.log('RESUMEN DEL DIAGNOSTICO');
    console.log('='.repeat(60));
    
    const allElementsOk = Object.values(diagnostics.elementos).every(v => v === true);
    const allScriptsOk = Object.values(diagnostics.scripts).every(v => v === true);
    
    console.log(`Elementos: ${allElementsOk ? '✓ OK' : '✗ FALTAN'}`);
    console.log(`Scripts: ${allScriptsOk ? '✓ OK' : '✗ FALTAN'}`);
    console.log(`\nInstrucciones: Haz clic en los 3 botones y verifica el console para ver los eventos`);
    console.log('='.repeat(60));
    
    // Exportar diagnósticos a una variable global para inspeccionar
    window.buttonDiagnostics = diagnostics;
    console.log('\nPuedes ver todos los detalles en: window.buttonDiagnostics');
});
