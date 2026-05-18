// Password Validator & Strength Checker
class PasswordValidator {
  static requirements = {
    minLength: { regex: /.{8,}/, text: 'Al menos 8 caracteres' },
    uppercase: { regex: /[A-Z]/, text: 'Una letra mayúscula' },
    lowercase: { regex: /[a-z]/, text: 'Una letra minúscula' },
    number: { regex: /\d/, text: 'Un número' },
    special: { regex: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/, text: 'Un carácter especial (!@#$%^&*)' }
  };

  static checkStrength(password) {
    let strength = 0;
    const met = {};

    Object.entries(this.requirements).forEach(([key, req]) => {
      met[key] = req.regex.test(password);
      if (met[key]) strength++;
    });

    return {
      score: strength,
      level: strength <= 1 ? 'weak' : strength <= 2 ? 'fair' : strength <= 3 ? 'good' : 'strong',
      met: met
    };
  }

  static updateUI(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    // Create or get strength visualization
    let strengthBar = input.parentElement.querySelector('.password-strength');
    let requirementsList = input.parentElement.querySelector('.password-requirements');

    if (!strengthBar) {
      strengthBar = document.createElement('div');
      strengthBar.className = 'password-strength';
      const bar = document.createElement('div');
      bar.className = 'password-strength-bar';
      strengthBar.appendChild(bar);
      input.parentElement.appendChild(strengthBar);
    }

    if (!requirementsList) {
      requirementsList = document.createElement('ul');
      requirementsList.className = 'password-requirements';
      input.parentElement.appendChild(requirementsList);
    }

    // Update on input
    input.addEventListener('input', () => {
      const password = input.value;
      const strength = this.checkStrength(password);

      // Update bar
      const bar = strengthBar.querySelector('.password-strength-bar');
      bar.className = `password-strength-bar password-strength-${strength.level}`;

      // Update requirements
      requirementsList.innerHTML = Object.entries(this.requirements)
        .map(([key, req]) => {
          const met = strength.met[key];
          return `<li class="password-requirement ${met ? 'met' : ''}">${req.text}</li>`;
        })
        .join('');
    });
  }

  static validate(password) {
    const strength = this.checkStrength(password);
    return strength.score >= 3; // Require "good" or "strong"
  }

  static getErrorMessage(password) {
    const strength = this.checkStrength(password);
    
    if (password.length === 0) {
      return 'La contraseña es requerida';
    }
    
    const missing = Object.entries(strength.met)
      .filter(([_, met]) => !met)
      .map(([key, _]) => this.requirements[key].text);

    if (missing.length > 0) {
      return 'La contraseña debe tener: ' + missing.join(', ');
    }

    return '';
  }
}

// Auto-initialize for password inputs
document.addEventListener('DOMContentLoaded', () => {
  const passwordInputs = document.querySelectorAll('input[type="password"]');
  passwordInputs.forEach(input => {
    if (!input.dataset.validatorInit) {
      PasswordValidator.updateUI(input.id || 'new-password');
      input.dataset.validatorInit = 'true';
    }
  });
});
