# oi-solutions
信息学教学工具


## 教学入口与笔试练习（2026-11）

- 首页 `index.html`：课程、知识点、题解及试卷的统一搜索与分类入口。
- `exams.html`：161 份本地笔试试卷，可按比赛、级别、年份与关键词筛选。
- `exams/practice.html?paper=<id>`：自由/限时练习，客观题评分、草稿、答题记录、最高分与错题复习。记录仅保存在当前浏览器，编程题不自动评测。
- 原有课程、讲义、题解地址和学生提交矩阵继续保留。

本地预览：`python -m http.server 8765 --bind 127.0.0.1`，打开 `http://127.0.0.1:8765/`。

来源、许可声明、原始数据限制及更新方法见 [题库维护说明](exams/SOURCES.md)。设计与行为规范见 [DESIGN.md](DESIGN.md) 和 [UX-CONTRACT.md](UX-CONTRACT.md)。

`.env` 与下载缓存不应进入版本控制。本站的部署方式仍为原 GitHub Pages 流程，无新增运行时构建步骤。

## 讲义排版：算法实验笔记

Typora 导出到 `memos/` 后执行：

```powershell
python script.py polish all --dry-run
python script.py polish all
python script.py polish Lec-array-basics.html
```

增强层提供点阵笔记纸、荧光标题、章节页签、批注便签、桌面章节目录/手机折叠目录、深浅主题、提示与例题、代码复制/展开以及打印样式。保留 Typora 原始正文、公式、图片和高亮；可重复运行。代码块中的 `// @open 标题`、`// @fold 标题`、前置 `<!-- @open -->` 及文档级 `<!-- @open-all -->` 标记继续兼容。

主题与增强逻辑的唯一维护源是 `script.py` 中的 `LECTURE_THEME_CSS`、`_ENHANCE_JS_TEMPLATE`。修改后重新执行 polish，生成文件 `memos/lecture-theme.css`、`lecture-enhance.js` 无需手改。

验证：`python -m unittest discover -s tests -p test_lecture_polish.py`；本地 8765 预览服务器启动后可运行 `python tests/lectures_browser.py`（使用本机 Edge）。
