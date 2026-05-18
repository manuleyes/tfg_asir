// Enhanced Dark Mode with Auto Theme & Preview
class ThemeManager {
  static themes = {
    light: 'light',
    dark: 'dark',
    auto: 'auto'
  };

  static storageKey = 'themeMode';

  static init() {
    let theme = localStorage.getItem(this.storageKey) || 'auto';
    this.setTheme(theme);
    this.setupHandlers();
  }

  static setTheme(theme) {
    if (!Object.values(this.themes).includes(theme)) {
      theme = 'auto';
    }

    localStorage.setItem(this.storageKey, theme);

    if (theme === 'auto') {
      this.applyAutoTheme();
    } else {
      this.applyTheme(theme === 'dark');
    }

    this.updateIcon();
    if (typeof ActivityHistory !== 'undefined') ActivityHistory.recordActivity('Tema actuali', theme);
  }

  static applyAutoTheme() {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.applyTheme(isDark);
  }

  static applyTheme(isDark) {
    if (isDark) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    this.updateIcon();
  }

  static updateIcon() {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;

    const theme = localStorage.getItem(this.storageKey) || 'auto';
    const isDark = document.body.classList.contains('dark-mode');

    // Icon shows next theme
    if (theme === 'auto') {
      icon.src = isDark ? '/static/img/sun.svg' : '/static/img/moon.svg';
    } else if (isDark) {
      icon.src = '/static/img/sun.svg';
    } else {
      icon.src = '/static/img/moon.svg';
    }
  }

  static previewTheme(theme) {
    if (theme === 'light') {
      document.body.classList.remove('dark-mode');
    } else if (theme === 'dark') {
      document.body.classList.add('dark-mode');
    }
    this.updateIcon();
  }

  static setupHandlers() {
    const themeBtn = document.getElementById('darkModeToggle');
    if (!themeBtn) return;

    themeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.cycleTheme();
    });

    // Detect system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      const theme = localStorage.getItem(this.storageKey);
      if (theme === 'auto') {
        this.applyAutoTheme();
      }
    });
  }

  static cycleTheme() {
    const current = localStorage.getItem(this.storageKey) || 'auto';
    const themes = ['auto', 'light', 'dark'];
    const currentIdx = themes.indexOf(current);
    const next = themes[(currentIdx + 1) % themes.length];
    this.setTheme(next);

    const messages = {
      light: 'Tema claro activado',
      dark: 'Tema oscuro activado',
      auto: 'Tema automático (sistema)'
    };
    if (typeof Toast !== 'undefined') Toast.info(messages[next]);
  }

  static getThemeOptions() {
    return [
      { value: 'light', label: 'Claro' },
      { value: 'dark', label: 'Oscuro' },
      { value: 'auto', label: 'Automático' }
    ];
  }
}

// Legacy functions for compatibility
let isDarkMode = false;
function initDarkMode() {
  ThemeManager.init();
}
function toggleDarkMode() {
  ThemeManager.cycleTheme();
}
function updateThemeIcon() {
  ThemeManager.updateIcon();
}

// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
  });
} else {
  ThemeManager.init();
}

window.ThemeManager = ThemeManager;
