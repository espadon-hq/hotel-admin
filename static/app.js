// app.js — спільна логіка

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
  let c = document.querySelector('.toast-container');
  if (!c) { c = document.createElement('div'); c.className = 'toast-container'; document.body.appendChild(c); }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${type === 'success' ? '✓' : '✕'}</span> ${msg}`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

// ─── Modal ─────────────────────────────────────────────────────────────────────
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});

// ─── Debounce ──────────────────────────────────────────────────────────────────
function debounce(fn, ms = 280) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

// ─── Client-side table sorter ──────────────────────────────────────────────────
// makeTableSorter(tbodyId, renderRowFn)
// Usage:
//   const tbl = makeTableSorter('tbody-id', row => `<tr>...</tr>`);
//   tbl.setData(array);          // завантажити дані й відрендерити
//   // на кожен <th>: data-sort="fieldName" onclick="tbl.sort(this)"
function makeTableSorter(tbodyId, renderRow) {
  let _data = [];
  let _field = null;
  let _asc   = true;

  // розумне порівняння: null — в кінець, числа — числово, дати — як дати
  function cmp(a, b) {
    if (a === null || a === undefined) return 1;
    if (b === null || b === undefined) return -1;
    // дата ISO
    if (typeof a === 'string' && /^\d{4}-\d{2}-\d{2}/.test(a))
      return new Date(a) - new Date(b);
    // число або числовий рядок
    const na = Number(a), nb = Number(b);
    if (!isNaN(na) && !isNaN(nb)) return na - nb;
    return String(a).localeCompare(String(b), 'uk');
  }

  function sorted() {
    if (!_field) return _data;
    return [..._data].sort((a, b) => {
      const d = cmp(a[_field], b[_field]);
      return _asc ? d : -d;
    });
  }

  function updateHeaders() {
    document.querySelectorAll('thead th[data-sort]').forEach(th => {
      th.classList.remove('sorted');
      const old = th.querySelector('.sort-arrow');
      if (old) old.remove();
      if (th.dataset.sort === _field) {
        th.classList.add('sorted');
        const arr = document.createElement('span');
        arr.className = 'sort-arrow';
        arr.textContent = _asc ? ' ↑' : ' ↓';
        th.appendChild(arr);
      }
    });
  }

  function render() {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    const rows = sorted();
    tbody.innerHTML = rows.length
      ? rows.map(renderRow).join('')
      : `<tr><td colspan="99"><div class="empty-state"><p>Нічого не знайдено</p></div></td></tr>`;
    updateHeaders();
  }

  return {
    setData(data) { _data = data; render(); },
    getData()     { return _data; },
    sort(th) {
      const f = th.dataset.sort;
      if (_field === f) _asc = !_asc;
      else { _field = f; _asc = true; }
      render();
    },
  };
}

// ─── Formatters ────────────────────────────────────────────────────────────────
function fmtDate(d)  { return d ? new Date(d).toLocaleDateString('uk-UA') : '—'; }
function fmtMoney(n) { return n != null ? Number(n).toLocaleString('uk-UA') + ' ₴' : '—'; }
function esc(s)      { return s == null ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function stars(n)    { return n ? `<span class="stars">${n} / 5</span>` : '<span class="td-muted">—</span>'; }

// ─── Badges ─────────────────────────────────────────────────────────────────────
function statusBadge(t) {
  const m = { 'Підтверджено':'success','Confirmed':'success','Очікує':'warning','Pending':'warning','Скасовано':'danger','Cancelled':'danger','Завершено':'info','Completed':'info','Заїхав':'success' };
  return `<span class="badge badge-${m[t]||'muted'}">${t||'—'}</span>`;
}
function roomStatusBadge(t) {
  const m = { 'Вільний':'success','Free':'success','Зайнятий':'danger','Occupied':'danger','На обслуговуванні':'warning','Maintenance':'warning' };
  return `<span class="badge badge-${m[t]||'muted'}">${t||'—'}</span>`;
}

// ─── Sidebar active ────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-link').forEach(a => {
  if (a.href === location.href) a.classList.add('active');
});