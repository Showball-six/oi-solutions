---
version: alpha
colors:
  primary: '#0284c7'
  background: '#ffffff'
  foreground: '#17212f'
  muted: '#536273'
  border: '#e5e9ef'
  subtle: '#f6f8fa'
typography:
  sans:
    fontFamily: "'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif"
    fontSize: 16px
    lineHeight: '1.7'
  mono:
    fontFamily: "Menlo, Consolas, 'Courier New', monospace"
rounded:
  surface: 8px
  control: 6px
spacing:
  page: 28px
  section: 32px
components:
  navigation:
    height: 68px
  reading:
    width: 1120px
---

# Showball OI

## Overview
面向中文信息学教学与复习的内容工具站。参考 CubeRoot 的任务分类与直接入口，首页搜索后即为学习、训练、常用三组链接。界面的特点是中文教学内容与试卷分类，避免大面积宣传区、装饰编号和统计大屏。2026-11-21 用户批准完整教学入口方案。

## Colors
运行时基础组件由 `assets/theme.css` 维护，教学入口的最终 token 及共享布局由 `assets/hub.css` 覆盖，同一份文件应用于所有本次修改的页面；禁止再逐页复制主题值。DESIGN.md 记录规范，CSS 为运行时实现。主色 `--brand-600` 天蓝，仅用于可操作链接与少量强调。

暗色：背景 #10151d，正文 #e5edf5，次要文字 #adbacb，边框 #2a3543，强调 #7dd3fc。语义色不随品牌替换：AC #52c41a，尝试 #fa8c16，无提交 #d9d9d9。洛谷难度按现有标准保留。

## Typography
中文无衬线与系统字体优先，无新增字体网络依赖。正文 16px，主要入口 15px，控件 14px，辅助信息 13px。代码使用等宽字体与独立滚动区域。题目数学使用本地 KaTeX；Typora 独立正文保持原样。

## Layout
紧凑顶栏、居中内容区，正文最大约 1120px。首页三列分类，760px 以下折成两列，460px 以下单列。练习页正文与答题卡双列，窄屏答题卡回到正文前方。顶栏窄屏显示导航开关；使用真实链接并保留所有历史 URL。

## Elevation & Depth
静态内容不加阴影，层级由文字、空白及细分隔线表达。搜索浮层与模态框允许遮罩及阴影，确保遮挡关系明确。

## Shapes
内容边界 8px 圆角，控件 6px，避免渐变和悬浮位移；触控目标至少约 38px，主要答题选项更高。

## Components
顶栏和四个历史导航项沿用 `.topbar/.nav-cards/.nav-card/.site-footer` 类名，新增笔试练习。当前项用 `aria-current`。时钟每秒更新，主题与菜单行为由 `assets/app.js` 负责。

筛选为带显式标签的原生 input/select，分页为 button；试卷及课程入口为 a。答题选项使用 radio/checkbox，代码与填空用 textarea。交卷和重做使用原生 dialog，由浏览器负责焦点约束，Escape 可取消。

## Do's and Don'ts
- 所有状态同时提供文字，颜色不能单独表达对错；焦点始终可见。
- 页面支持深浅主题、全局可操作滚动条与 reduced-motion。
- 不将编程草稿伪装成在线评测，不将本地练习成绩混入学生平台提交矩阵。
- 现有绿色占位页、天蓝侧栏与新顶栏的历史差异，在本次触及页面统一为此规范；不修改 Typora 及其他独立子站样式。
- 知识手册统一使用主站顶栏、主题和页脚。手册入口直接呈现第一章，章节目录折叠展示；不再增加独立首页、品牌侧栏和重复课程入口。阅读正文保留原公式、图片及代码。
- 页面不展示来源迁移文档、维护报告等面向维护者的入口；来源与许可文件在仓库中保留。必要的评分口径、答案缺失提示继续保留，帮助学生理解结果。

### 独立讲义：算法实验笔记

用户于 2026-11-21 反馈现代教材版本过于普通，改为更有趣的算法实验笔记。保留教材的阅读层级，以点阵底纹、白色笔记纸、标题荧光标记、章节页签、批注便签和代码实验卡片形成独立风格。装饰集中在结构和交互区，不给每段正文添加背景。

主色 #3569bd、正文 #23344a、纸面 #ffffff、背景 #f2f6fb、标题标记 #ffedaa；例题使用珊瑚色，提示使用薄荷绿，警告使用琥珀色，保持真实语义。暗色沿用深墨底与浅蓝强调，装饰降低对比度。

运行时由 `script.py` 内 `LECTURE_THEME_CSS` 和 `_ENHANCE_JS_TEMPLATE` 生成 `memos/lecture-theme.css`、`lecture-enhance.js`。正文 16px/1.95、主标题 34px、章标题 24px，纸面宽 848px；桌面目录在左侧，手机折叠。纯空白占位段在阅读时隐藏。原始正文、公式、图片和代码不改写。

打印白底 A4，隐藏点阵、标签装饰、目录和工具条，并展开折叠代码。`@open/@fold` 标记与默认展开阈值继续兼容。


讲义阅读页不设置顶部抬头栏。讲义不显示主题切换与打印控件；正文和目录按无顶栏的布局与锚点偏移定位。目录保留标题中渲染后的 Markdown 强调、行内代码、上下标与数学公式；内部链接扁平化，公式 SVG 定义及引用同步重命名，避免与正文 ID 冲突。异步公式渲染完成后更新对应目录项。
