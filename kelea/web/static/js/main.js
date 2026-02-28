/* ============================================================
   HackUDC 2026 — main.js
   Global interactions, toast notifications, form helpers
   ============================================================ */

// ---------- Toast Notifications ----------
function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const iconMap = {
    success: '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `${iconMap[type] || iconMap.success}<span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    toast.addEventListener('animationend', () => toast.remove());
  }, 3500);
}

// ---------- Input focus glow animation ----------
document.querySelectorAll('.form-input').forEach(input => {
  input.addEventListener('focus', () => {
    input.closest('.input-wrapper')?.querySelector('.input-icon')?.style
      && (input.closest('.input-wrapper').querySelector('.input-icon').style.color = 'var(--clr-accent)');
  });
  input.addEventListener('blur', () => {
    input.closest('.input-wrapper')?.querySelector('.input-icon')?.style
      && (input.closest('.input-wrapper').querySelector('.input-icon').style.color = '');
  });
});

// ---------- Animate stat values (count-up) ----------
function animateCount(el, target, duration = 1200) {
  if (!el || isNaN(target)) return;
  const start = 0;
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + eased * (target - start)).toLocaleString('es');
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// Run count-up on stat values that are numeric
window.addEventListener('load', () => {
  document.querySelectorAll('.stat-value').forEach(el => {
    const val = parseInt(el.textContent.replace(/[^\d]/g, ''));
    if (!isNaN(val)) animateCount(el, val);
  });
});

// ---------- Sidebar resize handler ----------
window.addEventListener('resize', () => {
  if (window.innerWidth > 768) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.style.display = 'none';
  }
});
