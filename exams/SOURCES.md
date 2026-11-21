# 笔试题库来源与维护

原始整理者：远明老师。原站：<https://exam.yuanming.wang/>。

源码与试卷数据：<https://github.com/sirwym/olympiad-practice-system>。
本次固定版本：`aa1326aad53a790a58b670f0b1f3fc26802cee01`。

上游 README 标明 MIT；原文保存在 [UPSTREAM-README.md](UPSTREAM-README.md)。上游当前未提供独立 LICENSE，本站没有编造作者授权文件。试卷内容与图片的原始权利属于相应赛事、作者或来源方；本页面提供来源追溯，不宣称本站原创。来源标识和数据异常记录在 [import-report.json](import-report.json)，使用前可逐项核对并联系原作者补充授权说明。

本站新增的原生目录、练习界面、评分和本地记录实现独立于上游的 Tailwind 页面，未复制上游站点标识、统计和账号逻辑。编程题只显示题面及保存草稿，不提供自动评测；客观题参考答案可能存在整理误差，反馈时请带试卷名称和题号。

## 本地导入与更新

```powershell
python -m pip install --no-user --target .cache/exams/python -r scripts/requirements-exams.txt
python -u scripts/download_exams.py
python scripts/import_exams.py --archive .cache/exams/upstream.zip
python -m unittest discover -s tests -p test_import_exams.py
node --test tests/exam-core.test.cjs
python -m http.server 8765 --bind 127.0.0.1
```

下载器固定版本并缓存数据。更新时先在下载器中明确设置新的 commit，另存并审阅导入报告；不要盲目覆盖旧版。试卷 id 保留上游目录名，version 取原始 JSON 摘要，改变试卷内容后练习记录自动隔离。压缩包摘要、版本、分类数量和异常记录由导入器写入报告。缓存目录不提交。

数据 JSON 包含原始字段与经过安全 Markdown 转换的题面。缺少有效答案的题目不自动评分，重复显示题号使用独立内部 uid，原始答案不猜测修改。公式资源 KaTeX 0.16.11 随数据本地存储，遵循其 MIT 许可；完整许可见 [KATEX-LICENSE.txt](assets/KATEX-LICENSE.txt)。

本次校验发现 3 份试卷的原卷总分与题目分值合计不一致，另有 3 份试卷共 14 道题缺少有效答案。相关提示同时展示在试卷页面中；这部分数据保持原样，不猜测补齐。
