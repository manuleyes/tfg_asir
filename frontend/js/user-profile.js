// User Profile Management
class UserProfile {
  constructor() {
    this.storageKey = 'userProfile';
    this.defaultProfile = {
      firstName: 'Usuario',
      lastName: 'Sistema',
      email: 'usuario@sistema.local',
      phone: '+34 600 000 000',
      department: 'Seguridad',
      role: 'Administrador'
    };
    this.loadProfile();
  }

  loadProfile() {
    const stored = localStorage.getItem(this.storageKey);
    if (stored) {
      this.profile = JSON.parse(stored);
    } else {
      this.profile = { ...this.defaultProfile };
      this.saveProfile();
    }
  }

  saveProfile() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.profile));
  }

  getFullName() {
    return `${this.profile.firstName} ${this.profile.lastName}`;
  }

  getProfile() {
    return { ...this.profile };
  }

  updateProfile(data) {
    this.profile = { ...this.profile, ...data };
    this.saveProfile();
    return this.profile;
  }

  getFirstName() {
    return this.profile.firstName;
  }
}

// Create global instance
const userProfile = new UserProfile();

// Update profile display in dropdown
function updateProfileDisplay() {
  const profileDropdown = document.getElementById('profileDropdown');
  if (!profileDropdown) return;

  // Check if profile header already exists
  let profileHeader = profileDropdown.querySelector('.profile-header');
  if (!profileHeader) {
    profileHeader = document.createElement('div');
    profileHeader.className = 'profile-header';
    profileDropdown.insertBefore(profileHeader, profileDropdown.firstChild);
  }

  // Update the header with user info
  profileHeader.innerHTML = `
    <div class="profile-info">
      <div class="profile-name">${userProfile.getFullName()}</div>
      <div class="profile-role">${userProfile.profile.role}</div>
    </div>
  `;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  updateProfileDisplay();
});
