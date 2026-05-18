/**
 * api.js - Llamadas a la API Backend
 */

// Usa el mismo origen desde donde se sirve el frontend (funciona en local, LAN e internet)
const API_BASE_URL = window.location.origin;

/**
 * Realizar petición HTTP genérica
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json',
    };

    // Agregar token si existe
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers,
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        // Si 401 o 403, redirigir a login
        if (response.status === 401 || response.status === 403) {
            removeToken();
            removeUser();
            redirect('index.html');
            return null;
        }

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || result.error || 'Error en la petición');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Login - POST /api/auth/login
 */
async function apiLogin(username, password) {
    return apiRequest('/api/auth/login', 'POST', {
        username,
        password,
    });
}

/**
 * Register - POST /api/auth/register
 */
async function apiRegister(username, password, email) {
    return apiRequest('/api/auth/register', 'POST', {
        username,
        password,
        email,
    });
}

/**
 * Obtener dashboard info - GET /api/dashboard
 */
async function apiGetDashboard() {
    return apiRequest('/api/dashboard', 'GET');
}

/**
 * Obtener lista de cámaras - GET /api/camaras
 */
async function apiGetCameras() {
    return apiRequest('/api/camaras', 'GET');
}

/**
 * Crear cámara - POST /api/camaras
 */
async function apiCreateCamera(data) {
    return apiRequest('/api/camaras', 'POST', data);
}

/**
 * Eliminar cámara - DELETE /api/camaras/{id}
 */
async function apiDeleteCamera(id) {
    return apiRequest(`/api/camaras/${id}`, 'DELETE');
}

/**
 * Obtener personas - GET /api/personas
 */
async function apiGetPersons(limit = 100, offset = 0) {
    return apiRequest(`/api/personas?limit=${limit}&offset=${offset}`, 'GET');
}

/**
 * Buscar personas - GET /api/personas/search?q=query
 */
async function apiSearchPersons(query) {
    return apiRequest(`/api/personas/search?q=${encodeURIComponent(query)}`, 'GET');
}

/**
 * Obtener vehículos - GET /api/vehiculos
 */
async function apiGetVehicles(limit = 100, offset = 0) {
    return apiRequest(`/api/vehiculos?limit=${limit}&offset=${offset}`, 'GET');
}

/**
 * Buscar vehículos - GET /api/vehiculos/search?q=query
 */
async function apiSearchVehicles(query) {
    return apiRequest(`/api/vehiculos/search?q=${encodeURIComponent(query)}`, 'GET');
}

/**
 * Obtener alertas - GET /api/alertas
 */
async function apiGetAlerts(filter = null) {
    let endpoint = '/api/alertas';
    if (filter) {
        endpoint += `?severity=${filter}`;
    }
    return apiRequest(endpoint, 'GET');
}

/**
 * Ejecutar query en BD - POST /api/bd/query
 */
async function apiExecuteQuery(sqlQuery) {
    return apiRequest('/api/bd/query', 'POST', {
        query: sqlQuery,
    });
}

/**
 * Logout - POST /api/auth/logout
 */
async function apiLogout() {
    return apiRequest('/api/auth/logout', 'POST');
}
