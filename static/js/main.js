/* ══════════════════════════════════════════════
   Kishaan Deepak — main.js  (Multilingual Edition)
   ══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─── i18n helper (reads from global I18N defined in index.html) ── */
  function t(key) {
    if (typeof I18N === 'undefined') return key;
    const obj = I18N[key];
    if (!obj) return key;
    const lang = document.documentElement.getAttribute('lang') || 'en';
    return obj[lang] || obj['en'] || key;
  }

  /* ─── Tab switching ─────────────────────────── */
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + target).classList.add('active');
    });
  });

  /* ─── Health / status ──────────────────────── */
  const pip   = document.getElementById('status-pip');
  const label = document.getElementById('status-label');

  fetch('/api/health')
    .then(r => r.json())
    .then(d => {
      const yieldOk   = d.yield_model   === 'loaded';
      const diseaseOk = d.disease_model === 'loaded';

      if (yieldOk && diseaseOk) {
        pip.className   = 'status-pip ok';
        label.textContent = t('status_ready');
      } else if (yieldOk || diseaseOk) {
        pip.className   = 'status-pip warn';
        label.textContent = t('status_partial');
      } else {
        pip.className   = 'status-pip err';
        label.textContent = t('status_error');
      }

      document.getElementById('stat-yield-hero').textContent   = yieldOk   ? t('stat_ready') : t('stat_not_loaded');
      document.getElementById('stat-disease-hero').textContent = diseaseOk ? t('stat_ready') : t('stat_not_loaded');
    })
    .catch(() => {
      pip.className = 'status-pip err';
      label.textContent = t('status_unreachable');
    });

  /* ─── Yield: populate dropdowns ────────────── */
  fetch('/api/yield/options')
    .then(r => r.json())
    .then(opts => {
      fillSelect('yield-crop',   opts.crop_type || []);
      fillSelect('yield-region', opts.region    || []);
      fillSelect('yield-soil',   opts.soil_type || []);
    })
    .catch(() => ['yield-crop','yield-region','yield-soil'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = `<option value="">${t('unavailable')}</option>`;
    }));

  function fillSelect(id, arr) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = arr.length
      ? arr.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('')
      : `<option value="">—</option>`;
  }

  /* ─── Yield: form submit ────────────────────── */
  const yieldForm   = document.getElementById('yield-form');
  const yieldSubmit = document.getElementById('yield-submit-btn');

  yieldForm.addEventListener('submit', async e => {
    e.preventDefault();
    const fd = new FormData(yieldForm);
    const payload = {};
    fd.forEach((v, k) => payload[k] = v);
    payload.temperature_c    = parseFloat(payload.temperature_c);
    payload.rainfall_mm      = parseFloat(payload.rainfall_mm);
    payload.humidity_percent = parseFloat(payload.humidity_percent);

    setLoading(yieldSubmit, true, t('running_prediction'));
    try {
      const resp = await fetch('/api/yield/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (resp.ok) {
        showYieldResult(data.prediction_tonnes_per_hectare, payload);
      } else {
        showYieldError(data.error || t('btn_try_again'));
      }
    } catch (err) {
      showYieldError('Network error: ' + err.message);
    } finally {
      setLoading(yieldSubmit, false, null, 'yield');
    }
  });

  function showYieldResult(val, p) {
    document.getElementById('yield-number').textContent = val.toFixed(4);
    document.getElementById('yield-details').innerHTML =
      `<strong>${p.crop_type}</strong> · ${p.region} · ${p.soil_type}<br>` +
      `${p.temperature_c}°C · ${p.rainfall_mm} mm · ${p.humidity_percent}%`;
    toggle('yield-placeholder', false);
    toggle('yield-result-content', true);
    toggle('yield-error', false);
  }
  function showYieldError(msg) {
    document.getElementById('yield-error-msg').textContent = msg;
    toggle('yield-placeholder', false);
    toggle('yield-result-content', false);
    toggle('yield-error', true);
  }
  function resetYield() {
    toggle('yield-placeholder', true);
    toggle('yield-result-content', false);
    toggle('yield-error', false);
    yieldForm.reset();
  }
  document.getElementById('yield-reset-btn').addEventListener('click', resetYield);
  document.getElementById('yield-error-reset').addEventListener('click', resetYield);

  /* ─── Disease classes ───────────────────────── */
  fetch('/api/disease/classes')
    .then(r => r.json())
    .then(d => {
      if (!d.classes) return;
      document.getElementById('classes-grid').innerHTML =
        d.classes.map(c => `<span class="class-chip">${esc(c)}</span>`).join('');
    })
    .catch(() => {});

  /* ─── Disease: upload / drag-drop ──────────── */
  const fileInput   = document.getElementById('disease-file');
  const uploadZone  = document.getElementById('upload-zone');
  const previewWrap = document.getElementById('image-preview-wrap');
  const previewImg  = document.getElementById('image-preview');
  const removeBtn   = document.getElementById('remove-img');
  const submitBtn   = document.getElementById('disease-submit-btn');
  let selectedFile  = null;

  uploadZone.addEventListener('click', () => fileInput.click());
  uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
  uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

  removeBtn.addEventListener('click', () => { clearFile(); resetDisease(); });

  function handleFile(file) {
    if (!/\.(png|jpe?g)$/i.test(file.name)) { alert(t('only_png_jpg')); return; }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = e => previewImg.src = e.target.result;
    reader.readAsDataURL(file);
    uploadZone.hidden  = true;
    previewWrap.hidden = false;
    submitBtn.disabled = false;
    resetDisease();
  }
  function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    previewWrap.hidden = true;
    uploadZone.hidden  = false;
    submitBtn.disabled = true;
  }

  /* ─── Disease: submit ───────────────────────── */
  submitBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    setLoading(submitBtn, true, t('analysing'));
    const fd = new FormData();
    fd.append('file', selectedFile);
    try {
      const resp = await fetch('/api/disease/predict', { method: 'POST', body: fd });
      const data = await resp.json();
      if (resp.ok && data.success) {
        showDiseaseResult(data);
      } else {
        showDiseaseError(data.error || 'Analysis failed.');
      }
    } catch (err) {
      showDiseaseError('Network error: ' + err.message);
    } finally {
      setLoading(submitBtn, false, null, 'disease');
    }
  });

  function showDiseaseResult(data) {
    document.getElementById('disease-img-box').innerHTML =
      `<img src="${data.image}" alt="Uploaded leaf" />`;
    document.getElementById('diag-disease').textContent = data.disease;
    document.getElementById('conf-pct').textContent = data.confidence.toFixed(1) + '%';
    const fill = document.getElementById('conf-bar');
    fill.style.width = '0%';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { fill.style.width = data.confidence + '%'; });
    });
    renderProbChart(data.all_predictions);

    toggle('disease-placeholder', false);
    toggle('disease-result-content', true);
    toggle('disease-error', false);
  }

  function renderProbChart(probs) {
    const palette = [
      '#4a9e6b','#c8a84b','#3d9e8e','#7e6bb5','#c85b4a',
      '#6b9ec8','#c88a4a','#4ac8a0','#9ec84a','#c84a8a',
    ];
    const entries = Object.entries(probs).sort((a, b) => b[1] - a[1]);
    document.getElementById('prob-chart').innerHTML = entries.map(([name, pct], i) => `
      <div class="prob-row">
        <span class="prob-name" title="${esc(name)}">${esc(name)}</span>
        <div class="prob-track">
          <div class="prob-fill" style="width:${pct}%; background:${palette[i % palette.length]};"></div>
        </div>
        <span class="prob-pct">${pct.toFixed(1)}%</span>
      </div>`).join('');
  }

  function showDiseaseError(msg) {
    document.getElementById('disease-error-msg').textContent = msg;
    toggle('disease-placeholder', false);
    toggle('disease-result-content', false);
    toggle('disease-error', true);
  }
  function resetDisease() {
    toggle('disease-placeholder', true);
    toggle('disease-result-content', false);
    toggle('disease-error', false);
  }
  function resetDiseaseAndFile() { clearFile(); resetDisease(); }
  document.getElementById('disease-reset-btn').addEventListener('click', resetDiseaseAndFile);
  document.getElementById('disease-error-reset').addEventListener('click', resetDiseaseAndFile);

  /* ─── Helpers ───────────────────────────────── */
  function toggle(id, show) {
    const el = document.getElementById(id);
    if (el) el.hidden = !show;
  }
  function esc(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  function setLoading(btn, loading, loadText, type) {
    if (loading) {
      btn.disabled = true;
      btn.innerHTML = `<span class="btn-spinner"></span> ${loadText}`;
    } else {
      btn.disabled = false;
      if (type === 'yield') {
        btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> <span data-i18n="btn_run_prediction">${t('btn_run_prediction')}</span>`;
      } else {
        btn.disabled = (selectedFile === null);
        btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg> <span data-i18n="btn_analyse">${t('btn_analyse')}</span>`;
      }
    }
  }

  /* ─── Re-translate dynamic content when language changes ── */
  // Listen for lang attribute changes on <html>
  const observer = new MutationObserver(() => {
    // Re-translate button labels if they're in loading state text
    const yBtn = document.getElementById('yield-submit-btn');
    const dBtn = document.getElementById('disease-submit-btn');
    if (yBtn && !yBtn.disabled) {
      yBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> <span data-i18n="btn_run_prediction">${t('btn_run_prediction')}</span>`;
    }
    if (dBtn && !dBtn.disabled) {
      dBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg> <span data-i18n="btn_analyse">${t('btn_analyse')}</span>`;
    }
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

});