#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OI 工具箱 - 数据管理辅助脚本
使用方法：
  python3 script.py create              # 添加题解
  python3 script.py list                # 列出题解
  python3 script.py add-lecture         # 添加讲义
  python3 script.py add-course-problem  # 向课程添加练习题
  python3 script.py add-student         # 添加学生
  python3 script.py fetch-submissions   # 爬取提交记录（供 GitHub Actions 调用）
  python3 script.py init                # 初始化示例数据
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

try:
    from prompt_toolkit import prompt as _pt_prompt
    from prompt_toolkit.completion import WordCompleter
    _PT = True
except ImportError:
    _PT = False


def ask(msg, completions=None, default=''):
    """input() with optional Tab completion."""
    if _PT and completions:
        c = WordCompleter(completions, ignore_case=True, sentence=True)
        try:
            return _pt_prompt(msg, completer=c).strip()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit
    try:
        return input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit


def select(items, prompt_text='选择: ', label_fn=None):
    """
    Show numbered list, return chosen item.
    Accepts a number OR Tab-complete on item labels.
    Returns None on invalid input.
    """
    labels = [label_fn(x) if label_fn else str(x) for x in items]
    if _PT:
        completions = [f"{i+1}. {l}" for i, l in enumerate(labels)] + labels
        c = WordCompleter(completions, ignore_case=True, sentence=True)
        try:
            raw = _pt_prompt(prompt_text, completer=c).strip()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit
    else:
        try:
            raw = input(prompt_text).strip()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit

    # numeric input
    if raw.isdigit():
        idx = int(raw) - 1
        return items[idx] if 0 <= idx < len(items) else None
    # label match (strip leading "N. " if present)
    clean = raw.split('. ', 1)[-1].strip() if '. ' in raw else raw
    for i, l in enumerate(labels):
        if l == clean:
            return items[i]
    return None

SOLUTIONS_DIR = Path("solutions")
RECORDS_FILE  = SOLUTIONS_DIR / "records.json"
MEMOS_DIR     = Path("memos")
COURSES_FILE  = MEMOS_DIR / "courses.json"
LECTURES_FILE = MEMOS_DIR / "lectures.json"
STUDENTS_DIR  = Path("students")
STUDENTS_FILE = STUDENTS_DIR / "students.json"
SUBS_FILE     = STUDENTS_DIR / "submissions.json"

SOLUTIONS_DIR.mkdir(exist_ok=True)
MEMOS_DIR.mkdir(exist_ok=True)
STUDENTS_DIR.mkdir(exist_ok=True)

COURSE_IDS = ["syntax-basics", "algo-basics", "basics-to-improve", "algo-improve", "contest-prep"]
TOPIC_IDS  = ["dp", "basic-algo", "ds", "math", "graph", "misc", "string"]
CONTEST_TYPES = ["GESP", "CSP-J", "CSP-S", "NOIP", "粤港澳大湾区信息学", "南海区信息学"]


def load_json(path, default=None):
    p = Path(path)
    if p.exists():
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法加载 {path}: {e}")
    return default if default is not None else {}


def save_json(path, data):
    with open(Path(path), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def load_existing_records():
    """从 records.json 加载所有记录（单一数据源）"""
    if RECORDS_FILE.exists():
        try:
            with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
                records = json.load(f)
                # 确保是列表
                if isinstance(records, list):
                    return sorted(records, key=lambda x: int(x.get('id', 0)))
                else:
                    print(f"⚠️ {RECORDS_FILE} 格式错误，已重置为空")
                    return []
        except Exception as e:
            print(f"⚠️ 无法加载 {RECORDS_FILE}: {e}")
            return []
    return []


def get_next_id(records):
    """获取下一个ID"""
    if not records:
        return "001"
    max_id = max(int(r.get('id', 0)) for r in records)
    return str(max_id + 1).zfill(3)


def create_json_record(pid, title, diff, source="洛谷", tags=None, problem_url=None):
    """创建一条记录"""
    records = load_existing_records()
    next_id = get_next_id(records)

    # 只生成 HTML 文件路径
    filename_base = pid.lower().replace(' ', '_')
    html_file = f"solutions/{filename_base}.html"

    record = {
        "id": next_id,
        "pid": pid,
        "title": title,
        "source": source,
        "href": html_file,
        "diff": diff,
        "tags": tags or []
    }

    if problem_url:
        record["problemUrl"] = problem_url

    return record


def save_record(record):
    """保存记录到统一的 records.json（追加 + 排序）"""
    records = load_existing_records()

    # 检查是否已存在相同 pid（防止重复）
    if any(r.get('pid') == record['pid'] for r in records):
        print(f"⚠️ 题号 {record['pid']} 已存在，跳过保存")
        return

    records.append(record)
    # 按 ID 重新排序
    records.sort(key=lambda x: int(x.get('id', 0)))

    # 写入 records.json
    with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✅ 已追加到 {RECORDS_FILE}（共 {len(records)} 条记录）")


def create_html_template(html_path, pid, title, source="洛谷", problem_url="#"):
    """创建题解HTML模板"""
    path = Path(html_path)
    if path.exists():
        print(f"⚠️ 文件已存在：{html_path}（跳过）")
        return

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{pid} - {title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif;
      line-height: 1.8;
      color: #333;
      background: #f5f5f5;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .back-link {{
      display: inline-block;
      margin-bottom: 20px;
      padding: 8px 12px;
      background: #f0f0f0;
      border-radius: 4px;
      text-decoration: none;
      color: #0066cc;
    }}
    h1 {{ margin-bottom: 10px; }}
    .meta {{ color: #888; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
    h2 {{ margin-top: 30px; margin-bottom: 15px; border-left: 4px solid #0066cc; padding-left: 15px; }}
  </style>
</head>
<body>
<div class="container">
  <a href="/" class="back-link">← 返回主页</a>
  <h1>{pid} - {title}</h1>
  <div class="meta">
    <span>🔗 <a href="{problem_url}" target="_blank">{source}</a></span>
  </div>
  <h2>📌 题目描述</h2>
  <p>在这里添加题目描述...</p>
  <h2>💡 解题思路</h2>
  <p>在这里添加解题思路...</p>
  <h2>📝 代码实现</h2>
  <pre><code>#include &lt;bits/stdc++.h&gt;
using namespace std;
int main() {{
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
   
    // 你的代码
   
    return 0;
}}
</code></pre>
  <h2>✅ 测试用例</h2>
  <p>在这里添加测试用例...</p>
</div>
</body>
</html>
"""

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ 已创建：{html_path}")


def interactive_create():
    """交互式创建新题目"""
    print("\n" + "="*50)
    print("📝 交互式创建新题目")
    print("="*50)

    pid = ask("题号 (如 P3372, CF1A, ABC086A): ").upper()
    if not pid:
        print("❌ 题号不能为空")
        return

    title = ask("题目标题: ")
    if not title:
        print("❌ 标题不能为空")
        return

    problem_url = ask("题目链接 (粘贴 URL，留空则为 #): ") or "#"

    source = ask("来源 (洛谷/CF/AtCoder，默认洛谷): ", ["洛谷", "CF", "AtCoder"]) or "洛谷"

    difficulties = ["入门", "普及-", "普及/提高-", "普及+/提高",
                    "提高+/省选-", "省选/NOI-", "NOI"]
    print("\n可选难度:")
    for i, d in enumerate(difficulties, 1):
        print(f" {i}. {d}")
    diff = select(difficulties, "选择难度 (1-7，默认4): ") or "普及/提高"

    tags_input = ask("标签 (用逗号分隔，可选): ")
    tags = [t.strip() for t in tags_input.split(',')] if tags_input else []

    record = create_json_record(pid, title, diff, source, tags, problem_url)

    print("\n" + "-"*50)
    print(f"ID: {record['id']}")
    print(f"题号: {pid}")
    print(f"标题: {title}")
    print(f"链接: {problem_url}")
    print(f"难度: {diff}")
    print(f"标签: {', '.join(tags) if tags else '(无)'}")
    print("-"*50)

    confirm = ask("\n确认创建？ (y/n): ", ["y", "n"]).lower()
    if confirm == 'y':
        html_path = record["href"]
        create_html_template(html_path, pid, title, source, problem_url)
        save_record(record)
        print("\n✨ 创建成功！")
    else:
        print("\n❌ 已取消")


def init_examples():
    """初始化示例数据（直接写入 records.json）"""
    print("\n初始化示例数据...")

    examples = [
        {
            "id": "001",
            "pid": "P3372",
            "title": "线段树 1",
            "source": "洛谷",
            "href": "solutions/lg-p3372.html",
            "diff": "普及/提高",
            "tags": ["线段树", "数据结构"],
            "problemUrl": "https://www.luogu.com.cn/problem/P3372"
        },
        {
            "id": "002",
            "pid": "CF1A",
            "title": "Theatre Square",
            "source": "CF",
            "href": "solutions/cf-1a.html",
            "diff": "入门",
            "tags": ["数学"],
            "problemUrl": "https://codeforces.com/problemset/problem/1/A"
        }
    ]

    # 先清空再写入（初始化）
    with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    for example in examples:
        html_path = example["href"]
        problem_url = example.get("problemUrl", "#")
        create_html_template(html_path, example["pid"], example["title"], example["source"], problem_url)
        save_record(example)

    print("✅ 示例数据初始化完成！")


def list_records():
    """列出所有题目"""
    records = load_existing_records()
    if not records:
        print("📭 暂无题目记录")
        return

    print("\n" + "="*80)
    print(f"{'ID':>3} {'题号':<8} {'标题':<20} {'难度':<12} {'标签':<20}")
    print("="*80)

    for r in records:
        tags = ", ".join(r.get('tags', [])[:2])
        if len(r.get('tags', [])) > 2:
            tags += f" +{len(r.get('tags'))-2}"
        print(f"{r['id']:>3} {r['pid']:<8} {r['title']:<20} {r['diff']:<12} {tags:<20}")

    print("="*80)
    print(f"总计: {len(records)} 题")


def interactive_add_lecture():
    """交互式添加讲义"""
    print("\n" + "="*50)
    print("📖 添加讲义")
    print("="*50)

    title = ask("讲义标题: ")
    if not title:
        print("❌ 标题不能为空"); return

    lectures_preview = load_json(LECTURES_FILE, default=[])
    nums_preview = [int(l['id'].split('-')[1]) for l in lectures_preview if '-' in l.get('id', '')]
    next_num_preview = max(nums_preview, default=0) + 1
    auto_slug = f"lec-{str(next_num_preview).zfill(3)}"
    slug_input = ask(f"Slug (回车使用自动生成的 '{auto_slug}'，或输入自定义): ").lower()
    slug = slug_input if slug_input else auto_slug

    courses_data = load_json(COURSES_FILE)
    course_names = [c['title'] for c in courses_data.get('courses', [])]
    print("\n可选课程 (空格分隔编号，可多选，直接回车跳过):")
    for i, name in enumerate(course_names, 1):
        print(f"  {i}. {name}")
    course_input = ask("选择课程: ")
    courses = [COURSE_IDS[int(x)-1] for x in course_input.split()
               if x.isdigit() and 1 <= int(x) <= len(COURSE_IDS)]

    topic_names = ["动态规划", "基础算法", "数据结构", "数学", "图论", "杂项", "字符串"]
    print("\n可选知识点 (空格分隔编号，可多选，直接回车跳过):")
    for i, name in enumerate(topic_names, 1):
        print(f"  {i}. {name}")
    topic_input = ask("选择知识点: ")
    topics = [TOPIC_IDS[int(x)-1] for x in topic_input.split()
              if x.isdigit() and 1 <= int(x) <= len(TOPIC_IDS)]

    tags_input = ask("标签 (逗号分隔，可选): ")
    tags = [t.strip() for t in tags_input.split(',') if t.strip()]

    lectures = load_json(LECTURES_FILE, default=[])
    if any(l.get('slug') == slug for l in lectures):
        print(f"⚠️ Slug '{slug}' 已存在，跳过"); return

    nums = [int(l['id'].split('-')[1]) for l in lectures if '-' in l.get('id', '')]
    next_num = max(nums, default=0) + 1
    lec_id = f"lec-{str(next_num).zfill(3)}"
    href = f"memos/{slug}.html"

    record = {
        "id": lec_id, "slug": slug, "title": title,
        "tags": tags, "courses": courses, "topics": topics,
        "href": href, "created": datetime.now().strftime("%Y-%m-%d")
    }

    print(f"\n将创建讲义: [{lec_id}] {title} → {href}")
    confirm = ask("确认? (y/n): ", ["y", "n"]).lower()
    if confirm != 'y':
        print("❌ 已取消"); return

    create_lecture_html(slug, title)
    lectures.append(record)
    save_json(LECTURES_FILE, lectures)
    print(f"✅ 讲义已创建: {href}")


def create_lecture_html(slug, title):
    """生成讲义 HTML 模板"""
    path = MEMOS_DIR / f"{slug}.html"
    if path.exists():
        print(f"⚠️ 文件已存在: {path}（跳过）"); return

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - OI 工具箱</title>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:-apple-system,'Segoe UI','Microsoft YaHei',sans-serif;line-height:1.8;color:#333;background:#f5f5f5}}
    .container{{max-width:800px;margin:0 auto;padding:40px 20px;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
    .back-link{{display:inline-block;margin-bottom:20px;padding:8px 12px;background:#f0f0f0;border-radius:4px;text-decoration:none;color:#0066cc}}
    h1{{margin-bottom:10px}}
    h2{{margin-top:30px;margin-bottom:15px;border-left:4px solid #9d3dcf;padding-left:15px}}
  </style>
</head>
<body>
<div class="container">
  <a href="../memos.html" class="back-link">← 返回备忘录</a>
  <h1>{title}</h1>
  <h2>📌 知识点概述</h2>
  <p>在这里添加知识点概述...</p>
  <h2>💡 核心内容</h2>
  <p>在这里添加核心内容...</p>
  <h2>📝 示例代码</h2>
  <pre><code>// 示例代码</code></pre>
  <h2>✅ 练习题目</h2>
  <p>在这里添加推荐练习题...</p>
</div>
</body>
</html>
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 已创建: {path}")


def interactive_add_content():
    """向课程添加课程内容（含讲义+练习题）"""
    print("\n" + "="*50)
    print("➕ 添加课程内容")
    print("="*50)

    data = load_json(COURSES_FILE)
    courses = data.get('courses', [])
    if not courses:
        print("❌ 未找到课程数据"); return

    print("选择课程:")
    for i, c in enumerate(courses, 1):
        print(f"  {i}. {c['title']}")
    course = select(courses, "课程编号: ", label_fn=lambda c: c['title'])
    if not course:
        print("❌ 无效选择"); return

    title = ask("内容标题 (如 AC自动机专题): ")
    if not title:
        print("❌ 标题不能为空"); return

    contents = course.setdefault('contents', [])
    nums = [int(c['id'].split('-')[1]) for c in contents if '-' in c.get('id', '')]
    next_num = max(nums, default=0) + 1
    content_id = f"content-{str(next_num).zfill(3)}"

    lectures_data = load_json(LECTURES_FILE, default=[])
    course_lecs = [l for l in lectures_data if course['id'] in l.get('courses', [])]
    linked_lecs = []
    if course_lecs:
        print(f"\n该课程下的讲义 (空格分隔编号，直接回车跳过):")
        for i, l in enumerate(course_lecs, 1):
            print(f"  {i}. {l['title']}")
        lec_input = ask("选择讲义: ")
        linked_lecs = [course_lecs[int(x)-1]['id'] for x in lec_input.split()
                       if x.isdigit() and 1 <= int(x) <= len(course_lecs)]

    problems = []
    platforms = ["luogu", "codeforces", "atcoder"]
    print("\n添加练习题 (输入 q 结束):")
    while True:
        pid = ask("  题号 (q结束): ")
        if pid.lower() == 'q' or not pid: break
        prob_title = ask("  题目标题: ")
        plat_item = select(platforms, "  平台 (1.洛谷 2.Codeforces 3.AtCoder): ")
        if not plat_item:
            print("  ❌ 无效平台，跳过"); continue
        problems.append({"pid": pid, "platform": plat_item, "title": prob_title})
        print(f"  ✓ 已添加 {pid}")

    content = {"id": content_id, "title": title, "lectures": linked_lecs, "problems": problems}
    contents.append(content)
    save_json(COURSES_FILE, data)
    print(f"✅ 已添加课程内容「{title}」({content_id}) 到「{course['title']}」")


def interactive_add_problem_to_content():
    """向课程内容或模拟赛添加练习题"""
    print("\n" + "="*50)
    print("➕ 添加练习题")
    print("="*50)

    print("目标: 1.课程内容  2.模拟赛")
    target = select(["课程内容", "模拟赛"], "选择: ")

    if target == "模拟赛":
        data = load_json(COURSES_FILE)
        course = _get_contest_prep(data)
        if not course:
            print("❌ 未找到 contest-prep 课程"); return
        mock_contents = [c for c in course.get('contents', []) if c.get('type') == 'mock']
        if not mock_contents:
            print("❌ 暂无模拟赛，请先用 add-mock 添加"); return
        print("选择模拟赛:")
        for i, c in enumerate(mock_contents, 1):
            print(f"  {i}. {c['title']}")
        content = select(mock_contents, "编号: ", label_fn=lambda c: c['title'])
        if not content:
            print("❌ 无效选择"); return
        platforms = ["luogu", "codeforces", "atcoder"]
        plat_item = select(platforms, "平台 (1.洛谷 2.Codeforces 3.AtCoder): ")
        if not plat_item:
            print("❌ 无效选择"); return
        pid   = ask("题号: ")
        title = ask("题目标题: ")
        if not pid or not title:
            print("❌ 题号和标题不能为空"); return
        full_score_input = ask("满分 (默认100): ")
        full_score = int(full_score_input) if full_score_input.isdigit() else 100
        href = ask("题解路径 (如 solutions/p1001.html，留空跳过): ") or None
        prob = {"pid": pid, "platform": plat_item, "title": title, "full_score": full_score}
        if href: prob["href"] = href
        content.setdefault('problems', []).append(prob)
        save_json(COURSES_FILE, data)
        print(f"✅ 已添加 {pid} 到「{content['title']}」")
        return

    data = load_json(COURSES_FILE)
    courses = data.get('courses', [])

    print("选择课程:")
    for i, c in enumerate(courses, 1):
        print(f"  {i}. {c['title']}")
    course = select(courses, "课程编号: ", label_fn=lambda c: c['title'])
    if not course:
        print("❌ 无效选择"); return

    contents = course.get('contents', [])
    if not contents:
        print("❌ 该课程暂无内容，请先用 add-content 添加"); return

    print("选择课程内容:")
    for i, c in enumerate(contents, 1):
        print(f"  {i}. {c['title']}")
    content = select(contents, "内容编号: ", label_fn=lambda c: c['title'])
    if not content:
        print("❌ 无效选择"); return

    platforms = ["luogu", "codeforces", "atcoder"]
    plat_item = select(platforms, "平台 (1.洛谷 2.Codeforces 3.AtCoder): ")
    if not plat_item:
        print("❌ 无效选择"); return

    pid   = ask("题号: ")
    title = ask("题目标题: ")
    if not pid or not title:
        print("❌ 题号和标题不能为空"); return

    content.setdefault('problems', []).append({"pid": pid, "platform": plat_item, "title": title})
    save_json(COURSES_FILE, data)
    print(f"✅ 已添加 {pid} 到「{content['title']}」")


def interactive_add_student():
    """添加学生账号"""
    print("\n" + "="*50)
    print("👤 添加学生")
    print("="*50)

    students = load_json(STUDENTS_FILE, default=[])
    nums = [int(s['id'].split('-')[1]) for s in students if '-' in s.get('id', '')]
    next_num = max(nums, default=0) + 1
    stu_id = f"stu-{str(next_num).zfill(3)}"

    name = ask("学生姓名: ")
    if not name:
        print("❌ 姓名不能为空"); return

    lg_uid    = ask("洛谷 UID (数字，留空跳过): ") or None
    cf_handle = ask("Codeforces handle (留空跳过): ") or None
    ac_handle = ask("AtCoder handle (留空跳过): ") or None

    record = {
        "id": stu_id, "name": name,
        "luogu_uid": lg_uid,
        "codeforces_handle": cf_handle,
        "atcoder_handle": ac_handle
    }
    students.append(record)
    save_json(STUDENTS_FILE, students)
    print(f"✅ 已添加学生: {name} ({stu_id})")


def fetch_submissions():
    """爬取学生提交记录，更新 submissions.json（供 GitHub Actions 调用）"""
    try:
        import requests
    except ImportError:
        print("❌ 需要安装 requests: pip install requests"); return

    students = load_json(STUDENTS_FILE, default=[])
    courses_data = load_json(COURSES_FILE)
    if not students:
        print("⚠️ 暂无学生数据"); return

    # 收集所有练习题
    luogu_pids, cf_pids, ac_pids = set(), set(), set()
    for course in courses_data.get('courses', []):
        for content in course.get('contents', []):
            for p in content.get('problems', []):
                if p.get('type') == 'divider': continue
                if p['platform'] == 'luogu':        luogu_pids.add(p['pid'])
                elif p['platform'] == 'codeforces': cf_pids.add(p['pid'])
                elif p['platform'] == 'atcoder':    ac_pids.add(p['pid'])

    # 加载现有数据
    existing_data = load_json(SUBS_FILE, default={}).get('data', {})
    result = {}
    for student in students:
        sid = student['id']
        prev = existing_data.get(sid, {})
        result[sid] = {
            "luogu":      dict(prev.get('luogu', {})),
            "codeforces": dict(prev.get('codeforces', {})),
            "atcoder":    dict(prev.get('atcoder', {})),
        }

    import re as _re

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    # ========== 洛谷：以学生为中心，从 /practice 页面获取全量数据 ==========
    if luogu_pids:
        print(f"\n📝 洛谷题目: {len(luogu_pids)} 道")
        for student in students:
            if not student.get('luogu_uid'):
                continue
            sid = student['id']
            uid = student['luogu_uid']

            # 如果该学生所有题目都已 AC，跳过
            if all(
                (result[sid]['luogu'].get(p) or {}).get('status') == 'ac'
                or result[sid]['luogu'].get(p) == 'ac'
                for p in luogu_pids
            ):
                print(f"\n  {student['name']}: 所有题目已AC，跳过")
                continue

            print(f"\n  {student['name']} (uid={uid}):")
            try:
                r = requests.get(f"https://www.luogu.com.cn/user/{uid}/practice",
                                 headers=headers, timeout=10)
                if r.status_code != 200:
                    print(f"    ❌ HTTP {r.status_code}")
                    continue

                passed_pids = set()
                submitted_pids = set()

                for s in _re.findall(r'<script[^>]*>(.*?)</script>', r.text, _re.DOTALL):
                    try:
                        d = json.loads(s)
                        if 'data' in d and 'passed' in d['data']:
                            passed_pids   = {p['pid'] for p in d['data'].get('passed', [])}
                            submitted_pids = {p['pid'] for p in d['data'].get('submitted', [])}
                            break
                    except json.JSONDecodeError:
                        continue

                for pid in sorted(luogu_pids):
                    if pid in passed_pids:
                        result[sid]['luogu'][pid] = {'status': 'ac', 'score': 100}
                        print(f"    {pid}: ✓ AC")
                    elif pid in submitted_pids:
                        result[sid]['luogu'][pid] = {'status': 'attempted', 'score': None}
                        print(f"    {pid}: ? 尝试")
                    else:
                        if pid in result[sid]['luogu']:
                            del result[sid]['luogu'][pid]
                        print(f"    {pid}: – 未做")

                time.sleep(0.5)
            except Exception as e:
                print(f"    ❌ 错误 ({e})")

    # ========== Codeforces：以题目为中心查询 ==========
    if cf_pids:
        print(f"\n📝 Codeforces 题目: {len(cf_pids)} 道")
        for pid in sorted(cf_pids):
            print(f"\n  题目 {pid}:")
            for student in students:
                if not student.get('codeforces_handle'):
                    continue
                sid = student['id']
                handle = student['codeforces_handle']

                # 如果已经 AC，跳过查询
                prev_data = result[sid]['codeforces'].get(pid)
                if isinstance(prev_data, dict) and prev_data.get('status') == 'ac':
                    print(f"    {student['name']}: 已AC，跳过")
                    continue
                elif prev_data == 'ac':  # 兼容旧格式
                    print(f"    {student['name']}: 已AC，跳过")
                    continue

                # 查询该学生所有提交（CF API 不支持按题目过滤，需要获取全部）
                try:
                    r = requests.get(
                        f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=10000",
                        timeout=15)
                    found_ac = False
                    found_attempted = False
                    for sub in r.json().get('result', []):
                        prob = sub.get('problem', {})
                        pid_str = str(prob.get('contestId', '')) + prob.get('index', '')
                        if pid_str == pid:
                            if sub.get('verdict') == 'OK':
                                found_ac = True
                                break
                            else:
                                found_attempted = True

                    if found_ac:
                        result[sid]['codeforces'][pid] = 'ac'
                        print(f"    {student['name']}: ✓ AC")
                    elif found_attempted:
                        result[sid]['codeforces'][pid] = 'attempted'
                        print(f"    {student['name']}: ? 尝试")
                    else:
                        if pid in result[sid]['codeforces']:
                            del result[sid]['codeforces'][pid]
                        print(f"    {student['name']}: – 未做")
                except Exception as e:
                    print(f"    {student['name']}: ❌ 错误 ({e})")

    # ========== AtCoder：以学生为中心，一次性获取全量提交 ==========
    if ac_pids:
        print(f"\n📝 AtCoder 题目: {len(ac_pids)} 道")
        for student in students:
            if not student.get('atcoder_handle'):
                continue
            sid = student['id']
            user = student['atcoder_handle']

            print(f"\n  {student['name']} ({user}):")
            try:
                # 分页获取该学生所有提交
                all_subs = []
                from_second = 0
                while True:
                    r = requests.get(
                        f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={user}&from_second={from_second}",
                        timeout=15)
                    if r.status_code != 200:
                        print(f"    ❌ API 不可用 (HTTP {r.status_code})")
                        break
                    batch = r.json()
                    if not batch:
                        break
                    all_subs.extend(batch)
                    if len(batch) < 500:
                        break
                    from_second = max(s['epoch_second'] for s in batch) + 1
                    time.sleep(0.5)

                ac_set       = {s['problem_id'] for s in all_subs if s.get('result') == 'AC'}
                attempted_set = {s['problem_id'] for s in all_subs if s.get('result') != 'AC'}

                for pid in sorted(ac_pids):
                    if pid in ac_set:
                        result[sid]['atcoder'][pid] = 'ac'
                        print(f"    {pid}: ✓ AC")
                    elif pid in attempted_set:
                        result[sid]['atcoder'][pid] = 'attempted'
                        print(f"    {pid}: ? 尝试")
                    else:
                        if pid in result[sid]['atcoder']:
                            del result[sid]['atcoder'][pid]
                        print(f"    {pid}: – 未做")

            except Exception as e:
                print(f"    ❌ 错误 ({e})")

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": result
    }
    save_json(SUBS_FILE, output)
    print(f"\n✅ submissions.json 已更新（{len(students)} 名学生）")


def _get_contest_prep(data):
    return next((c for c in data.get('courses', []) if c['id'] == 'contest-prep'), None)


def _select_contest():
    print("\n比赛类型:")
    for i, t in enumerate(CONTEST_TYPES, 1):
        print(f"  {i}. {t}")
    result = select(CONTEST_TYPES, "选择: ")
    if not result:
        print("❌ 无效选择")
    return result


def interactive_add_written():
    """添加笔试内容块"""
    print("\n" + "="*50)
    print("📝 添加笔试专题")
    print("="*50)

    data = load_json(COURSES_FILE)
    course = _get_contest_prep(data)
    if not course:
        print("❌ 未找到 contest-prep 课程"); return

    contest = _select_contest()
    if not contest: return

    title = ask("内容标题 (如 CSP-J 笔试专题): ")
    if not title:
        print("❌ 标题不能为空"); return

    contents = course.setdefault('contents', [])
    nums = [int(c['id'].split('-')[1]) for c in contents if c['id'].startswith('written-')]
    next_num = max(nums, default=0) + 1
    content_id = f"written-{str(next_num).zfill(3)}"

    lectures_data = load_json(LECTURES_FILE, default=[])
    course_lecs = [l for l in lectures_data if 'contest-prep' in l.get('courses', [])]
    linked_lecs = []
    if course_lecs:
        print(f"\n备赛课程下的讲义 (空格分隔编号，直接回车跳过):")
        for i, l in enumerate(course_lecs, 1):
            print(f"  {i}. {l['title']}")
        lec_input = ask("选择讲义: ")
        linked_lecs = [course_lecs[int(x)-1]['id'] for x in lec_input.split()
                       if x.isdigit() and 1 <= int(x) <= len(course_lecs)]

    problems = []
    print("\n添加笔试题目 (输入 q 结束):")
    wp_num = 1
    while True:
        name = ask("  题目名称 (如 2024 CSP-J 初赛，q结束): ")
        if name.lower() == 'q' or not name: break
        url = ask("  比赛链接 (URL): ")
        wp_id = f"wp-{str(wp_num).zfill(3)}"
        problems.append({"id": wp_id, "name": name, "url": url})
        wp_num += 1
        print(f"  ✓ 已添加 {name}")

    content = {"id": content_id, "type": "written", "contest": contest,
               "title": title, "lectures": linked_lecs, "problems": problems}
    contents.append(content)
    save_json(COURSES_FILE, data)
    print(f"✅ 已添加笔试专题「{title}」({content_id})")


def interactive_add_written_problem():
    """向已有笔试内容块追加笔试题目"""
    print("\n" + "="*50)
    print("➕ 向笔试专题添加题目")
    print("="*50)

    data = load_json(COURSES_FILE)
    course = _get_contest_prep(data)
    if not course:
        print("❌ 未找到 contest-prep 课程"); return

    written_contents = [c for c in course.get('contents', []) if c.get('type') == 'written']
    if not written_contents:
        print("❌ 暂无笔试专题，请先用 add-written 添加"); return

    print("选择笔试专题:")
    for i, c in enumerate(written_contents, 1):
        print(f"  {i}. {c['title']}")
    content = select(written_contents, "编号: ", label_fn=lambda c: c['title'])
    if not content:
        print("❌ 无效选择"); return

    existing_nums = [int(p['id'].split('-')[1]) for p in content.get('problems', []) if p.get('id','').startswith('wp-')]
    wp_num = max(existing_nums, default=0) + 1

    name = ask("题目名称 (如 2024 CSP-J 初赛): ")
    if not name:
        print("❌ 名称不能为空"); return
    url = ask("比赛链接 (URL): ")
    wp_id = f"wp-{str(wp_num).zfill(3)}"
    content.setdefault('problems', []).append({"id": wp_id, "name": name, "url": url})
    save_json(COURSES_FILE, data)
    print(f"✅ 已添加「{name}」到「{content['title']}」")


def interactive_add_mock():
    """添加上机模拟赛"""
    print("\n" + "="*50)
    print("🏆 添加上机模拟赛")
    print("="*50)

    data = load_json(COURSES_FILE)
    course = _get_contest_prep(data)
    if not course:
        print("❌ 未找到 contest-prep 课程"); return

    contest = _select_contest()
    if not contest: return

    title = ask("模拟赛标题 (如 CSP-J 模拟赛 #1): ")
    if not title:
        print("❌ 标题不能为空"); return

    contents = course.setdefault('contents', [])
    nums = [int(c['id'].split('-')[1]) for c in contents if c['id'].startswith('mock-')]
    next_num = max(nums, default=0) + 1
    content_id = f"mock-{str(next_num).zfill(3)}"

    platforms = ["luogu", "codeforces", "atcoder"]
    problems = []
    print("\n添加题目 (输入 q 结束):")
    while True:
        pid = ask("  题号 (q结束): ")
        if pid.lower() == 'q' or not pid: break
        prob_title = ask("  题目标题: ")
        plat_item = select(platforms, "  平台 (1.洛谷 2.Codeforces 3.AtCoder): ")
        if not plat_item:
            print("  ❌ 无效平台，跳过"); continue
        full_score_input = ask("  满分 (默认100): ")
        full_score = int(full_score_input) if full_score_input.isdigit() else 100
        href = ask("  题解路径 (如 solutions/p1001.html，留空跳过): ") or None
        prob = {"pid": pid, "platform": plat_item, "title": prob_title, "full_score": full_score}
        if href: prob["href"] = href
        problems.append(prob)
        print(f"  ✓ 已添加 {pid}")

    content = {"id": content_id, "type": "mock", "contest": contest,
               "title": title, "problems": problems, "scores": {}, "participants": []}
    students = load_json(STUDENTS_FILE, default=[])
    if students:
        print("\n选择参与学生 (空格分隔编号，直接回车=全员参与):")
        for i, s in enumerate(students, 1):
            print(f"  {i}. {s['name']}")
        sel = ask("选择: ")
        if sel:
            content["participants"] = [students[int(x)-1]['id'] for x in sel.split()
                                        if x.isdigit() and 1 <= int(x) <= len(students)]
    contents.append(content)
    save_json(COURSES_FILE, data)
    print(f"✅ 已添加模拟赛「{title}」({content_id})")


def interactive_set_scores():
    """录入模拟赛分数"""
    print("\n" + "="*50)
    print("📊 录入模拟赛分数")
    print("="*50)

    data = load_json(COURSES_FILE)
    course = _get_contest_prep(data)
    if not course:
        print("❌ 未找到 contest-prep 课程"); return

    mock_contents = [c for c in course.get('contents', []) if c.get('type') == 'mock']
    if not mock_contents:
        print("❌ 暂无模拟赛，请先用 add-mock 添加"); return

    print("选择模拟赛:")
    for i, c in enumerate(mock_contents, 1):
        print(f"  {i}. {c['title']}")
    content = select(mock_contents, "编号: ", label_fn=lambda c: c['title'])
    if not content:
        print("❌ 无效选择"); return

    problems = content.get('problems', [])
    if not problems:
        print("❌ 该模拟赛暂无题目"); return

    students = load_json(STUDENTS_FILE, default=[])
    if not students:
        print("❌ 暂无学生数据"); return

    scores = content.setdefault('scores', {})
    print(f"\n题目: {', '.join(p['pid'] for p in problems)}")
    print("(直接回车 = 0 分，输入 s 跳过该学生)\n")

    for s in students:
        print(f"  {s['name']} ({s['id']}):")
        stu_scores = dict(scores.get(s['id'], {}))
        skip = False
        for p in problems:
            cur = stu_scores.get(p['pid'], 0)
            val = ask(f"    {p['pid']} (满分{p.get('full_score',100)}, 当前{cur}): ")
            if val.lower() == 's':
                skip = True; break
            if val == '':
                stu_scores[p['pid']] = 0
            elif val.lstrip('-').isdigit():
                stu_scores[p['pid']] = int(val)
        if not skip:
            scores[s['id']] = stu_scores

    save_json(COURSES_FILE, data)
    print(f"\n✅ 分数已保存")


def interactive_set_participants():
    """设置模拟赛参与学生"""
    print("\n" + "="*50)
    print("👥 设置模拟赛参与学生")
    print("="*50)

    data = load_json(COURSES_FILE)
    course = _get_contest_prep(data)
    if not course:
        print("❌ 未找到 contest-prep 课程"); return

    mock_contents = [c for c in course.get('contents', []) if c.get('type') == 'mock']
    if not mock_contents:
        print("❌ 暂无模拟赛，请先用 add-mock 添加"); return

    print("选择模拟赛:")
    for i, c in enumerate(mock_contents, 1):
        cur = c.get('participants', [])
        print(f"  {i}. {c['title']} (当前: {'全员' if not cur else str(len(cur))+'人'})")
    content = select(mock_contents, "编号: ", label_fn=lambda c: c['title'])
    if not content:
        print("❌ 无效选择"); return

    students = load_json(STUDENTS_FILE, default=[])
    cur_ids = content.get('participants', [])
    print("\n选择参与学生 (空格分隔编号，直接回车=全员参与):")
    for i, s in enumerate(students, 1):
        mark = "✓" if s['id'] in cur_ids else " "
        print(f"  {i}. [{mark}] {s['name']}")
    sel = ask("选择: ")
    content['participants'] = [students[int(x)-1]['id'] for x in sel.split()
                                if x.isdigit() and 1 <= int(x) <= len(students)] if sel else []
    save_json(COURSES_FILE, data)
    result = '全员参与' if not content['participants'] else f"{len(content['participants'])} 名学生"
    print(f"✅ 已更新「{content['title']}」参与学生：{result}")


# ─────────────────────────────────────────────────────────────
# 讲义主题：polish 命令会把下面两段常量写出为
#   memos/lecture-theme.css / memos/lecture-enhance.js
# 改样式只需改这里，然后重新跑 python script.py polish
# ─────────────────────────────────────────────────────────────

LECTURE_THEME_CSS = r"""/* 本文件由 script.py polish 自动生成，请勿手改（改 script.py 里的 LECTURE_THEME_CSS） */

/* ── 设计 token ── */
:root {
  --lec-green:#52c41a;  --lec-green-bg:#f2fbe9;  --lec-green-line:#a5e07a;
  --lec-blue:#3498db;   --lec-blue-bg:#eef6fd;   --lec-blue-line:#9dcdf0;
  --lec-orange:#e67e22; --lec-orange-bg:#fef6ea; --lec-orange-line:#f3c18a;
  --lec-purple:#9d3dcf; --lec-purple-bg:#f7effb; --lec-purple-line:#d4a5ea;
  --lec-indigo:#5b6ee1; --lec-indigo-bg:#eef0fc; --lec-indigo-line:#aeb7f0;
  --lec-red:#e5484d;    --lec-red-bg:#fdeff0;    --lec-red-line:#f2a7aa;
  --lec-text:#2f3437;
  /* 代码块：浅色中性调，和站点主色只在 hover / 强调处相遇 */
  --lec-code-bg:#fbfcfd;  --lec-code-head:#f6f8fa;  --lec-code-border:#e5e8ec;
  --lec-code-sub:#6b7280;
  --lec-mono:'Fira Code','JetBrains Mono','Menlo','Consolas',monospace;
}

/* ── 阅读进度条 ── */
#lec-progress {
  position: fixed; top: 0; left: 0;
  height: 3px;
  background: linear-gradient(90deg, #52c41a, #3498db);
  width: 0%; z-index: 9999;
  transition: width .12s ease;
}

/* ── h2 自动编号 + 彩色圆圈 ── */
#write { counter-reset: h2c egc; }
#write h2 {
  counter-increment: h2c;
  border-bottom: none !important;
  padding: 8px 14px 8px 48px !important;
  background: linear-gradient(to right, #f0fbe8, transparent);
  border-radius: 8px;
  margin-top: 2em !important;
  position: relative;
}
#write h2::before {
  content: counter(h2c);
  position: absolute; left: 8px; top: 50%; transform: translateY(-50%);
  width: 28px; height: 28px;
  background: #52c41a; color: #fff;
  border-radius: 50%;
  font-size: .82rem; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
}

/* ── h3 左边框 ── */
#write h3 {
  border-left: 4px solid #3498db !important;
  padding-left: 12px !important;
  background: linear-gradient(to right, #ebf5fb 0%, transparent 80%);
  border-radius: 0 6px 6px 0;
}

/* ── h4 小节标题：比 h3 更轻，靛蓝菱形标记 ── */
#write h4 {
  position: relative;
  font-size: 1.05rem !important;
  font-weight: 600;
  color: #33383d;
  margin: 1.7em 0 .7em !important;
  padding: 0 0 5px 16px !important;
  border-bottom: 1px solid #edeff2;
}
#write h4::before {
  content: '';
  position: absolute;
  left: 1px; top: .62em;
  width: 7px; height: 7px;
  background: var(--lec-indigo);
  border-radius: 2px;
  transform: rotate(45deg);
}

/* 「例题：」标题 → 自动编号的靛蓝徽标（例题 1、例题 2 …） */
#write h4.lec-eg {
  counter-increment: egc;
  padding-left: 0 !important;
  border-bottom: none;
}
#write h4.lec-eg::before {
  content: '例题 ' counter(egc);
  position: static;
  display: inline-block;
  width: auto; height: auto;
  margin-right: 9px;
  padding: 2px 11px;
  transform: none;
  border-radius: 6px;
  background: var(--lec-indigo);
  color: #fff;
  font-size: 12.5px; font-weight: 700;
  letter-spacing: .02em;
  vertical-align: 2px;
}

/* 例题 h4 作为引用的首行时，收掉多余上间距 */
#write blockquote > h4:first-child { margin-top: .1em !important; }

/* h4 里的题目链接：去掉刺眼的下划线蓝，hover 才提示可点 */
#write h4 a {
  color: #2f3437 !important;
  text-decoration: none !important;
  border-bottom: 1px dashed var(--lec-indigo-line);
  transition: color .15s, border-color .15s;
}
#write h4 a:hover {
  color: var(--lec-indigo) !important;
  border-bottom-color: var(--lec-indigo);
}

/* ── 引用 / Callout 卡片 ──
   默认（无前缀标记）= 淡蓝「定义卡」，讲义里大量的概念定义走这一档  */
#write blockquote,
.typora-export blockquote {
  position: relative;
  margin: 1.35em 0 !important;
  padding: 12px 16px 12px 18px !important;
  border: 1px solid var(--lec-blue-line) !important;
  border-left: 4px solid var(--lec-blue) !important;
  border-radius: 4px 9px 9px 4px !important;
  background: var(--lec-blue-bg) !important;
  color: var(--lec-text) !important;      /* 盖掉 Typora 的 color:#777 */
  box-shadow: 0 1px 3px rgba(24,60,92,.05);
  transition: box-shadow .18s ease;
}
#write blockquote:hover { box-shadow: 0 3px 12px rgba(24,60,92,.09); }

/* 引用内部排版细节 */
#write blockquote > :first-child { margin-top: 0 !important; }
#write blockquote > :last-child  { margin-bottom: 0 !important; }
#write blockquote p { line-height: 1.75; }
#write blockquote code {
  background: rgba(255,255,255,.75) !important;
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 4px;
  padding: 1px 5px;
}
#write blockquote blockquote {      /* 嵌套引用收窄一点 */
  margin: .8em 0 !important;
  box-shadow: none;
}
#write li blockquote { margin: .7em 0 !important; }

/* 类型标签（由 lecture-enhance.js 加 class 后显示） */
#write blockquote[data-lec-label]::before {
  content: attr(data-lec-label);
  display: inline-block;
  margin: 0 0 7px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11.5px; font-weight: 700;
  letter-spacing: .03em;
  line-height: 1.6;
  color: #fff;
  background: var(--lec-blue);
}

/* 各类型配色 */
#write blockquote.lec-tip {
  border-color: var(--lec-green-line) !important;
  border-left-color: var(--lec-green) !important;
  background: var(--lec-green-bg) !important;
}
#write blockquote.lec-tip::before { background: var(--lec-green); }

#write blockquote.lec-warn {
  border-color: var(--lec-orange-line) !important;
  border-left-color: var(--lec-orange) !important;
  background: var(--lec-orange-bg) !important;
}
#write blockquote.lec-warn::before { background: var(--lec-orange); }

#write blockquote.lec-key {
  border-color: var(--lec-purple-line) !important;
  border-left-color: var(--lec-purple) !important;
  background: var(--lec-purple-bg) !important;
}
#write blockquote.lec-key::before { background: var(--lec-purple); }

#write blockquote.lec-example {
  border-color: var(--lec-indigo-line) !important;
  border-left-color: var(--lec-indigo) !important;
  background: var(--lec-indigo-bg) !important;
}
#write blockquote.lec-example::before { background: var(--lec-indigo); }

#write blockquote.lec-pitfall {
  border-color: var(--lec-red-line) !important;
  border-left-color: var(--lec-red) !important;
  background: var(--lec-red-bg) !important;
}
#write blockquote.lec-pitfall::before { background: var(--lec-red); }

/* 引用里的公式不要溢出卡片 */
#write blockquote mjx-container[display="true"],
#write blockquote .MathJax_Display {
  overflow-x: auto; overflow-y: hidden;
  max-width: 100%;
}

/* ── 代码块 wrapper + header bar ── */
.lec-code-wrap {
  margin: 1.4em 0;
  border: 1px solid var(--lec-code-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--lec-code-bg);
  box-shadow: 0 1px 3px rgba(24,60,92,.05);
  transition: box-shadow .18s ease, border-color .18s ease;
}
.lec-code-wrap:hover {
  border-color: #d6dbe2;
  box-shadow: 0 4px 14px rgba(24,60,92,.08);
}

.lec-code-header {
  display: flex; align-items: center; gap: 9px;
  padding: 7px 10px 7px 12px;
  background: var(--lec-code-head);
  border-bottom: 1px solid transparent;
  cursor: pointer;
  user-select: none;
  transition: background .15s, border-color .15s;
}
.lec-code-wrap.is-open .lec-code-header { border-bottom-color: var(--lec-code-border); }
.lec-code-header:hover { background: #f0f3f6; }

/* 语言徽标：左侧小圆点 + 语言名 */
.lec-lang-name {
  display: inline-flex; align-items: center; gap: 6px;
  flex: none;
  font-size: 11px; font-weight: 600;
  color: var(--lec-code-sub);
  font-family: var(--lec-mono);
  text-transform: uppercase; letter-spacing: .06em;
}
.lec-lang-name::before {
  content: '';
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--lec-green);
  box-shadow: 0 0 0 2px rgba(82,196,26,.16);
}

/* 可选标题：`// @open 快速幂` 里的「快速幂」 */
.lec-code-title {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 12.5px; font-weight: 600; color: #3f4650;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.lec-code-title:empty { display: none; }
.lec-code-title:empty + .lec-code-lines { margin-left: auto; }

/* 行数提示 */
.lec-code-lines {
  flex: none;
  font-size: 11px; color: var(--lec-text-light, #a3a9b3);
  font-family: var(--lec-mono);
}
.lec-lang-name + .lec-code-lines { margin-left: auto; }

.lec-header-actions { flex: none; display: flex; gap: 6px; margin-left: 4px; }
.lec-header-btn {
  padding: 3px 10px; font-size: 11px; line-height: 1.5;
  background: #fff; color: #5b6270;
  border: 1px solid var(--lec-code-border); border-radius: 6px;
  cursor: pointer;
  transition: background .15s, color .15s, border-color .15s;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.lec-header-btn:hover {
  background: var(--lec-green); color: #fff;
  border-color: var(--lec-green);
}
.lec-header-btn.is-done {
  background: var(--lec-green-bg); color: var(--lec-green-dark, #3da613);
  border-color: var(--lec-green-line);
}

/* 折叠区域：max-height 由 JS 精确设置，动画不再跳 */
.lec-code-inner {
  overflow: hidden;
  max-height: 0;
  transition: max-height .28s cubic-bezier(.4,0,.2,1);
}
/* 展开动画结束后解除裁剪，交回 CodeMirror 自己的横向滚动 */
.lec-code-inner.is-settled { overflow: visible; }

/* pre 交给 wrapper 管圆角和外边距 */
.lec-code-inner > pre.md-fences,
.lec-code-inner > pre {
  margin: 0 !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: var(--lec-code-bg) !important;
}
.lec-code-inner .CodeMirror,
.lec-code-inner .CodeMirror-scroll { background: var(--lec-code-bg) !important; }
/* 行号列：淡一点，别抢代码的注意力 */
.lec-code-inner .CodeMirror-linenumber { color: #c2c8d0 !important; }
.lec-code-inner .CodeMirror-gutters {
  background: var(--lec-code-bg) !important;
  border-right: 1px solid #eef1f4 !important;
}

/* ── 表格美化 ── */
#write table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0,0,0,.08);
  border-collapse: collapse;
  width: 100%;
}
#write thead tr { background: #52c41a !important; }
#write thead th { background: #52c41a !important; color: #fff !important; border: none !important; padding: 10px 14px !important; }
#write tbody tr:hover { background: #f0fbe8 !important; }
#write tbody td { border-color: #e8eaed !important; padding: 8px 14px !important; }

/* ── 动画演示卡片（assets/*.html iframe 嵌入） ── */
.lec-demo {
  margin: 1.6em 0;
  border: 1px solid #e8eaed;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,.08);
}
.lec-demo-head {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 14px;
  background: linear-gradient(to right, #f0fbe8, #fff);
  border-bottom: 1px solid #e8eaed;
}
.lec-demo-badge {
  flex: none;
  padding: 2px 9px;
  border-radius: 999px;
  background: #52c41a; color: #fff;
  font-size: 11px; font-weight: 700; letter-spacing: .04em;
}
.lec-demo-title {
  flex: 1 1 auto;
  font-size: 14px; font-weight: 600; color: #1a1a1a;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.lec-demo-open {
  flex: none;
  font-size: 12px; color: #3da613 !important;
  text-decoration: none !important;
  border: 1px solid #b7e59a; border-radius: 6px;
  padding: 2px 9px;
  transition: background .15s, color .15s;
}
.lec-demo-open:hover { background: #52c41a; color: #fff !important; border-color: #52c41a; }
.lec-demo iframe {
  display: block;
  width: 100% !important;
  border: none !important;
  margin: 0 !important;
  background: #f7f9fc;
}

/* ── 打印 ── */
@media print {
  #lec-progress { display: none; }
  #write blockquote { box-shadow: none; break-inside: avoid; }
  .lec-demo iframe { display: none; }
  .lec-demo-head { border-bottom: none; }
  /* 折叠的代码也要打出来 */
  .lec-code-inner { max-height: none !important; overflow: visible !important; }
  .lec-header-actions { display: none; }
  .lec-code-wrap { box-shadow: none; break-inside: avoid; }
}
"""

# 引用类型识别规则：(emoji 标记, 关键词, class, 标签文字)
# 顺序即优先级，第一条命中即停；全部不命中 → 默认淡蓝定义卡（无标签）
# class 为空 = 沿用默认淡蓝配色，只加标签
LECTURE_CALLOUTS = [
    (['📌'], ['重点', '核心', '结论','总结'],           'lec-key',     '总结'),
    (['💡'], ['提示', '技巧', '小贴士', 'tip'],  'lec-tip',     '提示'),
    (['⚠️', '⚠'], ['注意', '警告', 'warn'],      'lec-warn',    '注意'),
    (['❌'], ['易错', '坑点', '误区'],            'lec-pitfall', '易错'),
    (['📝'], ['例题', '举例', '例如', '例'],      'lec-example', '例题'),
    (['🔍'], ['证明', '分析', '推导'],            'lec-example', '证明'),
    (['📖'], ['定义', '定理', '性质'],            '',            '定义'),
]


def _callout_regex(emojis, keywords):
    """
    构造前缀正则：必须有显式标记才算 callout，避免误吃正文
      - 有 emoji：后面的关键词和冒号都可省略        「📌 xxx」「📌重点：xxx」
      - 无 emoji：关键词后必须跟冒号或逗号          「注意：xxx」「注意，xxx」
    所以「定义域是…」不会被识别成「定义」卡而被截断
    """
    e = '|'.join(emojis)
    k = '|'.join(keywords)
    return r'^(?:(?:%s)\s*(?:(?:%s)\s*[:：，]?)?|(?:%s)\s*[:：，])\s*' % (e, k, k)


# 没写标记时：不超过这个行数的代码块默认展开，更长的默认折叠
AUTO_OPEN_MAX_LINES = 18


def _build_enhance_js():
    """生成 lecture-enhance.js（callout 规则由 LECTURE_CALLOUTS 编译进去）"""
    rules = ',\n    '.join(
        '[/%s/i, %s, %s]' % (_callout_regex(emojis, kws), json.dumps(cls), json.dumps(label))
        for emojis, kws, cls, label in LECTURE_CALLOUTS
    )
    return (_ENHANCE_JS_TEMPLATE
            .replace('/*__CALLOUT_RULES__*/', rules)
            .replace('/*__AUTO_OPEN_MAX_LINES__*/', str(AUTO_OPEN_MAX_LINES)))


_ENHANCE_JS_TEMPLATE = r"""// 本文件由 script.py polish 自动生成，请勿手改（改 script.py 里的 _ENHANCE_JS_TEMPLATE）
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
    /*__CALLOUT_RULES__*/
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
  //
  // 展开策略标记（写在 Markdown 里，导出后都不显示）：
  //   ① 代码块首行注释   // @open        / # @fold  / -- @open 标题
  //   ② 代码块前一行     <!-- @open -->
  //   ③ 文档任意位置     <!-- @open-all -->  改变整篇默认
  // 没有任何标记时：行数 <= AUTO_OPEN_MAX_LINES 自动展开，更长的仍折叠。
  const AUTO_OPEN_MAX_LINES = /*__AUTO_OPEN_MAX_LINES__*/;

  // @open / @fold（含别名）+ 可选标题；前面允许各语言的行注释符
  const MARK_RE = /^\s*(?:\/\/+|#+|--|;+|%|\/\*|<!--)?\s*@(open|expand|show|展开|fold|close|collapse|hide|折叠)(?![A-Za-z0-9_])\s*[:：]?\s*(.*?)\s*(?:\*\/|-->)?\s*$/i;
  const OPEN_WORDS = /^(open|expand|show|展开)$/i;

  function parseMark(text) {
    const m = (text || '').replace(/[​﻿]/g, '').match(MARK_RE);
    if (!m) return null;
    return { open: OPEN_WORDS.test(m[1]), title: m[2] || '' };
  }

  // ③ 文档级默认：扫全文 HTML 注释
  let docDefault = null;
  (function () {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_COMMENT);
    let c;
    while ((c = w.nextNode())) {
      const m = c.nodeValue.trim().match(/^@(open|fold|展开|折叠)-all$/i);
      if (m) { docDefault = /^(open|展开)$/i.test(m[1]); break; }
    }
  })();

  // ② 代码块前的 HTML 注释标记；命中就把注释（和只装着它的空段落）一起删掉
  function markFromSiblings(pre) {
    let node = pre.previousSibling, hops = 0;
    while (node && hops++ < 3) {
      if (node.nodeType === 8) {                      // 注释节点
        const mk = parseMark(node.nodeValue);
        if (mk) { node.remove(); return mk; }
      } else if (node.nodeType === 1) {               // 只含注释的 <p>
        if (node.textContent.trim() === '') {
          for (const child of Array.from(node.childNodes)) {
            if (child.nodeType !== 8) continue;
            const mk = parseMark(child.nodeValue);
            if (mk) { node.remove(); return mk; }
          }
        } else break;
      } else if (node.nodeType === 3 && node.nodeValue.trim() !== '') {
        break;
      }
      node = node.previousSibling;
    }
    return null;
  }

  // ① 首行标记：从 CodeMirror 渲染结果里摘掉那一行，并把容器高度收回去
  function stripCMFirstLine(pre, lineEl) {
    const row = lineEl.closest('.CodeMirror-code > div') || lineEl.parentNode;
    const h = row.getBoundingClientRect().height || 0;
    row.remove();
    if (!h) return;
    const shrink = function (el, prop) {
      if (!el) return;
      const v = parseFloat(el.style[prop]);
      if (!isNaN(v)) el.style[prop] = Math.max(0, v - h) + 'px';
    };
    shrink(pre.querySelector('.CodeMirror'), 'height');
    shrink(pre.querySelector('.CodeMirror-gutters'), 'height');
    shrink(pre.querySelector('.CodeMirror-sizer'), 'minHeight');
    const spacer = pre.querySelector('.CodeMirror-sizer > div[style*="top"]');
    shrink(spacer, 'top');
    // 行号重新排一遍，删掉首行后不留空号
    pre.querySelectorAll('.CodeMirror-linenumber').forEach(function (n, i) {
      n.textContent = String(i + 1);
    });
  }

  // 首行标记：<code> 版（非 CodeMirror 导出）直接删掉第一行文本
  function stripCodeFirstLine(code) {
    const walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const i = node.nodeValue.indexOf('\n');
      if (i >= 0) { node.nodeValue = node.nodeValue.slice(i + 1); return; }
      node.nodeValue = '';
    }
  }

  document.querySelectorAll('#write pre, .typora-export pre').forEach(function (pre) {
    if (pre.closest('.CodeMirror')) return;

    const cmLines = pre.querySelectorAll('.CodeMirror-line');
    const cmCodeLines = pre.querySelectorAll('.CodeMirror-code pre');
    const isCM = cmLines.length > 0;
    const code = pre.querySelector('code');
    if (!isCM && !code) return;

    const langAttr = pre.getAttribute('lang');
    const langCls = code && Array.from(code.classList).find(function (c) { return c.startsWith('language-'); });
    const lang = (langAttr || (langCls ? langCls.slice(9) : 'code')).trim().split(/\s+/)[0] || 'code';

    // ── 解析展开策略 ──
    let mark = markFromSiblings(pre);
    if (isCM) {
      const first = cmLines[0];
      const mk = first && parseMark(first.textContent);
      if (mk) { mark = mk; stripCMFirstLine(pre, first); }
    } else {
      const firstLine = code.textContent.split('\n', 1)[0];
      const mk = parseMark(firstLine);
      if (mk) { mark = mk; stripCodeFirstLine(code); }
    }

    const lineCount = isCM
      ? pre.querySelectorAll('.CodeMirror-line').length
      : code.textContent.replace(/\n+$/, '').split('\n').length;

    const shouldOpen = mark ? mark.open
      : docDefault !== null ? docDefault
      : lineCount <= AUTO_OPEN_MAX_LINES;

    // Header bar
    const header = document.createElement('div');
    header.className = 'lec-code-header';

    const langLabel = document.createElement('span');
    langLabel.className = 'lec-lang-name';
    langLabel.textContent = lang;
    header.appendChild(langLabel);

    const titleEl = document.createElement('span');
    titleEl.className = 'lec-code-title';
    titleEl.textContent = mark && mark.title ? mark.title : '';
    header.appendChild(titleEl);

    const linesEl = document.createElement('span');
    linesEl.className = 'lec-code-lines';
    linesEl.textContent = lineCount + ' 行';
    header.appendChild(linesEl);

    const actions = document.createElement('div');
    actions.className = 'lec-header-actions';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'lec-header-btn';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'lec-header-btn';
    copyBtn.textContent = '复制';
    copyBtn.addEventListener('click', function (e) {
      e.stopPropagation();                  // 别连带触发 header 的折叠
      // 首行标记可能已被删掉 → 复制时重新取一次当前 DOM
      const src = isCM ? pre.querySelectorAll('.CodeMirror-code pre') : null;
      const text = src && src.length
        ? Array.from(src).map(function (l) { return l.textContent.replace(/​/g, '').replace(/ /g, ' '); }).join('\n')
        : code ? code.textContent : '';
      navigator.clipboard.writeText(text).then(function () {
        copyBtn.textContent = '已复制';
        copyBtn.classList.add('is-done');
        setTimeout(function () {
          copyBtn.textContent = '复制';
          copyBtn.classList.remove('is-done');
        }, 2000);
      });
    });

    actions.appendChild(toggleBtn);
    actions.appendChild(copyBtn);
    header.appendChild(actions);

    const inner = document.createElement('div');
    inner.className = 'lec-code-inner';

    // 组装：先把 wrap 插入正确位置，再移动 pre
    const wrap = document.createElement('div');
    wrap.className = 'lec-code-wrap';
    wrap.appendChild(header);
    const parent = pre.parentNode;
    parent.insertBefore(wrap, pre); // wrap 占位（pre 仍在 parent 中）
    inner.appendChild(pre);         // pre 从 parent 移入 inner
    wrap.appendChild(inner);

    function setOpen(open, animate) {
      wrap.classList.toggle('is-open', open);
      toggleBtn.textContent = open ? '▲ 收起' : '▼ 展开';
      if (!open) {
        // 收起：先钉住当前高度再回 0，否则 none → 0 不过渡
        inner.classList.remove('is-settled');
        if (animate) {
          inner.style.maxHeight = inner.scrollHeight + 'px';
          void inner.offsetHeight;
        }
        inner.style.maxHeight = '0px';
        return;
      }
      const settle = function () {
        if (!wrap.classList.contains('is-open')) return;
        inner.style.maxHeight = 'none';
        inner.classList.add('is-settled');
      };
      if (!animate) { settle(); return; }
      inner.style.maxHeight = inner.scrollHeight + 'px';
      // 动画结束后解除限制，让内容（长行/公式）自然撑开
      setTimeout(settle, 320);
    }

    // 整条 header 都能点，按钮只是视觉提示
    header.addEventListener('click', function () {
      setOpen(!wrap.classList.contains('is-open'), true);
    });

    setOpen(shouldOpen, false);
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
"""


def polish_html(target=None):
    """后处理 Typora 导出的讲义 HTML，注入增强样式和功能"""
    if target and target != 'all':
        files = [MEMOS_DIR / target] if not target.startswith('memos/') else [Path(target)]
    else:
        files = sorted(MEMOS_DIR.glob('lec-*.html'))

    if not files:
        print("❌ 未找到讲义 HTML 文件"); return

    # 每次 polish 都从脚本常量重写主题文件，保证样式只有一份来源
    (MEMOS_DIR / 'lecture-theme.css').write_text(LECTURE_THEME_CSS, encoding='utf-8')
    (MEMOS_DIR / 'lecture-enhance.js').write_text(_build_enhance_js(), encoding='utf-8')
    print("🎨 已生成 lecture-theme.css / lecture-enhance.js")

    for path in files:
        if not path.exists():
            print(f"❌ 文件不存在: {path}"); continue
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        # 先剥离旧注入，再重注入（幂等）
        html = html.replace('<link rel="stylesheet" href="lecture-theme.css">\n', '')
        html = html.replace('<script src="lecture-enhance.js"></script>\n', '')
        html = html.replace('</head>', '<link rel="stylesheet" href="lecture-theme.css">\n</head>', 1)
        html = html.replace('</body>', '<script src="lecture-enhance.js"></script>\n</body>', 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ 已增强: {path.name}")


def show_help():
    """显示帮助信息"""
    print("""
OI 工具箱 - 数据管理脚本
用法：
  python3 script.py <command>

题解命令：
  create                交互式添加题解（写入 solutions/records.json）
  list                  列出所有题解

备忘录命令：
  add-lecture           添加讲义（写入 memos/lectures.json，生成 HTML 模板）
  add-content           向课程添加课程内容（含讲义+练习题）
  add-problem           向课程内容添加练习题
  add-student           添加学生账号（写入 students/students.json）
  fetch-submissions     爬取提交记录（更新 students/submissions.json）

竞赛备赛命令：
  add-written           添加笔试专题（含讲义+笔试题目）
  add-written-problem   向已有笔试专题追加题目
  add-mock              添加上机模拟赛
  set-scores            录入模拟赛分数
  set-participants      设置模拟赛参与学生

讲义样式：
  polish [文件名|all]    重写 lecture-theme.css / lecture-enhance.js 并注入讲义 HTML

  Markdown 引用写法（> 开头）→ 自动配色：
    > 直接写内容              淡蓝「定义卡」（默认，无标签）
    > 定义：xxx / 📖 xxx      淡蓝 + 「定义」标签
    > 注意：xxx / ⚠️ xxx      橙色「注意」
    > 提示：xxx / 💡 xxx      绿色「提示」
    > 重点：xxx / 📌 xxx      紫色「重点」
    > 易错：xxx / ❌ xxx      红色「易错」
    > 例题：xxx / 📝 xxx      靛蓝「例题」
    > 证明：xxx / 🔍 xxx      靛蓝「证明」
  注：不带 emoji 时关键词后必须跟「：」或「，」才识别，
      所以「定义域是…」这类正文不会被误判。

  标题样式：
    ## 二级标题             绿色圆圈自动编号
    ### 三级标题            蓝色左边框
    #### 四级标题           靛蓝菱形标记 + 淡灰下划线
    #### 例题：P1001 xxx    靛蓝「例题 N」徽标（全文自动连续编号）
                            标题里的题目链接改为虚线下划线，hover 变靛蓝

  代码块展开策略（标记在导出的 HTML 里都不显示）：
    ① 写在代码块首行注释里（最常用）
         ```cpp
         // @open              这块默认展开
         // @open 快速幂        展开，并在标题栏显示「快速幂」
         // @fold              这块默认折叠
         ```
       注释符按语言写即可：// # -- ; % 都认，@ 号不能省。
    ② 写在代码块前一行的 HTML 注释里
         <!-- @open -->
         ```cpp
    ③ 整篇默认（放文档任意位置，一次生效全篇）
         <!-- @open-all -->    /    <!-- @fold-all -->

    别名：@open = @expand = @show = @展开；@fold = @close = @collapse = @hide = @折叠
    优先级：块内标记 > 文档级 @*-all > 自动判断
    自动判断：代码不超过 """ + str(AUTO_OPEN_MAX_LINES) + """ 行默认展开，更长的默认折叠
              （阈值改 script.py 里的 AUTO_OPEN_MAX_LINES）
    标题栏显示行数，整条标题栏可点击折叠/展开。

其他：
  init                  初始化示例数据
  help                  显示此帮助信息
""")


def main():
    COMMANDS = [
        "create", "list", "add-lecture", "add-content", "add-problem",
        "add-student", "fetch-submissions", "add-written", "add-written-problem",
        "add-mock", "set-scores", "set-participants", "polish", "init", "help"
    ]

    if len(sys.argv) < 2:
        if not _PT:
            show_help()
            print("\n💡 安装 prompt_toolkit 可启用 Tab 补全: pip install prompt_toolkit")
            return
        command = ask("命令 (Tab 补全): ", COMMANDS).lower()
        if not command:
            show_help(); return
    else:
        command = sys.argv[1].lower()

    if command == "create":
        interactive_create()
    elif command == "list":
        list_records()
    elif command == "add-lecture":
        interactive_add_lecture()
    elif command == "add-content":
        interactive_add_content()
    elif command == "add-problem":
        interactive_add_problem_to_content()
    elif command == "add-student":
        interactive_add_student()
    elif command == "fetch-submissions":
        fetch_submissions()
    elif command == "add-written":
        interactive_add_written()
    elif command == "add-written-problem":
        interactive_add_written_problem()
    elif command == "add-mock":
        interactive_add_mock()
    elif command == "set-scores":
        interactive_set_scores()
    elif command == "set-participants":
        interactive_set_participants()
    elif command == "polish":
        target = sys.argv[2] if len(sys.argv) > 2 else 'all'
        polish_html(target)
    elif command == "init":
        init_examples()
    elif command == "help":
        show_help()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()