// Avatar Upload Manager
class AvatarManager {
  constructor() {
    this.storageKey = 'userAvatar';
    this.maxFileSize = 2 * 1024 * 1024; // 2MB
    this.allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    this.init();
  }

  init() {
    // Create upload section if it exists
    const form = document.getElementById('profileForm');
    if (!form) return;

    // Create avatar upload section
    const uploadSection = document.createElement('div');
    uploadSection.className = 'avatar-upload-section';
    uploadSection.innerHTML = `
      <label class="avatar-upload-label">Avatar Personalizado</label>
      <div class="avatar-preview-box">
        <div class="avatar-preview" id="avatarPreview">
          <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="30" r="15" fill="currentColor"/>
            <ellipse cx="50" cy="70" rx="25" ry="20" fill="currentColor"/>
          </svg>
        </div>
        <div class="avatar-upload-controls">
          <div class="file-input-wrapper">
            <input type="file" id="avatarInput" accept="image/jpeg,image/png,image/webp">
            <label for="avatarInput" class="file-input-label">Seleccionar Imagen</label>
          </div>
          <p class="avatar-hint">JPG, PNG o WebP. Máximo 2MB. Se recomienda cuadrado.</p>
        </div>
      </div>
    `;

    // Insert at the beginning of the form
    form.insertBefore(uploadSection, form.firstChild);

    // Setup handlers
    this.setupHandlers();
    this.loadAvatar();
  }

  setupHandlers() {
    const input = document.getElementById('avatarInput');
    if (!input) return;

    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        this.validateAndUpload(file);
      }
    });

    // Drag and drop
    const preview = document.getElementById('avatarPreview');
    if (preview) {
      preview.addEventListener('dragover', (e) => {
        e.preventDefault();
        preview.style.opacity = '0.7';
      });

      preview.addEventListener('dragleave', () => {
        preview.style.opacity = '1';
      });

      preview.addEventListener('drop', (e) => {
        e.preventDefault();
        preview.style.opacity = '1';
        const file = e.dataTransfer.files[0];
        if (file) {
          this.validateAndUpload(file);
        }
      });
    }
  }

  validateAndUpload(file) {
    // Validate type
    if (!this.allowedTypes.includes(file.type)) {
      Toast.error('Formato no permitido. Use JPG, PNG o WebP.');
      return;
    }

    // Validate size
    if (file.size > this.maxFileSize) {
      Toast.error('Archivo muy grande. Máximo 2MB.');
      return;
    }

    // Read and display
    const reader = new FileReader();
    reader.onload = (e) => {
      const imageData = e.target.result;
      this.setAvatar(imageData);
      Toast.success('Avatar actualizado');
    };
    reader.readAsDataURL(file);
  }

  setAvatar(imageData) {
    // Save to localStorage
    localStorage.setItem(this.storageKey, imageData);

    // Update profile header
    this.updatePreview(imageData);

    // Update user profile
    if (typeof userProfile !== 'undefined') {
      userProfile.updateProfile({ avatar: imageData });
    }
  }

  updatePreview(imageData) {
    const preview = document.getElementById('avatarPreview');
    const profileAvatar = document.querySelector('.profile-avatar');

    if (preview) {
      preview.innerHTML = `<img src="${imageData}" alt="Avatar">`;
    }

    if (profileAvatar) {
      profileAvatar.innerHTML = `<img src="${imageData}" alt="Avatar">`;
    }
  }

  loadAvatar() {
    const saved = localStorage.getItem(this.storageKey);
    if (saved) {
      this.updatePreview(saved);
    }
  }

  getAvatar() {
    return localStorage.getItem(this.storageKey);
  }

  removeAvatar() {
    localStorage.removeItem(this.storageKey);
    const preview = document.getElementById('avatarPreview');
    const profileAvatar = document.querySelector('.profile-avatar');

    if (preview) {
      preview.innerHTML = `
        <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="30" r="15" fill="currentColor"/>
          <ellipse cx="50" cy="70" rx="25" ry="20" fill="currentColor"/>
        </svg>
      `;
    }

    if (profileAvatar) {
      profileAvatar.innerHTML = `
        <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="30" r="15" fill="currentColor"/>
          <ellipse cx="50" cy="70" rx="25" ry="20" fill="currentColor"/>
        </svg>
      `;
    }

    Toast.info('Avatar eliminado');
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.avatarManager = new AvatarManager();
  });
} else {
  window.avatarManager = new AvatarManager();
}
