# 信息学竞赛知识手册


## 主站阅读入口

手册卡片直接显示第一章正文，章节地址保持不变。所有阅读、搜索及标签页面使用主站导航与主题，不另设专栏首页。NOIP 与 CSP-S 共用的章节仅保留一个主入口。

更新静态导出后运行 `python scripts/unify_handbook.py`。脚本优先读取新导出的课程目录，重复执行时使用 `assets/books.json`，不会重复插入导航。回归：`python -m unittest discover -s tests -p test_handbook_import.py` 与 `python tests/handbook_browser.py`。
