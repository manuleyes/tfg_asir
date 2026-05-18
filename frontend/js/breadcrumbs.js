// Breadcrumbs Manager
class Breadcrumbs {
  static pages = {
    '/dashboard': 'Dashboard',
    '/camaras': 'Cámaras',
    '/personas': 'Personas',
    '/vehiculos': 'Vehículos',
    '/alertas': 'Alertas',
    '/bd': 'Base de Datos',
    '/reportes': 'Reportes',
    '/live-detection': 'Detección en Vivo',
    '/diagnostico': 'Diagnóstico',
    '/perfil': 'Mi Perfil'
  };

  static init() {
    const topBarLeft = document.querySelector('.top-bar-left');
    if (!topBarLeft) return;

    // Create breadcrumbs container
    const breadcrumbs = document.createElement('div');
    breadcrumbs.className = 'breadcrumbs';
    breadcrumbs.id = 'breadcrumbsContainer';
    topBarLeft.appendChild(breadcrumbs);

    this.update();
    
    // Update on route change
    window.addEventListener('hashchange', () => this.update());
    window.addEventListener('popstate', () => this.update());
  }

  static update() {
    const container = document.getElementById('breadcrumbsContainer');
    if (!container) return;

    const path = window.location.pathname;
    const parts = [
      { path: '/dashboard', label: 'Dashboard' }
    ];

    // Add current page if not dashboard
    if (path !== '/dashboard' && this.pages[path]) {
      parts.push({ path: path, label: this.pages[path] });
    }

    container.innerHTML = parts.map((part, idx) => {
      const isLast = idx === parts.length - 1;
      return `
        <div class="breadcrumb-item">
          ${isLast 
            ? `<span>${part.label}</span>` 
            : `<a href="${part.path}">${part.label}</a>`
          }
        </div>
        ${!isLast ? '<span class="breadcrumb-separator">/</span>' : ''}
      `;
    }).join('');
  }
}

// Initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    Breadcrumbs.init();
  });
} else {
  Breadcrumbs.init();
}

window.Breadcrumbs = Breadcrumbs;
