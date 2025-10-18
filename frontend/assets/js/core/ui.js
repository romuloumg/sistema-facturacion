export function money(v){ return 'Q' + Number(v).toFixed(2); }

export function toast(msg, type='success', ms=2600){
  const wrap = document.getElementById('toast');
  if(!wrap) return;
  const el = document.createElement('div');
  el.className = `toast-item toast-${type}`;
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), ms);
}

// helpers simples
export function $(sel, root=document){ return root.querySelector(sel); }
export function $all(sel, root=document){ return [...root.querySelectorAll(sel)]; }
