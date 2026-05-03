// app.js — спільна логіка для всіх сторінок

const API = '/api';

// ─── HTTP helpers ──────────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

const apiGet    = (p, params = {}) => {
  const qs = new URLSearchParams(Object.entries(params).filter(([,v]) => v != null && v !== '')).toString();
  return apiFetch(p + (qs ? '?' + qs : ''));
};
const apiPost   = (p, body) => apiFetch(p, { method: 'POST',   body: JSON.stringify(body) });
const apiPut    = (p, body) => apiFetch(p, { method: 'PUT',    body: JSON.stringify(body) });
const apiDelete = (p)       => apiFetch(p, { method: 'DELETE' });

// ─── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${type === 'success' ? '' : ''}</span> ${msg}`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

// ─── Modal ─────────────────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

// Close modal on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// ─── Sorting state ─────────────────────────────────────────────────────────────
function makeSorter(defaultField = 'id') {
  let field = defaultField, order = 'ASC';
  return {
    get: () => ({ sort: field, order }),
    toggle: (f) => {
      if (field === f) order = order === 'ASC' ? 'DESC' : 'ASC';
      else { field = f; order = 'ASC'; }
    },
    apply: (headers) => {
      headers.forEach(th => {
        th.classList.remove('sorted');
        th.dataset.order = '';
        if (th.dataset.sort === field) {
          th.classList.add('sorted');
          th.dataset.order = order;
        }
      });
    }
  };
}

// ─── Debounce ──────────────────────────────────────────────────────────────────
function debounce(fn, ms = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ─── Stars renderer ────────────────────────────────────────────────────────────
function stars(n) {
  if (!n) return '<span class="td-muted">—</span>';
  return '<span class="stars">' + n + ' / 5' + '</span>';
}

// ─── Badge helpers ─────────────────────────────────────────────────────────────
function statusBadge(title) {
  const map = {
    'Підтверджено': 'success', 'Confirmed': 'success',
    'Очікує': 'warning',       'Pending': 'warning',
    'Скасовано': 'danger',     'Cancelled': 'danger',
    'Завершено': 'info',       'Completed': 'info',
    'Заїхав': 'success',
  };
  const cls = map[title] || 'muted';
  return `<span class="badge badge-${cls}">${title || '—'}</span>`;
}

function roomStatusBadge(title) {
  const map = {
    'Вільний': 'success', 'Free': 'success',
    'Зайнятий': 'danger', 'Occupied': 'danger',
    'На обслуговуванні': 'warning', 'Maintenance': 'warning',
  };
  const cls = map[title] || 'muted';
  return `<span class="badge badge-${cls}">${title || '—'}</span>`;
}

// ─── Format helpers ────────────────────────────────────────────────────────────
function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('uk-UA');
}
function fmtMoney(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString('uk-UA', { minimumFractionDigits: 0 }) + ' ₴';
}
function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── Sidebar active link ───────────────────────────────────────────────────────
document.querySelectorAll('.nav-link').forEach(a => {
  if (a.href === location.href) a.classList.add('active');
});