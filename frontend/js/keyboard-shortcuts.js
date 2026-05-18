// Keyboard Shortcuts Manager
class KeyboardShortcuts {
  static shortcuts = {
    'Ctrl+K': { description: 'Abrir búsqueda global', handler: 'openGlobalSearch' },
    'Ctrl+P': { description: 'Ir a perfil', handler: 'goToProfile' },
    'Ctrl+.': { description: 'Alternar tema', handler: 'toggleTheme' },
    'Ctrl+M': { description: 'Alternar menú sidebar', handler: 'toggleSidebar' },
    'Escape': { description: 'Cerrar diálogos', handler: 'closeDialogs' },
    '?': { description: 'Mostrar ayuda', handler: 'showHelp' }
  };

  static handlers = {
    openGlobalSearch() {
      document.getElementById('globalSearch')?.click() || alert('Búsqueda no disponible');
    },
    goToProfile() {
      window.location.href = '/perfil';
    },
    toggleTheme() {
      document.getElementById('darkModeToggle')?.click();
    },
    toggleSidebar() {
      document.querySelector('.sidebar')?.classList.toggle('compact');
    },
    closeDialogs() {
      document.querySelectorAll('.search-modal.open').forEach(m => m.classList.remove('open'));
      document.querySelectorAll('.dropdown:not(.hidden)').forEach(d => d.classList.add('hidden'));
    },
    showHelp() {
      this.displayShortcuts();
    }
  };

  static displayShortcuts() {
    let modal = document.getElementById('shortcuts-modal');
    
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'shortcuts-modal';
      modal.className = 'search-modal';
      document.body.appendChild(modal);
    }

    const html = `
      <div class="search-modal-content">
        <div class="search-input-wrapper">
          <h2 style="margin: 0 0 16px 0; color: var(--primary);">Atajos de Teclado (Keyboard Shortcuts)</h2>
        </div>
        <div class="shortcuts-display">
          <div class="shortcuts-grid">
            ${Object.entries(this.shortcuts).map(([keys, info]) => `
              <div class="shortcut-item">
                <div class="shortcut-keys">
                  ${keys.split('+').map(k => `<span class="key">${k}</span>`).join('')}
                </div>
                <div class="shortcut-description">${info.description}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    modal.innerHTML = html;
    modal.classList.add('open');

    // Close on click outside
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
      }
    });
  }

  static init() {
    document.addEventListener('keydown', (e) => {
      // Skip if in input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        if (e.key === 'Escape') {
          e.target.blur();
        }
        return;
      }

      const key = this.getKeyCombo(e);
      const shortcut = this.shortcuts[key];

      if (shortcut && this.handlers[shortcut.handler]) {
        e.preventDefault();
        this.handlers[shortcut.handler]();
      }

      // Help with ?
      if (e.key === '?') {
        e.preventDefault();
        this.handlers.showHelp();
      }
    });

    // Add chevron or hint to help
    console.log('%cPress ? for keyboard shortcuts', 'color: #4a90e2; font-weight: bold;');
  }

  static getKeyCombo(e) {
    const keys = [];
    if (e.ctrlKey) keys.push('Ctrl');
    if (e.altKey) keys.push('Alt');
    if (e.shiftKey) keys.push('Shift');
    
    if (e.key && e.key !== 'Control' && e.key !== 'Alt' && e.key !== 'Shift') {
      keys.push(e.key.length === 1 ? e.key.toUpperCase() : e.key);
    }

    return keys.join('+');
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    KeyboardShortcuts.init();
  });
} else {
  KeyboardShortcuts.init();
}

window.KeyboardShortcuts = KeyboardShortcuts;
