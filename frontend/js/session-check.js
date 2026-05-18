/**
 * session-check.js - Verificación de sesión y redirección automática
 * Carga esta librería en todas las páginas protegidas para verificar autenticación
 */

class SessionManager {
    constructor() {
        this.apiBaseUrl = '';
        this.checkEndpoint = '/api/auth/check-session';
        this.loginPage = '/';  // Redirecciona a raíz para login
    }

    /**
     * Verificar si el usuario tiene sesión válida
     * @returns {Promise<Object>} Datos de sesión o null
     */
    async checkSession() {
        try {
            const response = await fetch(`${this.apiBaseUrl}${this.checkEndpoint}`, {
                method: 'GET',
                credentials: 'include', // Incluir cookies
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                console.warn('Session check failed:', response.status);
                return null;
            }

            const data = await response.json();

            if (data.authenticated) {
                console.log(' Session valid for user:', data.username);
                return data;
            } else {
                console.warn('No authenticated session found');
                return null;
            }
        } catch (error) {
            console.error('Error checking session:', error);
            return null;
        }
    }

    /**
     * Verificar sesión y redirigir a login si no existe
     * @param {boolean} autoRedirect - Si true, redirige automáticamente al login
     * @returns {Promise<boolean>} True si sesión es válida
     */
    async validateAndRedirect(autoRedirect = true) {
        const session = await this.checkSession();

        if (!session) {
            console.warn('No valid session - redirecting to login');
            if (autoRedirect) {
                // Redirigir al login con un pequeño delay
                setTimeout(() => {
                    window.location.href = this.loginPage;
                }, 500);
            }
            return false;
        }

        return true;
    }

    /**
     * Obtener datos del usuario autenticado
     * @returns {Promise<Object|null>}
     */
    async getCurrentUser() {
        const session = await this.checkSession();
        if (session && session.authenticated) {
            return {
                userId: session.user_id,
                username: session.username,
                isAdmin: session.is_admin
            };
        }
        return null;
    }

    /**
     * Logout - cerrar sesión
     * @returns {Promise<boolean>}
     */
    async logout() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/logout`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                console.log(' Logout successful');
                window.location.href = this.loginPage;
                return true;
            }
        } catch (error) {
            console.error('Error logging out:', error);
        }
        return false;
    }
}

// Crear instancia global
const sessionManager = new SessionManager();

/**
 * Verificar sesión cuando se carga la página
 * Llamar en el HTML: <script>requireAuth();</script>
 */
async function requireAuth() {
    const isValid = await sessionManager.validateAndRedirect(true);
    return isValid;
}

/**
 * Obtener usuario actual y mostrar información
 * Llamar en el HTML después que se carga body
 */
async function initSessionUI() {
    const user = await sessionManager.getCurrentUser();

    if (user) {
        // Mostrar información del usuario si existe elemento con id "user-info"
        const userInfoEl = document.getElementById('user-info');
        if (userInfoEl) {
            userInfoEl.innerHTML = `
                <span class="user-name">${user.username}</span>
                ${user.isAdmin ? '<span class="badge-admin">Admin</span>' : ''}
            `;
        }

        // Agregar listener a botón de logout si existe
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                sessionManager.logout();
            });
        }

        return user;
    }

    return null;
}

// Auto-check de sesión si el script se carga en una página protegida
// Comentar esta línea si quieres control manual
// requireAuth();

console.log(' session-check.js loaded');
