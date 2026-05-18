/**
 * profile-page.js — Perfil de usuario conectado a la API real
 * Endpoints: GET /api/2fa/profile/me, PATCH /api/2fa/profile, PATCH /api/2fa/change-password
 */
document.addEventListener('DOMContentLoaded', async () => {

  // ── Helpers UI ─────────────────────────────────────────────────────────────
  function showAlert(msg, type = 'success') {
    const el = document.getElementById('profileAlert');
    if (!el) return;
    el.textContent = msg;
    el.className = type;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 4000);
  }

  // ── Guardar campo en backend ────────────────────────────────────────────────
  async function patchProfile(fields) {
    const res = await fetch('/api/2fa/profile', {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fields)
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Error al guardar');
    return d;
  }

  // ── Cargar perfil desde API ─────────────────────────────────────────────────
  async function loadProfile() {
    try {
      const res = await fetch('/api/2fa/profile/me', { credentials: 'include' });
      if (!res.ok) { showAlert('Error cargando perfil', 'error'); return; }
      const d = await res.json();

      const _t = (key, fallback) => (typeof translations !== 'undefined' && typeof currentLang !== 'undefined' && translations[currentLang]?.[key]) || fallback;
      const roleLabel = d.role === 'admin' ? _t('adminRole', 'Administrador') : d.role === 'operator' ? _t('operatorRole', 'Operador') : _t('viewerRole', 'Visualizador');

      // Nombre visible (localStorage como alias, username como base)
      const savedName = localStorage.getItem('displayName') || d.username;
      const nameEl = document.getElementById('infoDisplayName');
      if (nameEl) nameEl.textContent = savedName;

      const roleEl = document.getElementById('infoRole');
      if (roleEl) roleEl.textContent = roleLabel;

      const createdEl = document.getElementById('infoCreated');
      if (createdEl && d.created_at) {
        createdEl.textContent = new Date(d.created_at).toLocaleDateString('es-ES', { year:'numeric', month:'long', day:'numeric' });
      }

      const tfaEl = document.getElementById('info2fa');
      if (tfaEl) tfaEl.textContent = d.totp_enabled ? _t('twoFaActivo', 'Activo') : _t('twoFaInactivo', 'Inactivo');

      const userEl = document.getElementById('infoUsername');
      if (userEl) userEl.textContent = d.username;

      const emailDisplay = document.getElementById('infoEmailDisplay');
      if (emailDisplay) emailDisplay.textContent = d.email || _t('sinCorreo', '(sin correo)');

      const phoneDisplay = document.getElementById('infoPhoneDisplay');
      if (phoneDisplay) phoneDisplay.textContent = d.phone || _t('sinTelefono', '(sin teléfono)');

      // Prellenar inputs de edición
      const emailInput = document.getElementById('emailInput');
      if (emailInput) emailInput.value = d.email || '';

      const phoneInput = document.getElementById('phoneInput');
      if (phoneInput) phoneInput.value = d.phone || '';

    } catch { showAlert('Error de conexión', 'error'); }
  }

  // ── Editar nombre visible (localStorage) ──────────────────────────────────
  document.getElementById('saveNameBtn')?.addEventListener('click', () => {
    const input = document.getElementById('displayNameInput');
    const name  = input?.value.trim();
    if (!name) { showAlert('Escribe un nombre', 'error'); return; }
    localStorage.setItem('displayName', name);
    const nameEl = document.getElementById('infoDisplayName');
    if (nameEl) nameEl.textContent = name;
    const form = document.getElementById('editNameForm');
    if (form) form.style.display = 'none';
    showAlert('Nombre actualizado');
  });

  // Prellenar input de nombre al abrir el form
  document.getElementById('editNameBtn')?.addEventListener('click', () => {
    const input = document.getElementById('displayNameInput');
    if (input) input.value = document.getElementById('infoDisplayName')?.textContent || '';
  });

  // ── Guardar email ──────────────────────────────────────────────────────────
  document.getElementById('saveEmailBtn')?.addEventListener('click', async () => {
    const input = document.getElementById('emailInput');
    const email = input?.value.trim();
    if (!email) { showAlert('Escribe un email', 'error'); return; }
    try {
      await patchProfile({ email });
      const display = document.getElementById('infoEmailDisplay');
      if (display) display.textContent = email;
      const form = document.getElementById('editEmailForm');
      if (form) form.style.display = 'none';
      showAlert('Email actualizado');
    } catch (e) { showAlert(e.message, 'error'); }
  });

  // ── Guardar teléfono ───────────────────────────────────────────────────────
  document.getElementById('savePhoneBtn')?.addEventListener('click', async () => {
    const input = document.getElementById('phoneInput');
    const phone = input?.value.trim();
    if (!phone) { showAlert('Escribe un teléfono', 'error'); return; }
    try {
      await patchProfile({ phone });
      const display = document.getElementById('infoPhoneDisplay');
      if (display) display.textContent = phone;
      const form = document.getElementById('editPhoneForm');
      if (form) form.style.display = 'none';
      showAlert('Teléfono actualizado');
    } catch (e) { showAlert(e.message, 'error'); }
  });

  // ── Cambio de contraseña ───────────────────────────────────────────────────
  document.getElementById('passwordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const current = document.getElementById('currentPassword').value;
    const newPass  = document.getElementById('newPassword').value;
    const confirm  = document.getElementById('confirmPassword').value;

    if (!current || !newPass || !confirm) { showAlert('Completa todos los campos', 'error'); return; }
    if (newPass !== confirm) { showAlert('Las contraseñas nuevas no coinciden', 'error'); return; }
    if (newPass.length < 4)  { showAlert('Mínimo 4 caracteres', 'error'); return; }

    try {
      const res = await fetch('/api/2fa/change-password', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: current, new_password: newPass })
      });
      const d = await res.json();
      if (res.ok) { showAlert('Contraseña cambiada correctamente'); document.getElementById('passwordForm').reset(); }
      else { showAlert(d.detail || 'Error al cambiar contraseña', 'error'); }
    } catch { showAlert('Error de conexión', 'error'); }
  });

  // ── Logout / Perfil dropdown ───────────────────────────────────────────────
  document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    window.location.href = '/';
  });

  document.getElementById('profileBtn')?.addEventListener('click', () => {
    document.getElementById('profileDropdown')?.classList.toggle('hidden');
  });

  // ── Avatar (localStorage) ──────────────────────────────────────────────────
  function loadAvatar() {
    const saved = localStorage.getItem('profileAvatar');
    const img   = document.getElementById('avatarImg');
    const svg   = document.getElementById('avatarSvg');
    if (saved && img && svg) {
      img.src = saved;
      img.style.display = 'block';
      svg.style.display = 'none';
    }
  }

  function handleAvatarClick() {
    document.getElementById('avatarInput')?.click();
  }

  document.getElementById('avatarChangeBtn')?.addEventListener('click', handleAvatarClick);
  document.getElementById('profileAvatarEl')?.addEventListener('click', handleAvatarClick);

  document.getElementById('avatarInput')?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { showAlert('La imagen no puede superar 2 MB', 'error'); e.target.value = ''; return; }
    const reader = new FileReader();
    reader.onload = (ev) => {
      localStorage.setItem('profileAvatar', ev.target.result);
      loadAvatar();
      showAlert('Foto de perfil actualizada');
    };
    reader.readAsDataURL(file);
  });

  loadAvatar();
  await loadProfile();
});
