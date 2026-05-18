// JavaScript para Diagnóstico del Sistema

const tests = document.getElementById('tests');
const results = [];

function addTest(name, status = 'wait', details = '') {
    const testDiv = document.createElement('div');
    testDiv.className = `test ${status}`;
    testDiv.innerHTML = `
        <strong>${name}</strong>
        <span class="status ${status}">
            ${status === 'pass' ? '[OK]' : status === 'fail' ? '[FAIL]' : '[PENDING]'}
        </span>
        ${details ? `<div class="details">${details}</div>` : ''}
    `;
    tests.appendChild(testDiv);
    return testDiv;
}

// Test 1: Verificar que utils.js se cargó
const utilsTest = addTest('utils.js cargado', 'wait');
setTimeout(() => {
    if (typeof getToken === 'function' && typeof saveToken === 'function') {
        utilsTest.classList.remove('wait');
        utilsTest.classList.add('pass');
        utilsTest.innerHTML = `
            <strong>utils.js cargado</strong>
            <span class="status pass">[OK]</span>
            <div class="details">[OK] getToken() disponible<br>[OK] saveToken() disponible</div>
        `;
        results.push({ test: 'utils.js', status: 'pass' });
    } else {
        utilsTest.classList.remove('wait');
        utilsTest.classList.add('fail');
        utilsTest.innerHTML = `
            <strong>utils.js cargado</strong>
            <span class="status fail"></span>
            <div class="details"> getToken no disponible</div>
        `;
        results.push({ test: 'utils.js', status: 'fail' });
    }
}, 100);

// Test 2: Verificar que api.js se cargó
const apiTest = addTest('api.js cargado', 'wait');
setTimeout(() => {
    if (typeof apiLogin === 'function' && typeof apiRequest === 'function') {
        apiTest.classList.remove('wait');
        apiTest.classList.add('pass');
        apiTest.innerHTML = `
            <strong>api.js cargado</strong>
            <span class="status pass"></span>
            <div class="details"> apiLogin() disponible<br> apiRequest() disponible</div>
        `;
        results.push({ test: 'api.js', status: 'pass' });
    } else {
        apiTest.classList.remove('wait');
        apiTest.classList.add('fail');
        apiTest.innerHTML = `
            <strong>api.js cargado</strong>
            <span class="status fail"></span>
            <div class="details"> apiLogin no disponible<br>typeof apiLogin: ${typeof apiLogin}</div>
        `;
        results.push({ test: 'api.js', status: 'fail' });
    }
}, 200);

// Test 3: Verificar conexión a backend
const backendTest = addTest('Conexión al backend (localhost:16000)', 'wait');
fetch('/health')
    .then(response => response.json())
    .then(data => {
        backendTest.classList.remove('wait');
        backendTest.classList.add('pass');
        backendTest.innerHTML = `
            <strong>Conexión al backend (localhost:16000)</strong>
            <span class="status pass"></span>
            <div class="details">Status: ${data.status}</div>
        `;
        results.push({ test: 'Backend', status: 'pass' });
        
        // Si el backend está disponible, intentar login
        setTimeout(() => {
            testLogin();
        }, 500);
    })
    .catch(error => {
        backendTest.classList.remove('wait');
        backendTest.classList.add('fail');
        backendTest.innerHTML = `
            <strong>Conexión al backend (localhost:16000)</strong>
            <span class="status fail"></span>
            <div class="details">Error: ${error.message}</div>
        `;
        results.push({ test: 'Backend', status: 'fail' });
    });

// Test 4: Intentar login
function testLogin() {
    const loginTest = addTest('Prueba de login (admin/admin123)', 'wait');
    if (typeof apiLogin !== 'function') {
        loginTest.classList.remove('wait');
        loginTest.classList.add('fail');
        loginTest.innerHTML = `
            <strong>Prueba de login (admin/admin123)</strong>
            <span class="status fail"></span>
            <div class="details">apiLogin no está disponible</div>
        `;
        return;
    }

    apiLogin('admin', 'admin123')
        .then(response => {
            console.log('Login response:', response);
            if (response && response.access_token) {
                loginTest.classList.remove('wait');
                loginTest.classList.add('pass');
                loginTest.innerHTML = `
                    <strong>Prueba de login (admin/admin123)</strong>
                    <span class="status pass"></span>
                    <div class="details">
                        Token recibido: ${response.access_token.substring(0, 20)}...<br>
                        Username: ${response.username}<br>
                        <a href="dashboard.html" style="color: #4caf50; text-decoration: none;">→ Ir a Dashboard</a>
                    </div>
                `;
                saveToken(response.access_token);
                saveUser({ username: response.username, is_admin: response.is_admin });
            } else {
                loginTest.classList.remove('wait');
                loginTest.classList.add('fail');
                loginTest.innerHTML = `
                    <strong>Prueba de login (admin/admin123)</strong>
                    <span class="status fail"></span>
                    <div class="details">Respuesta inválida: ${JSON.stringify(response)}</div>
                `;
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            loginTest.classList.remove('wait');
            loginTest.classList.add('fail');
            loginTest.innerHTML = `
                <strong>Prueba de login (admin/admin123)</strong>
                <span class="status fail"></span>
                <div class="details">Error: ${error.message}</div>
            `;
        });
}
