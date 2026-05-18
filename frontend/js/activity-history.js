// Activity History Manager
class ActivityHistory {
  static storageKey = 'userActivityHistory';
  static maxItems = 50;

  static recordActivity(action, details = '') {
    const history = this.getHistory();
    
    const activity = {
      timestamp: new Date().toISOString(),
      action: action,
      details: details,
      id: Date.now()
    };

    history.unshift(activity);
    history.splice(this.maxItems); // Keep only last 50

    localStorage.setItem(this.storageKey, JSON.stringify(history));
  }

  static getHistory() {
    const stored = localStorage.getItem(this.storageKey);
    return stored ? JSON.parse(stored) : [];
  }

  static getFormatted(activity) {
    const date = new Date(activity.timestamp);
    const time = date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
    
    return {
      action: activity.action,
      details: activity.details,
      time: time,
      date: date.toLocaleDateString('es-ES')
    };
  }

  static displayHistory(containerId = 'activityContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;

    const history = this.getHistory();
    
    if (history.length === 0) {
      container.innerHTML = '<p style="text-align: center; color: var(--text-light);">No hay actividad registrada</p>';
      return;
    }

    container.innerHTML = `
      <div class="activity-list">
        ${history.slice(0, 10).map(a => {
          const fmt = this.getFormatted(a);
          return `
            <div class="activity-item">
              <div class="activity-action">${fmt.action}</div>
              ${fmt.details ? `<div>${fmt.details}</div>` : ''}
              <div class="activity-time">${fmt.time} - ${fmt.date}</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  static clearHistory() {
    if (confirm('¿Está seguro de que desea borrar todo el historial?')) {
      localStorage.removeItem(this.storageKey);
      Toast.info('Historial borrado');
    }
  }
}

// Hook into common actions
document.addEventListener('DOMContentLoaded', () => {
  // Track profile updates
  const originalUpdateProfile = window.userProfile?.updateProfile;
  if (originalUpdateProfile) {
    window.userProfile.updateProfile = function(data) {
      const result = originalUpdateProfile.call(this, data);
      ActivityHistory.recordActivity('Perfil actualizado', Object.keys(data).join(', '));
      return result;
    };
  }

  // Track theme changes
  const themeBtn = document.getElementById('darkModeToggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const isDark = document.body.classList.contains('dark-mode');
      ActivityHistory.recordActivity('Tema cambiado', isDark ? 'Modo claro activado' : 'Modo oscuro activado');
    });
  }

  // Track language changes
  document.addEventListener('languageChanged', (e) => {
    ActivityHistory.recordActivity('Idioma cambiado', e.detail || 'Idioma actualizado');
  });
});

// Display activity in profile if section exists
document.addEventListener('DOMContentLoaded', () => {
  const hasActivitySection = document.querySelector('[data-i18n="historialActividad"]');
  if (hasActivitySection) {
    ActivityHistory.displayHistory();
  }
});

window.ActivityHistory = ActivityHistory;
