/**
 * utils.js - Funciones auxiliares
 */

/**
 * Obtener token JWT del localStorage
 */
function getToken() {
    return localStorage.getItem('token');
}

/**
 * Guardar token en localStorage
 */
function saveToken(token) {
    localStorage.setItem('token', token);
}

/**
 * Eliminar token
 */
function removeToken() {
    localStorage.removeItem('token');
}

/**
 * Obtener usuario del localStorage
 */
function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

/**
 * Guardar usuario en localStorage
 */
function saveUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

/**
 * Eliminar usuario
 */
function removeUser() {
    localStorage.removeItem('user');
}

/**
 * Verificar si hay sesión activa
 */
function isLoggedIn() {
    const token = getToken();
    return token !== null && token !== '';
}

/**
 * Redirigir a página
 */
function redirect(url) {
    window.location.href = url;
}

/**
 * Mostrar notificación
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

/**
 * Formatear fecha
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formatear hora relativa (ej: hace 5 minutos)
 */
function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    const useI18n = typeof i18n !== 'undefined';
    const lang = useI18n ? i18n.currentLanguage : 'es';

    function buildStr(value, unitKey) {
        const unit = useI18n ? i18n.t(unitKey) : unitKey;
        const ago  = useI18n ? i18n.t('hace')  : 'hace';
        if (lang === 'jp') return `${value}${unit}${ago}`;
        if (lang === 'en') return `${value} ${unit} ${ago}`;
        return `${ago} ${value} ${unit}`;
    }

    if (seconds < 60) {
        if (lang === 'jp') return 'たった今';
        if (lang === 'en') return 'Just now';
        return 'Hace unos segundos';
    }
    if (seconds < 3600) return buildStr(Math.floor(seconds / 60), 'minutos');
    if (seconds < 86400) return buildStr(Math.floor(seconds / 3600), 'horas');
    return formatDate(dateString);
}

/**
 * Crear elemento HTML
 */
function createElement(tag, className = '', innerHTML = '') {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (innerHTML) element.innerHTML = innerHTML;
    return element;
}

/**
 * Limpiar elemento
 */
function clearElement(element) {
    element.innerHTML = '';
}

/**
 * Adicionar clase CSS
 */
function addClass(element, className) {
    element.classList.add(className);
}

/**
 * Remover clase CSS
 */
function removeClass(element, className) {
    element.classList.remove(className);
}

/**
 * Toggle clase CSS
 */
function toggleClass(element, className) {
    element.classList.toggle(className);
}

/**
 * Validar email
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Exportar a CSV
 */
function downloadCSV(data, filename = 'data.csv') {
    let csv = '';
    if (Array.isArray(data) && data.length > 0) {
        // Headers
        csv = Object.keys(data[0]).join(',') + '\n';
        // Rows
        data.forEach(row => {
            csv += Object.values(row).map(v => `"${v}"`).join(',') + '\n';
        });
    }

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Exportar a JSON
 */
function downloadJSON(data, filename = 'data.json') {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}
