// Profile dropdown functionality
document.addEventListener('DOMContentLoaded', () => {
  const profileBtn = document.getElementById('profileBtn');
  const profileDropdown = document.getElementById('profileDropdown');
  const viewProfileBtn = document.getElementById('viewProfileBtn');
  const logoutBtn = document.getElementById('logoutBtn');

  if (!profileBtn || !profileDropdown) return;

  // Update profile header with user info
  function updateProfileHeader() {
    let profileHeader = profileDropdown.querySelector('.profile-header');
    if (!profileHeader) {
      profileHeader = document.createElement('div');
      profileHeader.className = 'profile-header';
      profileDropdown.insertBefore(profileHeader, profileDropdown.firstChild);
    }

    // Get user info from userProfile if available
    let fullName = 'Usuario Sistema';
    let role = 'Administrador';
    
    if (typeof userProfile !== 'undefined') {
      fullName = userProfile.getFullName();
      role = userProfile.profile.role;
    }

    profileHeader.innerHTML = `
      <div class="profile-info">
        <div class="profile-name">${fullName}</div>
        <div class="profile-role">${role}</div>
      </div>
    `;
  }

  // Toggle dropdown on button click
  profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    updateProfileHeader(); // Update before showing
    profileDropdown.classList.toggle('hidden');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!profileBtn.contains(e.target) && !profileDropdown.contains(e.target)) {
      profileDropdown.classList.add('hidden');
    }
  });

  // Handle profile button
  if (viewProfileBtn) {
    viewProfileBtn.addEventListener('click', () => {
      window.location.href = '/perfil';
      profileDropdown.classList.add('hidden');
    });
  }

  // Handle logout
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      console.log('Cerrar sesión clicked');
      // Implementar logout
      // window.location.href = '/logout';
    });
  }

  // Initial header update
  updateProfileHeader();
});
