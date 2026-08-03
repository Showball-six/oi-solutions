// 本文件由 script.py polish 自动生成，请勿手改（改 script.py 里的 _ENHANCE_JS_TEMPLATE）
(function () {
  // 1. 阅读进度条
  const bar = document.createElement('div');
  bar.id = 'lec-progress';
  document.body.prepend(bar);
  window.addEventListener('scroll', function () {
    const pct = window.scrollY / (document.body.scrollHeight - innerHeight) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  });

  // 从开头的文本节点里删掉已变成标签/徽标的前缀，避免「注意」出现两次。
  // 前缀可能被 <span>/<strong>/<a> 拆成多个文本节点，所以要跨节点删。
  function stripPrefix(root, prefix) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node, left = prefix.length, leading = true;
    while (left > 0 && (node = walker.nextNode())) {
      const raw = node.nodeValue;
      let from = 0;
      if (leading) {
        // prefix 来自 textContent.trim()，开头的空白只跳过一次，不计入 left
        from = raw.length - raw.trimStart().length;
        if (from >= raw.length) continue;   // 整个节点都是空白 → 原样保留
        leading = false;
      }
      const take = Math.min(left, raw.length - from);
      node.nodeValue = raw.slice(0, from) + raw.slice(from + take);
      left -= take;
    }
    // 清掉残留的空白 / 冒号
    const w2 = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n2;
    while ((n2 = w2.nextNode())) {
      const cleaned = n2.nodeValue.replace(/^[\s:：，]+/, '');
      n2.nodeValue = cleaned;
      if (cleaned) break;   // 命中第一个有内容的文本节点即停
    }
  }

  // 2. h4「例题：xxx」→ 自动编号徽标（编号由 CSS counter 生成）
  //    必须在 blockquote 之前跑：有些例题 h4 被包在引用里，
  //    否则前缀会先被 callout 吃掉，h4 就认不出来了
  const EG_RE = /^(?:例题|例)\s*[:：]\s*/;
  document.querySelectorAll('#write h4').forEach(function (h) {
    const m = h.textContent.trim().match(EG_RE);
    if (!m) return;
    h.classList.add('lec-eg');
    stripPrefix(h, m[0]);
  });

  // 3. Callout 识别：命中前缀 → 上色 + 加标签并吃掉正文前缀；
  //    没命中 → 保持默认淡蓝定义卡，不加标签
  const CALLOUT_RULES = [
    [/^(?:(?:📌)\s*(?:(?:重点|核心|结论)\s*[:：，]?)?|(?:重点|核心|结论)\s*[:：，])\s*/i, "lec-key", "\u91cd\u70b9"],
    [/^(?:(?:💡)\s*(?:(?:提示|技巧|小贴士|tip)\s*[:：，]?)?|(?:提示|技巧|小贴士|tip)\s*[:：，])\s*/i, "lec-tip", "\u63d0\u793a"],
    [/^(?:(?:⚠️|⚠)\s*(?:(?:注意|警告|warn)\s*[:：，]?)?|(?:注意|警告|warn)\s*[:：，])\s*/i, "lec-warn", "\u6ce8\u610f"],
    [/^(?:(?:❌)\s*(?:(?:易错|坑点|误区)\s*[:：，]?)?|(?:易错|坑点|误区)\s*[:：，])\s*/i, "lec-pitfall", "\u6613\u9519"],
    [/^(?:(?:📝)\s*(?:(?:例题|举例|例如|例)\s*[:：，]?)?|(?:例题|举例|例如|例)\s*[:：，])\s*/i, "lec-example", "\u4f8b\u9898"],
    [/^(?:(?:🔍)\s*(?:(?:证明|分析|推导)\s*[:：，]?)?|(?:证明|分析|推导)\s*[:：，])\s*/i, "lec-example", "\u8bc1\u660e"],
    [/^(?:(?:📖)\s*(?:(?:定义|定理|性质)\s*[:：，]?)?|(?:定义|定理|性质)\s*[:：，])\s*/i, "", "\u5b9a\u4e49"]
  ];
  document.querySelectorAll('#write blockquote, .typora-export blockquote').forEach(function (bq) {
    // 引用整体就是一道例题（首个子元素是例题 h4）→ 只上靛蓝色，
    // 标签交给 h4 徽标，避免「例题」出现两次
    const firstEl = bq.firstElementChild;
    if (firstEl && firstEl.tagName === 'H4' && firstEl.classList.contains('lec-eg')) {
      bq.classList.add('lec-example');
      return;
    }
    const text = bq.textContent.trim();
    for (let i = 0; i < CALLOUT_RULES.length; i++) {
      const re = CALLOUT_RULES[i][0], cls = CALLOUT_RULES[i][1], label = CALLOUT_RULES[i][2];
      const m = text.match(re);
      if (!m) continue;
      if (cls) bq.classList.add(cls);
      bq.setAttribute('data-lec-label', label);
      stripPrefix(bq, m[0]);
      return;
    }
  });

  // 4. 代码块：header bar（语言 + 展开 + 复制）
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
        ? Array.from(src).map(function (l) { return l.textContent.replace(/​/g, '').replace(/ /g, ' '); }).join('\n')
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

  // 4. 动画演示卡片 iframe：撑开内部高度上限并自适应
  document.querySelectorAll('.lec-demo iframe').forEach(function (frame) {
    const fallback = parseInt(frame.getAttribute('data-height'), 10) || 640;
    frame.style.height = fallback + 'px';

    function fit() {
      // 同源才能读 contentDocument；file:// 下 Chrome 会抛错，保持 fallback 高度
      let doc;
      try {
        doc = frame.contentDocument;
        if (!doc || !doc.body) return;
      } catch (e) { return; }

      const app = doc.querySelector('.app') || doc.body;
      // 解除演示页自身的 60vh / max-height 限制，让内容完整展开
      app.style.height = 'auto';
      app.style.maxHeight = 'none';
      app.style.minHeight = '0';
      app.style.overflowY = 'visible';
      doc.documentElement.style.minHeight = '0';
      doc.body.style.minHeight = '0';

      const h = Math.ceil(app.getBoundingClientRect().height) + 24;
      if (Math.abs(h - parseInt(frame.style.height, 10)) > 2) {
        frame.style.height = h + 'px';
      }
    }

    frame.addEventListener('load', function () {
      fit();
      let doc;
      try { doc = frame.contentDocument; } catch (e) { return; }
      if (!doc || !doc.body || typeof ResizeObserver === 'undefined') return;
      // 演示过程中素数列表会变长 → 跟随重算
      new ResizeObserver(fit).observe(doc.querySelector('.app') || doc.body);
    });

    if (frame.contentDocument && frame.contentDocument.readyState === 'complete') fit();
    window.addEventListener('resize', fit);
  });
})();
