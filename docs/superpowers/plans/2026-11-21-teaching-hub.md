# Teaching Hub Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 在原 GitHub Pages 站点提供统一教学导航与可本地保存的笔试练习。
**Architecture:** 原生 HTML/CSS/JS；固定上游版本导入 JSON，Python 生成安全题面，浏览器按试卷加载并在本地判分与保存。
**Tech Stack:** Python 标准库与已有 markdown-it-py，原生浏览器 API，本地 KaTeX。
**Spec:** `docs/superpowers/specs/2026-11-21-teaching-hub-design.md`

## Global Constraints
- 保留已有 URL、Typora 正文与学生提交数据；不覆盖 `solutions/solutons.md`。
- 使用现有 checkout；不推送或发布，不引入框架，不提交凭据。
- 当前用户已批准设计并指示继续，直接在本会话实施，无需再次选择执行方式。
- 保留上游署名与来源；不将编程题视作可自动评分。

## Review Focus
- 多选顺序、判断布尔值及空答案：统一规范化，缺答案不自动判错。
- 试卷修订与损坏本地记录：版本隔离，忽略非法状态；存储失败不阻止作答。
- 限时刷新与超时：截止时间持久化，超时只能交卷一次。
- 题面中的代码、图片、HTML 与公式：转义危险内容，保留代码字段并校验本地资源。
- 原有课程和手机版：保留路由与矩阵数据逻辑，统一导航不溢出。

### Task 1: 题库导入
Files: `scripts/import_exams.py`, `tests/test_import_exams.py`, `exams/catalog.json`, `exams/papers/`, `exams/assets/`, `exams/SOURCES.md`。
Interfaces: `normalize_paper(raw, slug, revision)` 返回具有稳定 id、版本、questions、objective_score 的对象；题目保留上游字段并增加安全 HTML。
- [x] 先写并运行源数据规范化、安全渲染、无答案不计分与重复题号测试，观察缺失实现失败。
- [x] 实现固定版本导入、资源复制与报告，运行 Python unittest 验证。
- [x] 导入全部可解析试卷，记录分类、异常与来源；校验资源路径。

### Task 2: 答题与目录
Files: `exams.html`, `exams/practice.html`, `tests/exam-core.test.cjs`。
Interfaces: practice.html 内的 ExamCore 提供 `grade(paper, answers)`, `restore(paper, state)`, `remaining(deadline, now)`；目录读取 catalog，练习页读取 catalog 中校验过的路径。
- [x] 先编写 Node 测试：多选完全匹配、判断、填空、跳过编程/无答案、记录版本、计时；运行观察失败。
- [x] 实现按需加载、筛选分页、原生答题控件、答题卡、交卷结果、本地记录、错题与最高分。
- [x] 页面内 dialog 处理交卷与重做，明确评分口径与隐私限制；执行全部核心测试。

### Task 3: 主站统一
Files: `index.html`, `memos.html`, `memos/detail.html`, `favorite.html`, `templates.html`, `tools.html`, `assets/theme.css`, `assets/app.js`, `DESIGN.md`, `UX-CONTRACT.md`, `AGENTS.md`。
- [x] 依据批准方案更新共享主题与紧凑顶栏；所有主页面保留时钟、四个历史导航项和 footer。
- [x] 首页改为搜索、任务分组、真实最近更新；将试卷元数据并入搜索。
- [x] 保留课程、题解、模板和工具现有正文及事件处理，检查窄屏、主题与键盘操作。
- [x] 补充 `.gitignore` 凭据及缓存规则；保留本地 .env，不改写历史或隐式发布。

### Task 4: 验证与审阅
- [x] Python 与 Node 测试全绿；检查所有试卷目录、图片、内部链接、内联脚本语法。
- [x] 启动本地预览，使用浏览器核查桌面与手机、深浅主题及答题流程；失败则如实记录限制。
- [x] 独立代码审阅并修复实质问题；交付可预览的本地改动及维护说明。

## Progress / Rulings
- 使用当前 checkout，避免隔离 worktree 导致用户无法直接预览；不自动提交用户改动。
- 用户的继续指令涵盖既定方案的实施，不再增加技能中的重复批准流程。


## Completion evidence
- 161 papers / 4432 questions imported from the fixed commit; all rendered image paths checked locally.
- 6 Python normalization/security/math tests and 6 Node grading/state/timer tests passed.
- Browser regression passed on installed Edge: search, filters, pagination, all objective input types, persistence, dialog cancellation, highest score, timer expiration and cross-tab updates, themes, 390px mobile, storage failure, legacy routes.
- Whole-change independent review found three P2 issues (TeX emphasis, stale dialog returnValue, cross-tab state). Regressions reproduced; fixes applied; final suites green. No deferred review findings.
- DESIGN lint: zero errors; four orphaned documentation-token warnings (runtime CSS owns these roles).
- `.env` removed from Git index with local file preserved. No remote push or deployment performed. Existing user modification `solutions/solutons.md` untouched.
- Ruling: retain existing checkout and leave changes uncommitted for direct review; no worktree or automatic commits. Cost: changes share a checkout with the existing user edit; files remain separate.
- Ruling: preserve the upstream incomplete answers and inconsistent score totals. Fourteen questions are excluded from automatic grading; six paper-level notices make limitations visible. Cost: those questions need a later source correction to become gradable.
