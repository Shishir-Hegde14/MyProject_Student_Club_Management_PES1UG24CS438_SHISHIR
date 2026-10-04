async function updateStatus() {
  const note = document.getElementById('refresh-note');
  try {
    const response = await fetch('/api/status');
    if (!response.ok || response.redirected) throw new Error('Session expired');
    const data = await response.json();
    const rows = document.querySelectorAll('[data-event]');
    if (rows.length !== data.events.length) { location.reload(); return; }
    for (const event of data.events) {
      const row = document.querySelector(`[data-event="${event.id}"]`);
      if (!row) { location.reload(); return; }
      row.querySelector('.status').textContent = event.status;
      row.querySelector('.count').textContent = event.registrations;
    }
    const available = document.getElementById('available');
    if (available) available.textContent = (data.available / 100).toFixed(2);
    note.textContent = '';
  } catch (_) { note.textContent = 'Could not refresh. Check your connection or log in again.'; }
}
setInterval(updateStatus, 3000);
