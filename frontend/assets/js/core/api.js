// frontend/assets/js/core/api.js
const API_BASE = 'http://127.0.0.1:5000';

function authHeaders(json = true) {
  const h = {};
  if (json) h['Content-Type'] = 'application/json';

  const uid  = localStorage.getItem('userId') || '';
  const role = localStorage.getItem('userRole') || 'admin';

  if (uid) h['X-User-Id'] = uid;   // usuario real desde BD
  h['X-Role'] = role;              // respaldo por rol

  return h;
}

export async function getJSON(path) {
  const res  = await fetch(API_BASE + path, { headers: authHeaders(false) });
  const text = await res.text();
  let data = null; try { data = text ? JSON.parse(text) : null; } catch {}
  if (!res.ok) throw new Error(data?.error || `${res.status} ${text || ''}`.trim());
  return data;
}

export async function postJSON(path, body) {
  const res  = await fetch(API_BASE + path, { method: 'POST', headers: authHeaders(true), body: JSON.stringify(body) });
  const text = await res.text();
  let data = null; try { data = text ? JSON.parse(text) : null; } catch {}
  if (!res.ok) throw new Error(data?.error || `${res.status} ${text || ''}`.trim());
  return data;
}

export async function patchJSON(path, body) {
  const res  = await fetch(API_BASE + path, { method: 'PATCH', headers: authHeaders(true), body: JSON.stringify(body) });
  const text = await res.text();
  let data = null; try { data = text ? JSON.parse(text) : null; } catch {}
  if (!res.ok) throw new Error(data?.error || `${res.status} ${text || ''}`.trim());
  return data;
}
