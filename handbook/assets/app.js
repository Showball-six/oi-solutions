(() => {
  'use strict';
  const root = document.body.dataset.root || './';
  const themeButton = document.querySelector('button[data-theme]');
  function updateThemeLabel() {
    const dark = document.documentElement.dataset.theme === 'dark';
    themeButton?.setAttribute('aria-label', dark ? '切换到浅色模式' : '切换到深色模式');
    if (themeButton) themeButton.textContent = dark ? '☼' : '◐';
  }
  themeButton?.addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('showball-theme', theme); } catch (_) {}
    updateThemeLabel();
  });
  updateThemeLabel();
  const menu = document.querySelector('.mobile-dialog');
  document.querySelector('[data-menu-open]')?.addEventListener('click', () => menu.showModal());
  document.querySelector('[data-menu-close]')?.addEventListener('click', () => menu.close());
  menu?.addEventListener('click', e => { if (e.target === menu && e.offsetX > menu.clientWidth) menu.close(); });
  document.addEventListener('keydown', e => {
    if (e.key === '/' && !e.isComposing && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName) && !document.activeElement?.isContentEditable) {
      e.preventDefault();
      const input = document.querySelector('#search-input') || document.querySelector('.hero-search input');
      if (input) input.focus(); else location.href = root + 'search/index.html';
    }
  });
  let toastTimer;
  function toast(text) {
    const status = document.querySelector('.toast');
    status.textContent = text; status.classList.add('visible');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => status.classList.remove('visible'), 2500);
  }
  document.querySelectorAll('.prose pre').forEach(pre => {
    let wrap = pre.closest('[class*=codeBlockContainer]');
    if (!wrap) { wrap = document.createElement('div'); wrap.className = 'codeBlockContainer'; pre.before(wrap); wrap.append(pre); }
    const button = document.createElement('button'); button.type = 'button'; button.className = 'copy-code'; button.textContent = '复制'; button.setAttribute('aria-label', '复制代码');
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText((pre.querySelector('code') || pre).innerText); toast('代码已复制'); }
      catch (_) { toast('无法访问剪贴板，请选中代码手动复制'); }
    });
    wrap.append(button);
  });
  const heroInput = document.querySelector('.hero-search input');
  if (heroInput) {
    const clear = document.createElement('button'); clear.type = 'button'; clear.textContent = '×'; clear.setAttribute('aria-label', '清空搜索'); clear.hidden = true;
    heroInput.after(clear); heroInput.addEventListener('input', () => { clear.hidden = !heroInput.value; });
    clear.addEventListener('click', () => { heroInput.value = ''; clear.hidden = true; heroInput.focus(); });
  }
  const form = document.querySelector('#search-form');
  if (!form) return;
  const input = document.querySelector('#search-input');
  const clear = document.querySelector('#clear-search');
  const status = document.querySelector('#search-status');
  const results = document.querySelector('#search-results');
  const more = document.querySelector('#search-more');
  let indexPromise = null, matches = [], count = 0, serial = 0, timer, composing = false, currentQuery = '';
  const normalize = value => value.normalize('NFKC').toLocaleLowerCase('zh-CN');
  async function loadIndex() {
    if (!indexPromise) indexPromise = fetch(root + 'assets/search-index.json').then(r => { if (!r.ok) throw new Error('index'); return r.json(); }).then(rows => rows.map(row => ({ ...row, haystack: normalize(row.title + ' ' + row.heading + ' ' + row.text), normalizedTitle: normalize(row.title + ' ' + row.heading) }))).catch(err => { indexPromise = null; throw err; });
    return indexPromise;
  }
  function highlighted(node, text, query) {
    const lower = text.toLocaleLowerCase('zh-CN'), needle = query.toLocaleLowerCase('zh-CN');
    let start = 0, pos;
    while (needle && (pos = lower.indexOf(needle, start)) !== -1) {
      node.append(document.createTextNode(text.slice(start, pos)));
      const mark = document.createElement('mark'); mark.textContent = text.slice(pos, pos + query.length); node.append(mark); start = pos + query.length;
    }
    node.append(document.createTextNode(text.slice(start)));
  }
  function renderMore() {
    const next = matches.slice(count, count + 20);
    next.forEach(row => {
      const link = document.createElement('a'); link.className = 'search-result'; link.href = root + row.url;
      const group = document.createElement('span'); group.className = 'result-category'; group.textContent = row.group + ' / ' + row.title;
      const h = document.createElement('h2'); highlighted(h, row.heading, currentQuery);
      const p = document.createElement('p'); const pos = row.text.toLocaleLowerCase('zh-CN').indexOf(currentQuery.toLocaleLowerCase('zh-CN')); const start = Math.max(0, pos - 50);
      const excerpt = (start ? '…' : '') + row.text.slice(start, start + 180) + (row.text.length > start + 180 ? '…' : ''); highlighted(p, excerpt, currentQuery);
      link.append(group, h, p); results.append(link);
    });
    count += next.length; more.hidden = count >= matches.length;
    status.textContent = `找到 ${matches.length} 个相关知识段落，已显示 ${count} 个`;
  }
  function empty(text, help) {
    const box = document.createElement('div'); box.className = 'search-empty'; const p = document.createElement('p'); p.textContent = text; box.append(p);
    if (help) { const detail = document.createElement('small'); detail.textContent = help; box.append(detail); }
    results.append(box);
  }
  async function run() {
    clearTimeout(timer); const token = ++serial; const query = input.value.trim(); currentQuery = query;
    clear.hidden = !input.value; results.replaceChildren(); more.hidden = true; count = 0;
    const url = new URL(location.href); if (query) url.searchParams.set('q', query); else url.searchParams.delete('q'); history.replaceState(null, '', url);
    if (!query) { status.textContent = '输入关键词开始搜索'; empty('你想了解哪个知识点？', '试试“二分”“动态规划”或“数组”。'); return; }
    status.textContent = '正在加载全文索引…';
    try {
      const rows = await loadIndex(); if (token !== serial) return;
      const terms = normalize(query).split(/\s+/).filter(Boolean);
      matches = rows.filter(row => terms.every(term => row.haystack.includes(term))).map(row => ({ ...row, score: terms.reduce((score, term) => score + (row.normalizedTitle.includes(term) ? 10 : 0), 0) })).sort((a, b) => b.score - a.score);
      if (!matches.length) { status.textContent = '没有找到匹配内容'; empty('换个关键词再试试', '可以减少关键词，或从“全部课程”按章节查找。'); return; }
      renderMore();
    } catch (_) {
      if (token !== serial) return;
      status.textContent = '全文索引加载失败'; empty('暂时无法读取搜索索引', '请确认站点文件已完整部署；也可以直接浏览课程目录。');
      const retry = document.createElement('button'); retry.type = 'button'; retry.className = 'secondary-button'; retry.textContent = '重新加载'; retry.addEventListener('click', run); results.append(retry);
    }
  }
  input.value = new URLSearchParams(location.search).get('q') || '';
  form.addEventListener('submit', e => { e.preventDefault(); if (!composing) run(); });
  input.addEventListener('compositionstart', () => { composing = true; clearTimeout(timer); ++serial; });
  input.addEventListener('compositionend', () => { composing = false; run(); });
  input.addEventListener('input', () => { clear.hidden = !input.value; ++serial; clearTimeout(timer); if (!composing) timer = setTimeout(run, 180); });
  clear.addEventListener('click', () => { input.value = ''; run(); input.focus(); });
  more.addEventListener('click', renderMore);
  window.addEventListener('popstate', () => { input.value = new URLSearchParams(location.search).get('q') || ''; run(); });
  run();
})();
