// Sidebar Toggle Manager
class SidebarToggle {
  static storageKey = 'sidebarCompacts';

  static init() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    const isCompact = localStorage.getItem(this.storageKey) === 'true';
    if (isCompact) {
      sidebar.classList.add('compact');
    }

    this.setupToggleButton();
  }

  static setupToggleButton() {
    // Check for existing toggle button
    let toggleBtn = document.getElementById('sidebarToggleBtn');
    if (!toggleBtn) {
      toggleBtn = document.createElement('button');
      toggleBtn.id = 'sidebarToggleBtn';
      toggleBtn.className = 'sidebar-toggle-btn';
      toggleBtn.title = 'Alternar menú (Ctrl+M)';
      toggleBtn.innerHTML = '≡';
      document.body.appendChild(toggleBtn);
    }

    toggleBtn.addEventListener('click', () => {
      this.toggle();
    });
  }

  static toggle() {
    const sidebar = document.querySelector('.sidebar');
    const app = document.querySelector('.app-container');

    if (!sidebar) return;

    const isCompact = sidebar.classList.toggle('compact');
    localStorage.setItem(this.storageKey, isCompact);

    // Close mobile menu if open
    if (window.innerWidth <= 992) {
      sidebar.classList.remove('open');
    }

    Toast.info(isCompact ? 'Menú compacto' : 'Menú expandido');
  }

  static makeResponsive() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');

    if (!sidebar || !toggleBtn) return;

    // Show toggle on mobile
    const mediaQuery = window.matchMedia('(max-width: 992px)');
    mediaQuery.addListener((e) => {
      if (e.matches) {
        if (!sidebar.classList.contains('compact')) {
          sidebar.classList.add('open');
        }
      }
    });

    // Close on link click (mobile)
    const links = sidebar.querySelectorAll('.nav-item');
    links.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 992) {
          sidebar.classList.remove('open');
        }
      });
    });
  }
}

// Initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    SidebarToggle.init();
    SidebarToggle.makeResponsive();
  });
} else {
  SidebarToggle.init();
  SidebarToggle.makeResponsive();
}

window.SidebarToggle = SidebarToggle;
