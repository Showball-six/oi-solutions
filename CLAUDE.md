# CLAUDE.md — oi-solutions

## 项目概览

**项目地址**: D:/oi-solutions  
**线上域名**: showball.ac.cn (GitHub Pages)  
**定位**: 信息学教学工具站，面向 OI 竞赛教学，记录做题解析、课程讲义、学生练习进度。

### 目录结构

```
oi-solutions/
├── index.html            # 做题记录主页（读 solutions/records.json）
├── memos.html            # 课程/知识点导航页
├── templates.html        # 模板页（建设中占位）
├── tools.html            # 小工具页（建设中占位）
├── script.py             # 本地 CLI 管理工具
├── tx.jpg                # 站点 logo
├── solutions/
│   ├── records.json      # 所有做题记录（主数据源）
│   └── *.html            # Typora 导出的题解 HTML
├── memos/
│   ├── courses.json      # 课程与知识点定义
│   ├── lectures.json     # 讲义元数据
│   ├── detail.html       # 动态详情页（course/topic/content 三模式）
│   ├── lec-*.html        # Typora 导出的讲义 HTML
│   └── img/              # SVG/PNG 图表资源
└── students/
    ├── students.json     # 学生账号信息
    └── submissions.json  # GitHub Actions 每小时自动更新的提交状态
```

---

## 数据格式

### solutions/records.json

```json
[
  {
    "id": "001",
    "pid": "CF1342F",
    "title": "Make It Ascending",
    "source": "CF",
    "href": "solutions/cf1342f.html",
    "diff": "省选/NOI-",
    "tags": ["状压DP，状态合并"],
    "problemUrl": "https://www.luogu.com.cn/problem/CF1342F"
  }
]
```

- `id`: 三位零填充顺序编号，递增
- `source`: 平台标识，值为 `"CF"` / `"洛谷"` / `"AtCoder"`
- `diff`: 严格使用洛谷难度标签（见下方列表），否则前端 `difficultyClassMap` 匹配不到颜色 class，会回退为「未评定」灰色
- `tags`: 字符串数组（注意：现有数据里每个元素内部用中文顿号「，」把多个标签拼在一个字符串里，而非拆成多个数组项）
- `href`: 相对路径，指向 `solutions/` 下的 HTML 文件
- `problemUrl`: 可选。若缺省，前端 `buildRow`（index.html）会根据 `source`/`pid` 自动推导洛谷/CF/AtCoder 链接

**洛谷难度标签（有序，需与 index.html 的 `difficultyRank` / `difficultyClassMap` 完全一致）**:
入门 / 普及- / 普及/提高- / 普及+/提高 / 提高+/省选- / 省选/NOI- / NOI（另有「未评定」作为兜底）

### memos/lectures.json

```json
[
  {
    "id": "lec-001",
    "slug": "lec-001",
    "title": "AC自动机",
    "tags": ["ACAM"],
    "courses": ["algo-improve"],
    "topics": ["string"],
    "href": "memos/lec-001.html",
    "created": "2026-05-13"
  }
]
```

- `id` / `slug`: 格式 `lec-NNN`（三位零填充），由 script.py 自动生成；slug 决定 HTML 文件名
- `courses`: 所属课程 id 数组（对应 courses.json 中的 course id）
- `topics`: 所属知识点 id 数组（对应 courses.json 中的 topic id，如 `dp/string/math`）
- `href`: 相对项目根目录的 HTML 路径
- `created`: 创建日期 `YYYY-MM-DD`

### students/students.json

```json
[
  {
    "id": "stu-001",
    "name": "海老师",
    "luogu_uid": "728487",
    "codeforces_handle": "5h0wba11",
    "atcoder_handle": "Showball"
  }
]
```

- `id`: 格式 `stu-NNN`（三位零填充）
- 未注册的平台字段值为 `null`（script.py 用 `input() or None` 生成），fetch-submissions 会跳过为 null 的平台

---

## CLI 工具（script.py）

所有命令均在项目根目录下执行：

```bash
python script.py <command>
```

| 命令 | 作用 |
|---|---|
| `create` | 交互式新增做题记录 + 生成 HTML 题解模板 |
| `list` | 打印所有做题记录 |
| `add-lecture` | 新增讲义条目到 lectures.json + 生成 HTML 模板 |
| `add-content` | 为课程新增内容块（含讲义 + 练习题） |
| `add-problem` | 向已有内容块追加练习题 |
| `add-student` | 新增学生账号 |
| `fetch-submissions` | 拉取 Luogu/CF/AtCoder 提交状态，更新 submissions.json |
| `init` | 写入两条样例记录初始化 records.json |
| `add-written` | 添加笔试专题（选比赛类型、关联讲义、添加笔试题目） |
| `add-written-problem` | 向已有笔试专题追加笔试题目 |
| `add-mock` | 添加上机模拟赛（选比赛类型、添加题目及满分） |
| `set-scores` | 交互式录入模拟赛分数（逐学生逐题输入） |

---

## 竞赛备赛专项课程

入口：`memos.html` → 点击「竞赛备赛专项课程」→ `memos/detail.html?type=course&id=contest-prep`

### 两种内容类型

**笔试专题**（`type: "written"`）：
```json
{
  "id": "written-001",
  "type": "written",
  "contest": "CSP-J",
  "title": "CSP-J 笔试专题",
  "lectures": ["lec-010"],
  "problems": [
    { "id": "wp-001", "name": "2024 CSP-J 初赛", "url": "https://..." }
  ]
}
```
- `problems[].id`：格式 `wp-NNN`，由 script.py 自动生成
- `problems[].url`：外部比赛/题目链接（detail.html 读取的是 `p.url`，以 `target="_blank"` 打开，**不是** `href`）
- 页面展示：讲义列表 + 笔试题目列表（含「查看题目 →」按钮）+ 学生完成情况矩阵

**上机模拟赛**（`type: "mock"`）：
```json
{
  "id": "mock-001",
  "type": "mock",
  "contest": "CSP-J",
  "title": "CSP-J 模拟赛 #1",
  "problems": [
    { "pid": "P1001", "platform": "luogu", "title": "A+B Problem", "full_score": 100 }
  ],
  "scores": {
    "stu-001": { "P1001": 100 },
    "stu-002": { "P1001": 80 }
  },
  "participants": ["stu-003", "stu-004"]
}
```
- `scores`：由 `set-scores` 手动录入，key 为 student id，value 为 `{pid: 分数}` 映射
- `participants`：参赛学生 id 数组；**为空数组时表示全员参与**（detail.html 据此过滤排名表）
- `problems[].href`：可选，指向本地题解 HTML
- 页面展示：题目列表 + 按总分降序排名表（含奖牌）+ 补题情况矩阵（从 submissions.json 读取）；同一 contest 下有多场 mock 时，分区页还会用手写 SVG 画总分趋势折线图

### 支持的比赛类型

`GESP` / `CSP-J` / `CSP-S` / `NOIP` / `粤港澳大湾区信息学` / `南海区信息学`

---

## UI / 前端风格

### 整体风格

- **纯原生 HTML + CSS + JS**，无任何前端框架（无 Vue/React/Tailwind）
- 每个页面在 `<head>` 内内联自己的 `<style>`，**没有共享样式表**——设计 token 通过一组 CSS 变量在各页面间复制粘贴，改主题需逐页同步
- 字体变量 `--font: 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif`（从 Google Fonts 引入 Noto Sans SC）
- 等宽字体变量 `--mono: 'Menlo','Consolas','Courier New', monospace`

### 核心 CSS 变量（绿色主题）

```css
--green:#52C41A; --green-light:#f0fbe8; --green-dark:#3da613;  /* 主色 */
--blue:#3498db;  --blue-light:#ebf5fb;
--orange:#e67e22;--orange-light:#fef5e7;
--purple:#9d3dcf;--purple-light:#f5eefa;
--bg:#f4f5f7; --white:#fff; --text:#1a1a1a;
--text-sub:#8e8e93; --text-light:#b0b0b6; --border:#e8eaed;
--radius:10px;
--shadow-sm:0 1px 3px rgba(0,0,0,.04),0 1px 2px rgba(0,0,0,.06);
--shadow-md:0 4px 12px rgba(0,0,0,.08);
```

### 页面骨架（index.html / memos.html / detail.html 共用）

```html
<header class="topbar">
  <div class="topbar-inner">
    <a class="logo"><div class="logo-icon"><img src="tx.jpg"></div><span>Showball's OI 工具箱</span></a>
    <span class="topbar-time" id="clock"></span>   <!-- 实时时钟 -->
  </div>
</header>
<div class="container">
  <div class="nav-cards"> … 四个 .nav-card：做题记录/课程/模板/小工具 … </div>
  …主内容…
</div>
<footer class="site-footer">2026 &copy; Showball's OI 工具箱</footer>
```

> 注意：实际类名是 `.topbar/.topbar-inner/.logo/.nav-cards/.nav-card/.site-footer`，导航卡片**没有** `.active` 高亮态。

### 难度颜色（index.html 中的 `.diff-*` class，对应洛谷配色）

| 难度 | CSS 类 | 颜色 |
|---|---|---|
| 入门 | `.diff-beginner` | `#FE4C61` |
| 普及- | `.diff-basic-minus` | `#F39C11` |
| 普及/提高- | `.diff-basic-improve-minus` | `#FFC116` |
| 普及+/提高 | `.diff-basic-improve` | `#52C41A` |
| 提高+/省选- | `.diff-improve-province-minus` | `#3498DB` |
| 省选/NOI- | `.diff-province-noi-minus` | `#9D3DCF` |
| NOI | `.diff-noi` | `#0E1D69` |
| 未评定（兜底） | `.diff-unrated` | `#BFBFBF` |

难度名 → class 的映射写在 index.html 的 `difficultyClassMap` 中；新增难度需同时更新 CSS、`difficultyClassMap`、`difficultyRank`。

### 学生提交状态点（detail.html 完成矩阵）

| 状态 | class | 颜色 |
|---|---|---|
| AC（通过） | `.status-ac` | `#52c41a`（绿） |
| 已尝试（未AC） | `.status-attempted` | `#fa8c16`（橙） |
| 未提交 | `.status-none` | `#d9d9d9`（灰） |

### 实时时钟

各主页面顶栏右侧 `#clock`，用自调用的 `tick()` 每秒刷新，格式 `YYYY-MM-DD HH:MM:SS`（手动 zero-pad，非 `toLocaleTimeString`）。

---

## 题解 / 讲义 HTML 格式

题解和讲义均为 **Typora 导出的独立 HTML 文件**，包含：

- 完整的 Typora CSS（内联在 `<style>` 中）
- KaTeX 或 MathJax 用于数学公式渲染
- CodeMirror 风格代码高亮
- 图片资源使用相对路径（讲义图片放在 `memos/img/`）

新建题解 HTML 时，使用 `script.py create` 命令生成 stub 模板，再用 Typora 编辑 Markdown 后导出覆盖该文件。

**命名规则**：
- 题解：`solutions/{pid_lowercase}.html`（如 `cf1342f.html`、`p2322.html`）
- 讲义：`memos/lec-{NNN}.html`（如 `lec-001.html`）

---

## 自动化（GitHub Actions）

`.github/workflows/update-submissions.yml`：
- 触发：每小时整点（`cron: '0 * * * *'`）+ 手动触发
- 行为：运行 `python script.py fetch-submissions`，如有变更则提交 `students/submissions.json`
- `.gitattributes` 设置 `students/submissions.json merge=ours` 防止合并冲突

本地运行 `fetch-submissions` 需要 `.env` 文件中的 Luogu cookie（不提交到 git）。

---

## 开发注意事项

1. **不引入外部框架**：保持纯 HTML/CSS/JS，所有逻辑内联在页面 `<script>` 中
2. **新增页面必须包含**：topbar（含实时时钟）、nav-cards（四个导航项）、footer
3. **难度标签必须精确匹配**洛谷标准值，否则颜色 class 不生效
4. **records.json 的 id 字段**必须手动保持递增，`script.py create` 会自动处理
5. **题解 HTML 由 Typora 生成**，不手动维护其内部 CSS
6. `students/submissions.json` 由 CI 自动更新，本地不需要手动编辑
7. `.env` 包含敏感 cookie，确保在 `.gitignore` 中排除（当前项目需确认）
