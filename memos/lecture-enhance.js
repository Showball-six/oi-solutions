(function () {
  // 1. 阅读进度条
  const bar = document.createElement('div');
  bar.id = 'lec-progress';
  document.body.prepend(bar);
  window.addEventListener('scroll', function () {
    const pct = window.scrollY / (document.body.scrollHeight - innerHeight) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  });

  // 2. Callout 检测：blockquote 首字符匹配
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
    bq.classList.add('lec-tip'); // 默认
  });

  // 3. 代码块：语言 badge + 复制按钮
  document.querySelectorAll('#write pre, .typora-export pre').forEach(function (pre) {
    const code = pre.querySelector('code');
    if (!code) return;

    const lang = Array.from(code.classList).find(function (c) { return c.startsWith('language-'); });
    if (lang) {
      const badge = document.createElement('span');
      badge.className = 'lec-lang-badge';
      badge.textContent = lang.slice(9);
      pre.appendChild(badge);
    }

    const btn = document.createElement('button');
    btn.className = 'lec-copy-btn';
    btn.textContent = '复制';
    btn.addEventListener('click', function () {
      navigator.clipboard.writeText(code.innerText).then(function () {
        btn.textContent = '已复制';
        btn.classList.add('copied');
        setTimeout(function () { btn.textContent = '复制'; btn.classList.remove('copied'); }, 2000);
      });
    });
    pre.appendChild(btn);
  });
})();
