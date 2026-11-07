/**
 * PokeTranslator GBA - Frontend Application Controller
 */

let currentCategory = 'all';
let currentSearch = '';
let currentPage = 1;
const pageSize = 50;
let totalEntries = 0;
let isRomLoaded = false;

// DOM Elements
const btnSelectRom = document.getElementById('btnSelectRom');
const romFileInput = document.getElementById('romFileInput');
const dropZone = document.getElementById('dropZone');
const dropHint = document.getElementById('dropHint');
const actionsGroup = document.getElementById('actionsGroup');
const romInfoBanner = document.getElementById('romInfoBanner');
const mainContent = document.getElementById('mainContent');
const welcomeContainer = document.getElementById('welcomeContainer');

const infoFilename = document.getElementById('infoFilename');
const infoTitle = document.getElementById('infoTitle');
const infoCode = document.getElementById('infoCode');
const infoEngine = document.getElementById('infoEngine');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const statusText = document.getElementById('statusText');
const headerStatus = document.getElementById('headerStatus');

const categoryTabs = document.getElementById('categoryTabs');
const searchInput = document.getElementById('searchInput');
const entriesTbody = document.getElementById('entriesTbody');
const paginationInfo = document.getElementById('paginationInfo');
const pageDisplay = document.getElementById('pageDisplay');
const btnPrevPage = document.getElementById('btnPrevPage');
const btnNextPage = document.getElementById('btnNextPage');

const btnAutoTranslate = document.getElementById('btnAutoTranslate');
const btnExportRom = document.getElementById('btnExportRom');
const btnExportIps = document.getElementById('btnExportIps');
const sampleRomSelect = document.getElementById('sampleRomSelect');
const btnLoadSample = document.getElementById('btnLoadSample');

const previewText = document.getElementById('previewText');
const chkPatchFont = document.getElementById('chkPatchFont');
const charWidthRange = document.getElementById('charWidthRange');
const charWidthVal = document.getElementById('charWidthVal');
const btnToggleGlyphs = document.getElementById('btnToggleGlyphs');
const glyphGrid = document.getElementById('glyphGrid');

// Progress & ETA Modal Elements
const progressModal = document.getElementById('progressModal');
const modalTaskTitle = document.getElementById('modalTaskTitle');
const modalTaskDetail = document.getElementById('modalTaskDetail');
const modalProgressStage = document.getElementById('modalProgressStage');
const modalProgressPercent = document.getElementById('modalProgressPercent');
const modalProgressFill = document.getElementById('modalProgressFill');
const modalStatItems = document.getElementById('modalStatItems');
const modalStatElapsed = document.getElementById('modalStatElapsed');
const modalStatEta = document.getElementById('modalStatEta');
const modalStatSpeed = document.getElementById('modalStatSpeed');
const modalFooterMessage = document.getElementById('modalFooterMessage');

let progressPollTimer = null;
let modalStartTime = 0;

function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const remSec = s % 60;
  return `${String(m).padStart(2, '0')}:${String(remSec).padStart(2, '0')}`;
}

function formatEta(seconds) {
  if (seconds === undefined || seconds === null || isNaN(seconds) || seconds <= 0) {
    return '完了間近...';
  }
  const s = Math.ceil(seconds);
  if (s <= 1) return '残り約 1秒';
  if (s < 60) return `残り約 ${s}秒`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `残り約 ${m}分 ${rem}秒`;
}

function showProgressModal(title, initialDetail = '準備中...') {
  modalStartTime = Date.now();
  modalTaskTitle.textContent = title;
  modalTaskDetail.textContent = initialDetail;
  modalProgressPercent.textContent = '0%';
  modalProgressFill.style.width = '0%';
  modalStatItems.textContent = '-';
  modalStatElapsed.textContent = '00:00';
  modalStatEta.textContent = '計算中...';
  modalStatSpeed.textContent = '-';
  progressModal.style.display = 'flex';
}

function updateProgressModal(data) {
  if (data.title) modalTaskTitle.textContent = data.title;
  if (data.detail) modalTaskDetail.textContent = data.detail;
  if (data.percentage !== undefined) {
    const pct = Math.min(100, Math.max(0, data.percentage));
    modalProgressPercent.textContent = `${pct.toFixed(1)}%`;
    modalProgressFill.style.width = `${pct}%`;
  }
  if (data.itemsText) {
    modalStatItems.textContent = data.itemsText;
  } else if (data.current !== undefined && data.total !== undefined) {
    modalStatItems.textContent = `${Number(data.current).toLocaleString()} / ${Number(data.total).toLocaleString()} 項目`;
  }
  if (data.elapsedSeconds !== undefined) {
    modalStatElapsed.textContent = formatTime(data.elapsedSeconds);
  } else if (modalStartTime > 0) {
    modalStatElapsed.textContent = formatTime((Date.now() - modalStartTime) / 1000);
  }
  if (data.etaText) {
    modalStatEta.textContent = data.etaText;
  } else if (data.etaSeconds !== undefined) {
    modalStatEta.textContent = formatEta(data.etaSeconds);
  }
  if (data.speedText) {
    modalStatSpeed.textContent = data.speedText;
  } else if (data.speed !== undefined) {
    modalStatSpeed.textContent = `${Math.round(data.speed)} 項目/秒`;
  }
  if (data.footerMessage) {
    modalFooterMessage.textContent = data.footerMessage;
  }
}

function hideProgressModal(delayMs = 300) {
  if (progressPollTimer) {
    clearInterval(progressPollTimer);
    progressPollTimer = null;
  }
  setTimeout(() => {
    progressModal.style.display = 'none';
  }, delayMs);
}

function startProgressPolling(onDone) {
  if (progressPollTimer) clearInterval(progressPollTimer);
  progressPollTimer = setInterval(async () => {
    try {
      const resp = await fetch('/api/progress');
      if (!resp.ok) return;
      const data = await resp.json();
      if (!data) return;

      updateProgressModal({
        title: data.title,
        detail: data.detail,
        current: data.current,
        total: data.total,
        percentage: data.percentage,
        elapsedSeconds: data.elapsed_seconds,
        speed: data.speed,
        etaSeconds: data.eta_seconds,
      });

      if (data.finished) {
        clearInterval(progressPollTimer);
        progressPollTimer = null;
        if (onDone) onDone(data);
      }
    } catch (e) {
      console.warn('Progress poll error:', e);
    }
  }, 200);
}

// ---------------------------------------------------------------------------
// Initialization & File Upload
// ---------------------------------------------------------------------------
async function loadSampleRoms() {
  try {
    const resp = await fetch('/api/sample_roms');
    if (!resp.ok) return;
    const data = await resp.json();
    if (data.samples && data.samples.length > 0) {
      sampleRomSelect.innerHTML = '<option value="">-- サンプルROMを選択 --</option>';
      data.samples.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.filename;
        opt.textContent = `${s.filename} (${s.size_mb}MB)`;
        sampleRomSelect.appendChild(opt);
      });
    }
  } catch (e) {
    console.error('Failed to load sample ROMs:', e);
  }
}
loadSampleRoms();

btnLoadSample.addEventListener('click', async () => {
  const selected = sampleRomSelect.value;
  if (!selected) {
    alert('読み込むサンプルROMを選択してください。');
    return;
  }
  statusText.textContent = `${selected} を解析中...`;
  btnLoadSample.disabled = true;
  btnLoadSample.textContent = '解析中...';
  showProgressModal(`サンプルROM読み込み: ${selected}`, 'ROMバイナリをロードしています...');

  startProgressPolling();

  try {
    const resp = await fetch('/api/load_sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: selected }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'Failed to load sample');
    }
    const data = await resp.json();
    updateProgressModal({
      percentage: 100,
      detail: 'ROM解析完了！画面を初期化しています...',
      etaText: '完了',
    });
    setTimeout(() => {
      hideProgressModal(250);
      onRomLoaded(data);
    }, 400);
  } catch (err) {
    hideProgressModal(100);
    alert('サンプルROMの読み込みに失敗しました: ' + err.message);
  } finally {
    btnLoadSample.disabled = false;
    btnLoadSample.textContent = '読み込む';
  }
});
btnSelectRom.addEventListener('click', () => romFileInput.click());

romFileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    uploadRomFile(e.target.files[0]);
  }
});

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) {
    uploadRomFile(e.dataTransfer.files[0]);
  }
});

function uploadRomFile(file) {
  if (!file.name.toLowerCase().endsWith('.gba')) {
    alert('.gba 形式のGame Boy Advance ROMファイルを選択してください。');
    return;
  }

  statusText.textContent = 'ROM読み込み・解析中...';
  dropHint.textContent = `${file.name} をアップロード中...`;
  showProgressModal(`ROMアップロード & 解析: ${file.name}`, 'アップロード準備中...');

  const fileSizeMb = (file.size / (1024 * 1024)).toFixed(1);
  const uploadStartTime = Date.now();

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/upload_rom');
  xhr.setRequestHeader('Content-Type', 'application/octet-stream');

  xhr.upload.onprogress = (evt) => {
    if (evt.lengthComputable) {
      const elapsed = Math.max(0.001, (Date.now() - uploadStartTime) / 1000);
      const loadedMb = (evt.loaded / (1024 * 1024)).toFixed(1);
      const totalMb = (evt.total / (1024 * 1024)).toFixed(1);
      const pct = (evt.loaded / evt.total) * 100;
      const speedMb = (evt.loaded / (1024 * 1024)) / elapsed;
      const remainingBytes = evt.total - evt.loaded;
      const eta = speedMb > 0 ? (remainingBytes / (1024 * 1024)) / speedMb : 0;

      updateProgressModal({
        detail: `${file.name} をアップロード中...`,
        percentage: pct * 0.7, // Upload is 0-70%, Server extraction is 70-100%
        itemsText: `${loadedMb} / ${totalMb} MB`,
        elapsedSeconds: elapsed,
        speedText: `${speedMb.toFixed(1)} MB/秒`,
        etaSeconds: eta,
      });
    }
  };

  xhr.upload.onload = () => {
    updateProgressModal({
      percentage: 75,
      detail: 'サーバー側でROMバイナリ展開 & テキスト抽出中...',
      itemsText: `${fileSizeMb} / ${fileSizeMb} MB`,
      etaText: '抽出中...',
      speedText: '内部処理中',
    });
    startProgressPolling();
  };

  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const data = JSON.parse(xhr.responseText);
        updateProgressModal({
          percentage: 100,
          detail: 'ROM読み込み完了！',
          etaText: '完了',
        });
        setTimeout(() => {
          hideProgressModal(250);
          onRomLoaded(data);
        }, 350);
      } catch (e) {
        hideProgressModal(100);
        alert('レスポンスの解析に失敗しました: ' + e.message);
      }
    } else {
      hideProgressModal(100);
      let msg = 'ROMの読み込みに失敗しました';
      try {
        const err = JSON.parse(xhr.responseText);
        if (err.error) msg += ': ' + err.error;
      } catch (e) {}
      alert(msg);
      statusText.textContent = '読み込みエラー';
    }
  };

  xhr.onerror = () => {
    hideProgressModal(100);
    alert('ネットワークエラーによりアップロードが中断されました。');
    statusText.textContent = 'エラー';
  };

  xhr.send(file);
}

function onRomLoaded(data) {
  isRomLoaded = true;
  const rom = data.rom_info;
  const stats = data.stats;

  infoFilename.textContent = rom.filename;
  infoTitle.textContent = rom.title || '(No Title)';
  infoCode.textContent = rom.code || 'BPRE';
  infoEngine.textContent = rom.engine;

  updateProgress(stats);

  statusText.textContent = `${rom.title || 'ROM'} 読み込み完了`;
  headerStatus.querySelector('.status-badge').className = 'status-badge active';

  dropHint.textContent = `選択中: ${rom.filename} (${rom.size_mb} MB)`;
  actionsGroup.style.display = 'flex';
  romInfoBanner.style.display = 'grid';
  mainContent.style.display = 'grid';
  welcomeContainer.style.display = 'none';

  loadEntries();
}

function updateProgress(stats) {
  if (!stats) return;
  const pct = stats.completion_percentage || 0;
  progressBar.style.width = `${pct}%`;
  progressText.textContent = `${pct}% (${stats.translated_entries} / ${stats.total_entries} 件 翻訳済)`;
}

// ---------------------------------------------------------------------------
// Entries Table & Pagination
// ---------------------------------------------------------------------------
async function loadEntries() {
  if (!isRomLoaded) return;

  const url = `/api/entries?category=${encodeURIComponent(currentCategory)}&search=${encodeURIComponent(currentSearch)}&page=${currentPage}&page_size=${pageSize}`;
  try {
    const resp = await fetch(url);
    const data = await resp.json();

    totalEntries = data.total;
    renderEntries(data.entries);
    updatePaginationUI();
  } catch (err) {
    console.error('Failed to load entries:', err);
  }
}

function renderEntries(entries) {
  entriesTbody.innerHTML = '';

  if (entries.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="4" style="text-align:center; padding: 2rem; color: var(--text-muted);">該当するテキストが見つかりません</td>`;
    entriesTbody.appendChild(tr);
    return;
  }

  entries.forEach((entry) => {
    const tr = document.createElement('tr');
    tr.dataset.id = entry.id;

    const catBadge = getCategoryBadge(entry.category);

    tr.innerHTML = `
      <td><span class="badge-cat ${entry.category}">${catBadge}</span></td>
      <td><strong>${escapeHtml(entry.original)}</strong></td>
      <td>
        <input type="text" class="trans-input" value="${escapeHtml(entry.translated || '')}" placeholder="日本語を入力..." data-id="${entry.id}">
      </td>
      <td>
        <button class="btn btn-outline btn-sm btn-quick-preview" title="実機プレビューに表示">👁️</button>
      </td>
    `;

    // Row click previews dialogue
    tr.addEventListener('click', (e) => {
      if (!e.target.classList.contains('trans-input')) {
        updateGbaPreview(entry.translated || entry.original);
      }
    });

    // Input changes
    const input = tr.querySelector('.trans-input');
    input.addEventListener('input', debounce((e) => {
      const val = e.target.value;
      updateEntryTranslation(entry.id, val);
      updateGbaPreview(val || entry.original);
    }, 400));

    entriesTbody.appendChild(tr);
  });
}

function getCategoryBadge(cat) {
  const map = {
    species: 'ポケモン',
    moves: 'わざ',
    items: 'どうぐ',
    item_descriptions: '説明文',
    abilities: 'とくせい',
    types: 'タイプ',
    menu: 'メニュー',
    dialogue: 'セリフ',
  };
  return map[cat] || cat;
}

function updatePaginationUI() {
  const totalPages = Math.max(1, Math.ceil(totalEntries / pageSize));
  pageDisplay.textContent = `Page ${currentPage} / ${totalPages}`;
  paginationInfo.textContent = `全 ${totalEntries} 件中 ${(currentPage - 1) * pageSize + 1} - ${Math.min(currentPage * pageSize, totalEntries)} 件`;

  btnPrevPage.disabled = currentPage <= 1;
  btnNextPage.disabled = currentPage >= totalPages;
}

btnPrevPage.addEventListener('click', () => {
  if (currentPage > 1) {
    currentPage--;
    loadEntries();
  }
});

btnNextPage.addEventListener('click', () => {
  const totalPages = Math.ceil(totalEntries / pageSize);
  if (currentPage < totalPages) {
    currentPage++;
    loadEntries();
  }
});

// Category Tab Switching
categoryTabs.addEventListener('click', (e) => {
  if (e.target.classList.contains('tab-btn')) {
    categoryTabs.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    currentCategory = e.target.dataset.category;
    currentPage = 1;
    loadEntries();
  }
});

// Search Input Filtering
searchInput.addEventListener('input', debounce((e) => {
  currentSearch = e.target.value.trim();
  currentPage = 1;
  loadEntries();
}, 300));

// ---------------------------------------------------------------------------
// Entry Updating
// ---------------------------------------------------------------------------
async function updateEntryTranslation(id, text) {
  try {
    const resp = await fetch('/api/update_entry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id, translated: text }),
    });
    if (resp.ok) {
      refreshStatus();
    }
  } catch (err) {
    console.error('Failed to update entry:', err);
  }
}

async function refreshStatus() {
  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();
    if (data.project) {
      updateProgress(data.project);
    }
  } catch (e) {}
}

// ---------------------------------------------------------------------------
// Batch Actions: Auto Translate & Export
// ---------------------------------------------------------------------------
btnAutoTranslate.addEventListener('click', async () => {
  if (!confirm('辞書マッチ・表記ゆれ正規化・説明文パターン・自然機械翻訳を使い、全項目を完全自動翻訳しますか？')) {
    return;
  }

  btnAutoTranslate.disabled = true;
  btnAutoTranslate.textContent = '🚀 全自動翻訳中...';
  showProgressModal('🚀 100%全自動翻訳を実行中', '辞書照合と翻訳エンジンを初期化しています...');

  startProgressPolling();

  try {
    const resp = await fetch('/api/auto_translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ overwrite: false, use_machine_translation: true }),
    });

    const data = await resp.json();
    updateProgressModal({
      percentage: 100,
      detail: `すべての項目の翻訳が完了しました (${data.translated_count} 件翻訳)`,
      etaText: '完了',
    });

    setTimeout(() => {
      hideProgressModal(350);
      alert(`全自動翻訳が完了しました！ (${data.translated_count} 件を自動翻訳)`);
      updateProgress(data.stats);
      loadEntries();
    }, 450);
  } catch (err) {
    hideProgressModal(100);
    alert('自動翻訳に失敗しました: ' + err.message);
  } finally {
    btnAutoTranslate.disabled = false;
    btnAutoTranslate.textContent = '🚀 100%全自動翻訳';
  }
});

btnExportRom.addEventListener('click', async () => {
  btnExportRom.disabled = true;
  btnExportRom.textContent = 'ROM構築中...';
  showProgressModal('📥 日本語版GBA ROMを出力中', 'フォント注入と翻訳テーブルの書き込みを準備しています...');

  startProgressPolling();

  try {
    const patchFont = chkPatchFont.checked;
    const resp = await fetch('/api/build_rom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patch_font: patchFont }),
    });

    if (!resp.ok) throw new Error('ROM build failed');

    updateProgressModal({
      percentage: 100,
      detail: 'ROM構築完了！ダウンロードを開始します...',
      etaText: '完了',
    });

    const blob = await resp.blob();
    const filename = infoFilename.textContent.replace(/\.gba$/i, '') + '_JP.gba';
    downloadBlob(blob, filename);
    setTimeout(() => hideProgressModal(200), 500);
  } catch (err) {
    hideProgressModal(100);
    alert('GBA ROMの出力に失敗しました: ' + err.message);
  } finally {
    btnExportRom.disabled = false;
    btnExportRom.textContent = '📥 翻訳済みGBAを出力';
  }
});

btnExportIps.addEventListener('click', async () => {
  btnExportIps.disabled = true;
  btnExportIps.textContent = 'IPS生成中...';
  showProgressModal('📦 IPSパッチを出力中', 'テキスト注入と差分パッチを計算しています...');

  startProgressPolling();

  try {
    const resp = await fetch('/api/build_ips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!resp.ok) throw new Error('IPS generation failed');

    updateProgressModal({
      percentage: 100,
      detail: 'IPSパッチ完成！ダウンロードを開始します...',
      etaText: '完了',
    });

    const blob = await resp.blob();
    const filename = infoFilename.textContent.replace(/\.gba$/i, '') + '_JP.ips';
    downloadBlob(blob, filename);
    setTimeout(() => hideProgressModal(200), 500);
  } catch (err) {
    hideProgressModal(100);
    alert('IPSパッチの出力に失敗しました: ' + err.message);
  } finally {
    btnExportIps.disabled = false;
    btnExportIps.textContent = '📦 IPSパッチ出力';
  }
});

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// GBA Preview & Font Settings
// ---------------------------------------------------------------------------
function updateGbaPreview(text) {
  if (!text) return;
  // Replace newlines with <br>
  const formatted = escapeHtml(text).replace(/\n/g, '<br>');
  previewText.innerHTML = formatted;
}

charWidthRange.addEventListener('input', (e) => {
  charWidthVal.textContent = e.target.value;
});

btnToggleGlyphs.addEventListener('click', async () => {
  if (glyphGrid.style.display === 'none') {
    glyphGrid.style.display = 'grid';
    btnToggleGlyphs.textContent = '注入フォント一覧を閉じる';
    if (glyphGrid.children.length === 0) {
      loadGlyphPreview();
    }
  } else {
    glyphGrid.style.display = 'none';
    btnToggleGlyphs.textContent = '注入フォント一覧を表示';
  }
});

async function loadGlyphPreview() {
  try {
    const resp = await fetch('/api/font_preview');
    const data = await resp.json();
    glyphGrid.innerHTML = '';
    for (const [char, pattern] of Object.entries(data.kana)) {
      const tile = document.createElement('div');
      tile.className = 'glyph-tile';
      tile.textContent = char;
      tile.title = `Glyph: ${char}`;
      glyphGrid.appendChild(tile);
    }
  } catch (e) {}
}

// ---------------------------------------------------------------------------
// Utility Functions
// ---------------------------------------------------------------------------
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
