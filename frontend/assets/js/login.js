import { toast } from './core/ui.js';

function setSession({ id, role }) {
  localStorage.setItem('userId', String(id ?? ''));
  localStorage.setItem('userRole', role ?? 'vendedor');
}

const USERS = {
  // usuario : { pass, role, id }
  admin:     { pass: '1234', role: 'admin',     id: 1 },
  vendedor1: { pass: '1234', role: 'vendedor',  id: 18 },
  super1:    { pass: '1234', role: 'supervisor',id: 3 },   // << NUEVO
  bodega1:   { pass: '1234', role: 'bodeguero', id: 4 },   // << NUEVO
};

function login() {
  const u = (document.getElementById('usuario')?.value || '').trim().toLowerCase();
  const p = document.getElementById('password')?.value || '';

  const info = USERS[u];
  if (info && p === info.pass) {
    setSession({ id: info.id, role: info.role });
    if (info.role === 'vendedor') {
      location.href = 'vendedor.html';
    } else {
      location.href = 'main.html';
    }
    return;
  }

  const msg = document.getElementById('login-msg');
  if (msg) msg.textContent = 'Usuario o contraseña incorrectos';
  toast('Credenciales inválidas', 'error');
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  if (form) form.addEventListener('submit', (e) => { e.preventDefault(); login(); });
});
