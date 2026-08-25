# 西安之行 v6：固定密码 + Supabase

这版已经删除邮箱 / Magic Link。

## 1. 先开启匿名登录
Supabase Dashboard → Authentication → Sign In / Providers → 开启 Anonymous Sign-Ins。

匿名登录不会要求邮箱；Supabase 会静默为每台设备创建匿名用户。匿名用户仍使用 authenticated role，因此现有 RLS 可以继续生效。

## 2. 设置你的固定密码
打开 `password_mode_migration.sql`，找到：

    crypt('xian2026',gen_salt('bf'))

把 `xian2026` 改成你自己的密码，然后把整个 SQL 放到 Supabase SQL Editor 运行。

不要把真正密码写入 app.js / config.js。

## 3. 部署 GitHub Pages
部署：
- index.html
- style.css
- app.js
- config.js

SQL 文件不用上传到网页目录也可以。

## 工作原理
网页后台先 `signInAnonymously()`，用户只看到一个“旅行密码”输入框。
数据库函数 `unlock_trip_by_password()` 用 bcrypt 验证密码；成功后才把当前匿名用户加入 `trip_members`。
之后日程、预约、美食仍由原 RLS 保护。

右上角“锁定页面”会要求当前标签页重新输入旅行密码。


## v6.1 修复

本版本修复：
- `pgcrypto` 明确安装到 `extensions` schema
- 密码验证使用 `extensions.crypt(...)`
- 登录失败时直接显示 Supabase 的真实错误，不再把所有错误都显示成“密码不正确”
- Anonymous Sign-In 会验证是否真的拿到了用户 session

### 已运行过旧 v6 SQL 怎么办？

直接重新运行新版 `password_mode_migration.sql` 即可。

注意：如果你已经把密码从 `xian2026` 改成了自己的密码，请在新版 SQL 中再次改成同一个密码后再运行。


## v7 准备清单
先在 Supabase SQL Editor 运行 `preparation_items_migration.sql`，再部署新版前端。准备清单支持新增、编辑、删除、勾选完成、分类筛选、完成进度和 Realtime 同步。
