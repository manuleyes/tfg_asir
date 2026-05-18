// Global Search Manager
class GlobalSearch {
  static pages = [
    { title: 'Dashboard', path: '/dashboard', keywords: ['dashboard', 'inicio', 'panel'] },
    { title: 'Cámaras', path: '/camaras', keywords: ['camaras', 'cámaras', 'videocamara'] },
    { title: 'Personas', path: '/personas', keywords: ['personas', 'gente', 'usuarios'] },
    { title: 'Vehículos', path: '/vehiculos', keywords: ['vehiculos', 'vehículos', 'coches', 'autos'] },
    { title: 'Alertas', path: '/alertas', keywords: ['alertas', 'notificaciones', 'alarmas'] },
    { title: 'Base de Datos', path: '/bd', keywords: ['base datos', 'bd', 'datos', 'almacenamiento'] },
    { title: 'Reportes', path: '/reportes', keywords: ['reportes', 'reports', 'informes'] },
    { title: 'Detección en Vivo', path: '/live-detection', keywords: ['deteccion', 'vivo', 'tiempo real'] },
    { title: 'Diagnóstico', path: '/diagnostico', keywords: ['diagnostico', 'estado', 'status'] },
    { title: 'Mi Perfil', path: '/perfil', keywords: ['perfil', 'usuario', 'cuenta', 'configuracion'] }
  ];

  static init() {
    // Add search box to top bar if it doesn't exist
    const topBarRight = document.querySelector('.top-bar-right');
    if (!topBarRight) return;

    // Create search modal
    const modal = document.createElement('div');
    modal.id = 'globalSearchModal';
    modal.className = 'search-modal';
    modal.innerHTML = `
      <div class="search-modal-content">
        <div class="search-input-wrapper">
          <input type="text" class="search-input" id="globalSearchInput" placeholder="Buscar páginas, acciones... (Ctrl+K)">
        </div>
        <div class="search-results" id="searchResults">
          <div class="search-hint">Escribe para buscar</div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    // Setup handlers
    this.setupHandlers(modal);
  }

  static setupHandlers(modal) {
    const input = modal.querySelector('#globalSearchInput');
    const resultsDiv = modal.querySelector('#searchResults');
    let timeout;

    // Open modal with Ctrl+K
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        modal.classList.add('open');
        input.focus();
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('open')) {
        modal.classList.remove('open');
      }
    });

    // Search on input
    input.addEventListener('input', (e) => {
      clearTimeout(timeout);
      const query = e.target.value.toLowerCase();

      if (!query) {
        resultsDiv.innerHTML = '<div class="search-hint">Escribe para buscar</div>';
        return;
      }

      timeout = setTimeout(() => {
        this.search(query, resultsDiv, modal);
      }, 200);
    });

    // Close when clicking outside
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
      }
    });

    // Navigate on arrow keys
    input.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        const items = resultsDiv.querySelectorAll('.search-result-item');
        if (items.length === 0) return;

        const current = resultsDiv.querySelector('.search-result-item:focus');
        if (!current) {
          items[0].focus();
        } else {
          const next = e.key === 'ArrowDown' ? current.nextElementSibling : current.previousElementSibling;
          if (next) next.focus();
        }
      }

      if (e.key === 'Enter') {
        const current = resultsDiv.querySelector('.search-result-item:focus');
        if (current) current.click();
      }
    });
  }

  static search(query, resultsDiv, modal) {
    const results = this.pages.filter(page => {
      const searchText = `${page.title} ${page.keywords.join(' '.toLowerCase())}`;
      return searchText.includes(query);
    });

    if (results.length === 0) {
      resultsDiv.innerHTML = `<div class="search-hint">No se encontraron resultados para "${query}"</div>`;
      return;
    }

    resultsDiv.innerHTML = results.map(page => `
      <button class="search-result-item" onclick="window.location.href='${page.path}'; document.getElementById('globalSearchModal').classList.remove('open');">
        <strong>${page.title}</strong>
      </button>
    `).join('');
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    GlobalSearch.init();
  });
} else {
  GlobalSearch.init();
}

window.GlobalSearch = GlobalSearch;
