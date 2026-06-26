(function () {
  // 1. 阅读进度条
  const bar = document.createElement('div');
  bar.id = 'lec-progress';
  document.body.prepend(bar);
  window.addEventListener('scroll', function () {
    const pct = window.scrollY / (document.body.scrollHeight - innerHeight) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  });

  // 2. Callout 检测
  const CALLOUT_MAP = [
    [/^(📌|重点|关键)/, 'lec-key'],
    [/^(💡|提示|tip)/i, 'lec-tip'],
    [/^(⚠️|注意|警告|warn)/i, 'lec-warn'],
    [/^(📝|例题|example)/i, 'lec-note'],
  ];
  document.querySelectorAll('#write blockquote, .typora-export blockquote').forEach(function (bq) {
    const text = bq.textContent.trim();
    for (const [re, cls] of CALLOUT_MAP) {
      if (re.test(text)) { bq.classList.add(cls); return; }
    }
    bq.classList.add('lec-tip');
  });

  // 3. 代码块：header bar（语言 + 展开 + 复制）
  document.querySelectorAll('#write pre, .typora-export pre').forEach(function (pre) {
    if (pre.closest('.CodeMirror')) return;

    const cmLines = pre.querySelectorAll('.CodeMirror-line');
    const cmCodeLines = pre.querySelectorAll('.CodeMirror-code pre');
    const isCM = cmLines.length > 0;
    const code = pre.querySelector('code');
    if (!isCM && !code) return;

    const langAttr = pre.getAttribute('lang');
    const langCls = code && Array.from(code.classList).find(function (c) { return c.startsWith('language-'); });
    const lang = langAttr || (langCls ? langCls.slice(9) : 'code');

    // Header bar
    const header = document.createElement('div');
    header.className = 'lec-code-header';

    const langLabel = document.createElement('span');
    langLabel.className = 'lec-lang-name';
    langLabel.textContent = lang;
    header.appendChild(langLabel);

    const actions = document.createElement('div');
    actions.className = 'lec-header-actions';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'lec-header-btn';
    toggleBtn.textContent = '▶ 展开代码';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'lec-header-btn';
    copyBtn.textContent = '复制';
    copyBtn.addEventListener('click', function () {
      const src = isCM ? cmCodeLines : null;
      const text = src && src.length
        ? Array.from(src).map(function (l) { return l.textContent.replace(/\u200b/g, '').replace(/\u00a0/g, ' '); }).join('\n')
        : code ? code.textContent : '';
      navigator.clipboard.writeText(text).then(function () {
        copyBtn.textContent = '已复制';
        setTimeout(function () { copyBtn.textContent = '复制'; }, 2000);
      });
    });

    actions.appendChild(toggleBtn);
    actions.appendChild(copyBtn);
    header.appendChild(actions);

    // 折叠容器（默认折叠）
    const inner = document.createElement('div');
    inner.className = 'lec-code-inner lec-collapsed';

    toggleBtn.addEventListener('click', function () {
      const isCollapsed = inner.classList.contains('lec-collapsed');
      inner.classList.toggle('lec-collapsed', !isCollapsed);
      inner.classList.toggle('lec-expanded', isCollapsed);
      toggleBtn.textContent = isCollapsed ? '▼ 收起代码' : '▶ 展开代码';
    });

    // 组装：先把 wrap 插入正确位置，再移动 pre
    const wrap = document.createElement('div');
    wrap.className = 'lec-code-wrap';
    wrap.appendChild(header);
    const parent = pre.parentNode;
    parent.insertBefore(wrap, pre); // wrap 占位（pre 仍在 parent 中）
    inner.appendChild(pre);         // pre 从 parent 移入 inner
    wrap.appendChild(inner);
  });
})();
