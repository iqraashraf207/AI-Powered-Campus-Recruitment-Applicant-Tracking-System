const API = 'https://ai-powered-campus-recruitment-applicant-tracking-production.up.railway.app';


function saveUser(data) {
  localStorage.setItem('token',      data.access_token);
  localStorage.setItem('account_id', data.account_id);
  localStorage.setItem('name',       data.name);
  localStorage.setItem('role',       data.role);
}

function getToken()     { return localStorage.getItem('token'); }
function getRole()      { return localStorage.getItem('role'); }
function getAccountId() { return parseInt(localStorage.getItem('account_id')); }
function getName()      { return localStorage.getItem('name'); }


function logout() {
  localStorage.clear();
  window.location.href = '/index.html';
}


function authHeaders() {
  return {
    'Content-Type':  'application/json',
    'Authorization': 'Bearer ' + getToken()
  };
}

function requireLogin() {
  if (!getToken()) {
    window.location.href = '/index.html';
  }
}

function requireStudent() {
  requireLogin();
  if (getRole() !== 'student') {
    window.location.href = '/recruiter/dashboard.html';
  }
}

function requireRecruiter() {
  requireLogin();
  if (getRole() !== 'recruiter') {
    window.location.href = '/student/dashboard.html';
  }
}


function showAlert(id, message, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  el.className   = 'alert alert-' + type;
}

function setNavbarName() {
  const el = document.getElementById('navbar-name');
  if (el) el.textContent = getName();
}

function initModernMenu() {
  const navbars = document.querySelectorAll('.navbar');
  navbars.forEach(function(navbar) {
    const links = navbar.querySelector('.navbar-links');
    if (!links || navbar.querySelector('.menu-toggle')) return;

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'menu-toggle';
    toggle.setAttribute('aria-label', 'Toggle navigation menu');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.innerHTML = '<span></span><span></span><span></span>';

    const userSection = navbar.querySelector('.navbar-user');
    if (userSection) {
      navbar.insertBefore(toggle, userSection);
    } else {
      navbar.appendChild(toggle);
    }

    toggle.addEventListener('click', function() {
      const isOpen = navbar.classList.toggle('navbar-open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    links.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        navbar.classList.remove('navbar-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  });
}

async function loadCompanies() {
  try {
    const res  = await fetch(API + '/jobs/companies/all');
    const data = await res.json();
    const sel  = document.getElementById('company-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select your company</option>';
    data.forEach(function(c) {
      sel.innerHTML += '<option value="' + c.company_id + '">' + c.name + ' — ' + c.industry + '</option>';
    });
  } catch (err) {
    console.error('Could not load companies:', err);
  }
}

const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showAlert('alert', 'Please fill in all fields.', 'error');
      return;
    }

    try {
      const res  = await fetch(API + '/auth/login', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ email: email, password: password })
      });

      const data = await res.json();

      if (!res.ok) {
        showAlert('alert', data.detail || 'Login failed. Please check your credentials.', 'error');
        return;
      }

      saveUser(data);

      if (data.role === 'student') {
        window.location.href = '/student/dashboard.html';
      } else if (data.role === 'recruiter') {
        window.location.href = '/recruiter/dashboard.html';
      }

    } catch (err) {
      showAlert('alert', 'Could not connect to the server. Make sure the backend is running.', 'error');
    }
  });
}

const registerForm = document.getElementById('register-form');
if (registerForm) {

  const roleSelect = document.getElementById('role');
  if (roleSelect) {
    roleSelect.addEventListener('change', function() {
      const studentFields   = document.getElementById('student-fields');
      const recruiterFields = document.getElementById('recruiter-fields');

      if (this.value === 'student') {
        studentFields.style.display   = 'block';
        recruiterFields.style.display = 'none';
      } else if (this.value === 'recruiter') {
        studentFields.style.display   = 'none';
        recruiterFields.style.display = 'block';
        loadCompanies();
      } else {
        studentFields.style.display   = 'none';
        recruiterFields.style.display = 'none';
      }
    });
  }

  registerForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const role = document.getElementById('role').value;

    if (!role) {
      showAlert('alert', 'Please select a role.', 'error');
      return;
    }

    const body = {
      name:     document.getElementById('name').value.trim(),
      email:    document.getElementById('reg-email').value.trim(),
      password: document.getElementById('reg-password').value,
      role:     role
    };

    if (role === 'student') {
      body.cgpa            = parseFloat(document.getElementById('cgpa').value);
      body.major           = document.getElementById('major').value.trim();
      body.graduation_year = parseInt(document.getElementById('grad-year').value);

      if (!body.cgpa || !body.major || !body.graduation_year) {
        showAlert('alert', 'Please fill in all student details.', 'error');
        return;
      }
    }

    if (role === 'recruiter') {
      const companyId = document.getElementById('company-select').value;
      if (!companyId) {
        showAlert('alert', 'Please select your company.', 'error');
        return;
      }
      body.company_id = parseInt(companyId);
    }

    try {
      const res  = await fetch(API + '/auth/register', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body)
      });

      const data = await res.json();

      if (!res.ok) {
        showAlert('alert', data.detail || 'Registration failed. Please try again.', 'error');
        return;
      }

      showAlert('alert', 'Account created successfully! Redirecting to login...', 'success');
      setTimeout(function() {
        window.location.href = '/index.html';
      }, 1500);

    } catch (err) {
      showAlert('alert', 'Could not connect to the server. Make sure the backend is running.', 'error');
    }
  });
}

initModernMenu();