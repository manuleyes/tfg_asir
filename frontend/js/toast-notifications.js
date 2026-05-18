// Toast Notification System
class ToastNotification {
  static instances = [];

  constructor(message, type = 'info', duration = 3000) {
    this.message = message;
    this.type = type; // success, error, warning, info
    this.duration = duration;
    this.id = Date.now();
    this.show();
  }

  show() {
    const container = this.getContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${this.type}`;
    toast.id = `toast-${this.id}`;
    
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };

    toast.innerHTML = `
      <div class="toast-content">
        <span class="toast-icon">${icons[this.type]}</span>
        <span class="toast-message">${this.message}</span>
        <button class="toast-close">×</button>
      </div>
    `;

    container.appendChild(toast);
    ToastNotification.instances.push(this);

    toast.querySelector('.toast-close').addEventListener('click', () => {
      this.hide();
    });

    if (this.duration > 0) {
      setTimeout(() => this.hide(), this.duration);
    }

    requestAnimationFrame(() => {
      toast.classList.add('show');
    });
  }

  hide() {
    const toast = document.getElementById(`toast-${this.id}`);
    if (toast) {
      toast.classList.remove('show');
      setTimeout(() => {
        toast.remove();
        ToastNotification.instances = ToastNotification.instances.filter(t => t.id !== this.id);
      }, 300);
    }
  }

  static getContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  static success(message, duration) {
    return new ToastNotification(message, 'success', duration);
  }

  static error(message, duration) {
    return new ToastNotification(message, 'error', duration || 5000);
  }

  static warning(message, duration) {
    return new ToastNotification(message, 'warning', duration);
  }

  static info(message, duration) {
    return new ToastNotification(message, 'info', duration);
  }

  static clearAll() {
    ToastNotification.instances.forEach(t => t.hide());
    ToastNotification.instances = [];
  }
}

// Make globally available
window.Toast = ToastNotification;
