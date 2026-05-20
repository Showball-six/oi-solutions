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
- `diff`: 严格使用洛谷难度标签（见下方列表）
- `tags`: 字符串数组，每项用顿号分隔多个标签
- `href`: 相对路径，指向 `solutions/` 下的 HTML 文件

**洛谷难度标签（有序）**:
入门 / 普及- / 普及/提高- / 普及+/提高 / 提高+/省选- / 省选/NOI- / NOI/NOI+/CTSC

### memos/lectures.json

```json
[
  {
    "id": "lec-001",
    "title": "AC自动机",
    "date": "2026-05-13",
    "topics": ["字符串"],
    "file": "memos/lec-001.html"
  }
]
```

- `id`: 格式 `lec-NNN`（三位零填充）
- `topics`: 对应 courses.json 中的 topic id 数组

### students/students.json

```json
[
  {
    "id": "stu-001",
    "name": "Showball",
    "luogu_uid": "728487",
    "codeforces_handle": "Showball",
    "atcoder_handle": "Showball"
  }
]
```

- `id`: 格式 `stu-NNN`（三位零填充）
- 未注册的平台留空字符串 `""`

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
    { "id": "wp-001", "name": "2024 CSP-J 初赛", "href": "memos/written-cspj-2024.html" }
  ]
}
```
- `problems[].id`：格式 `wp-NNN`，由 script.py 自动生成
- `problems[].href`：相对于项目根目录的讲解 HTML 路径
- 页面展示：讲义列表 + 笔试题目列表（含「详细讲解」按钮）+ 学生完成情况矩阵

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
  }
}
```
- `scores`：手动录入，key 为 student id，value 为 `{pid: 分数}` 映射
- 页面展示：题目列表 + 按总分降序排名表 + 补题情况矩阵（从 submissions.json 读取）

### 支持的比赛类型

`GESP` / `CSP-J` / `CSP-S` / `NOIP` / `粤港澳大湾区信息学` / `南海区信息学`

---

## UI / 前端风格

### 整体风格

- **纯原生 HTML + CSS + JS**，无任何前端框架（无 Vue/React/Tailwind）
- 所有页面共享同一套内联样式（`<style>` 块直接写在 `<head>` 内）
- 字体：`'PingFang SC', 'Microsoft YaHei', sans-serif`
- 背景色：`#f5f7fa`（浅灰）；卡片/容器背景：`#ffffff`

### 页面结构（每个主页面都有）

```html
<!-- 顶栏 -->
<div class="topbar">
  <div class="topbar-left">
    <a href="..."><img src="tx.jpg" ...></a>  <!-- logo -->
    <span class="site-title">...</span>
  </div>
  <div class="topbar-right">
    <span id="clock"></span>  <!-- 实时时钟 -->
  </div>
</div>

<!-- 导航卡片组 -->
<div class="nav-cards">
  <a class="nav-card active" href="index.html">做题记录</a>
  <a class="nav-card" href="memos.html">课程</a>
  <a class="nav-card" href="templates.html">模板</a>
  <a class="nav-card" href="tools.html">小工具</a>
</div>

<!-- 主内容 -->
<div class="container">...</div>

<!-- 页脚 -->
<div class="footer">2026 © Showball's OI 工具箱</div>
```

### 颜色系统

**难度颜色**（对应洛谷配色）：

| 难度 | CSS 类 | 颜色 |
|---|---|---|
| 入门 | `.diff-intro` | `#fe4c61` |
| 普及- | `.diff-easy` | `#f39c11` |
| 普及/提高- | `.diff-normal` | `#ffc116` |
| 普及+/提高 | `.diff-hard` | `#52c41a` |
| 提高+/省选- | `.diff-harder` | `#3498db` |
| 省选/NOI- | `.diff-expert` | `#9d3dcf` |
| NOI/NOI+/CTSC | `.diff-master` | `#0e1d69` |

**学生提交状态点**（detail.html 矩阵）：

| 状态 | 颜色 |
|---|---|
| AC（通过） | `#52c41a`（绿） |
| 已尝试（未AC） | `#f39c11`（橙） |
| 未提交 | `#e0e0e0`（灰） |

### 组件样式规范

**卡片**：
```css
border-radius: 12px;
box-shadow: 0 2px 8px rgba(0,0,0,0.08);
padding: 20px 24px;
```

**按钮/导航卡片激活状态**：
```css
background: #4a9eff;
color: white;
border-radius: 8px;
```

**表格**：无边框，行 hover 背景 `#f0f7ff`，`border-radius: 12px` 包裹容器

**标签（tag）**：
```css
background: #eef2ff;
color: #4a6fa5;
border-radius: 4px;
font-size: 12px;
padding: 2px 8px;
```

### 实时时钟

每个主页面的顶栏右侧都有实时时钟，固定格式：

```js
function tick() {
  const now = new Date();
  document.getElementById('clock').textContent =
    now.toLocaleTimeString('zh-CN', { hour12: false });
}
setInterval(tick, 1000);
tick();
```

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
