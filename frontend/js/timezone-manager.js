// Timezone Manager
class TimezoneManager {
  static storageKey = 'userTimezone';

  static getTimezones() {
    return [
      'UTC',
      'America/New_York',
      'America/Chicago',
      'America/Denver',
      'America/Los_Angeles',
      'Europe/London',
      'Europe/Paris',
      'Europe/Madrid',
      'Europe/Berlin',
      'Europe/Moscow',
      'Asia/Dubai',
      'Asia/Kolkata',
      'Asia/Bangkok',
      'Asia/Singapore',
      'Asia/Tokyo',
      'Australia/Sydney',
      'Pacific/Auckland'
    ];
  }

  static init() {
    const savedTz = localStorage.getItem(this.storageKey) || this.getSystemTimezone();
    this.currentTimezone = savedTz;
    localStorage.setItem(this.storageKey, savedTz);
  }

  static getSystemTimezone() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  }

  static getCurrentTimezone() {
    return localStorage.getItem(this.storageKey) || this.getSystemTimezone();
  }

  static setTimezone(tz) {
    if (this.getTimezones().includes(tz)) {
      this.currentTimezone = tz;
      localStorage.setItem(this.storageKey, tz);
      this.updateDisplay();
      Toast.success(`Zona horaria: ${tz}`);
      ActivityHistory.recordActivity('Zona horaria actualizada', tz);
    }
  }

  static formatTime(date) {
    const tz = this.getCurrentTimezone();
    if (tz === 'UTC') {
      return date.toUTCString();
    }
    return date.toLocaleString('es-ES', { timeZone: tz });
  }

  static createSelector() {
    const container =  document.querySelector('.info-card:last-child');
    if (!container) return;

    const selector = document.createElement('div');
    selector.className = 'timezone-selector';
    selector.innerHTML = `
      <select class="timezone-select" id="timezoneSelect">
        ${this.getTimezones().map(tz => `
          <option value="${tz}" ${tz === this.getCurrentTimezone() ? 'selected' : ''}>${tz}</option>
        `).join('')}
      </select>
      <div class="timezone-display" id="timezoneDisplay">${this.getCurrentTimezone()}</div>
    `;

    const timezoneSection = container.querySelector('p:last-of-type');
    if (timezoneSection) {
      timezoneSection.innerHTML = 'Zona Horaria: ' + this.getCurrentTimezone();
      timezoneSection.appendChild(selector);
    }

    document.getElementById('timezoneSelect')?.addEventListener('change', (e) => {
      this.setTimezone(e.target.value);
    });
  }

  static updateDisplay() {
    const display = document.getElementById('timezoneDisplay');
    if (display) {
      display.textContent = this.getCurrentTimezone();
    }
  }
}

// Initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    TimezoneManager.init();
  });
} else {
  TimezoneManager.init();
}

window.TimezoneManager = TimezoneManager;
