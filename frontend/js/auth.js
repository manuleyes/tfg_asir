/**
 * auth.js - Autenticación minimal con cookies
 * FastAPI maneja todo: sesión, cookies, validación
 * Frontend solo: form submit → API login → redirige
 */

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        // Página de LOGIN
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const loginError = document.getElementById('loginError');
            const loginSuccess = document.getElementById('loginSuccess');
            
            if (!username || !password) {
                loginError.textContent = 'Por favor completa todos los campos';
                loginError.style.display = 'block';
                return;
            }
            
            try {
                // POST a /api/auth/login
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    credentials: 'include',  // Incluir cookies
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Login exitoso
                    loginSuccess.textContent = data.message;
                    loginSuccess.style.display = 'block';
                    loginError.style.display = 'none';
                    
                    // Redirigir a dashboard después de 1 segundo
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1000);
                } else {
                    // Error en login
                    loginError.textContent = data.detail || 'Error al iniciar sesión';
                    loginError.style.display = 'block';
                    loginSuccess.style.display = 'none';
                }
            } catch (error) {
                loginError.textContent = `Error: ${error.message}`;
                loginError.style.display = 'block';
                loginSuccess.style.display = 'none';
            }
        });
    }
    
    // Logout button (en dashboard/other pages)
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
            } catch (error) {
                console.error('Error en logout:', error);
            }
            // Redirigir a login
            window.location.href = '/';
        });
    }
});

/**
 * Cargar datos del dashboard
 */
async function loadDashboardData() {
    try {
        const data = await apiGetDashboard();
        console.log('Dashboard data:', data);
        
        // Actualizar widgets del dashboard
        const totalCameras = document.getElementById('totalCameras');
        const totalPersons = document.getElementById('totalPersons');
        const totalVehicles = document.getElementById('totalVehicles');
        const totalAlerts = document.getElementById('totalAlerts');
        
        if (totalCameras) totalCameras.textContent = data.total_cameras || 0;
        if (totalPersons) totalPersons.textContent = data.total_persons || 0;
        if (totalVehicles) totalVehicles.textContent = data.total_vehicles || 0;
        if (totalAlerts) totalAlerts.textContent = data.total_alerts || 0;
    } catch (error) {
        console.error('Error cargando dashboard:', error);
    }
}

/**
 * Mostrar error
 */
function showError(message, element) {
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

/**
 * Mostrar éxito
 */
function showSuccess(message, element) {
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}
