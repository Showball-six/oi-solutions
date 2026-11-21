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

LECTURE_THEME_CSS = r"""
/* Generated by script.py polish. Edit LECTURE_THEME_CSS in script.py. */ :root {
  color-scheme:light;
  --lec-bg:#f2f6fb;
  --lec-paper:#fff;
  --lec-ink:#23344a;
  --lec-muted:#64748b;
  --lec-line:#dfe5ec;
  --lec-accent:#3569bd;
  --lec-accent-soft:#eaf2ff;
  --lec-code-bg:#f7f9fc;
  --lec-code-head:#f0f4f8;
  --lec-code-border:#dce4ed;
  --lec-code-sub:#687b91;
  --lec-green:#257762;
  --lec-green-bg:#edf8f2;
  --lec-green-line:#c9dfd3;
  --lec-blue:#3569bd;
  --lec-blue-bg:#edf4ff;
  --lec-blue-line:#c5d8f6;
  --lec-orange:#9b641e;
  --lec-orange-bg:#fff8df;
  --lec-orange-line:#f0d694;
  --lec-purple:#73568c;
  --lec-purple-bg:#f5f1f8;
  --lec-purple-line:#dfd2e9;
  --lec-indigo:#b45a46;
  --lec-indigo-bg:#fff1eb;
  --lec-indigo-line:#ecc6b8;
  --lec-red:#ad4652;
  --lec-red-bg:#fbf1f2;
  --lec-red-line:#eccfd3;
  --lec-dot:#d5dfed;
  --lec-highlight:#ffedaa;
  --lec-text:var(--lec-ink);
  --lec-font:'Noto Sans SC',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
  --lec-mono:'SFMono-Regular','Menlo','Consolas','Courier New',monospace;
}
html[data-theme=dark] {
  color-scheme:dark;
  --lec-bg:#111b2a;
  --lec-dot:#2a3a51;
  --lec-highlight:#354c72;
  --lec-paper:#18222f;
  --lec-ink:#e0e8f2;
  --lec-muted:#a6b4c7;
  --lec-line:#334254;
  --lec-accent:#a2c5e3;
  --lec-accent-soft:#233548;
  --lec-code-bg:#121c28;
  --lec-code-head:#1e2c3e;
  --lec-code-border:#34475b;
  --lec-code-sub:#a2b3c9;
  --lec-green:#9bd0b7;
  --lec-green-bg:#21382f;
  --lec-green-line:#3b5a4a;
  --lec-blue:#a2c5e3;
  --lec-blue-bg:#223548;
  --lec-blue-line:#3b546b;
  --lec-orange:#e4be82;
  --lec-orange-bg:#3b3225;
  --lec-orange-line:#665037;
  --lec-purple:#cdb2e1;
  --lec-purple-bg:#352b40;
  --lec-purple-line:#574462;
  --lec-indigo:#eab09a;
  --lec-indigo-bg:#3f302e;
  --lec-indigo-line:#745248;
  --lec-red:#edabb4;
  --lec-red-bg:#402c33;
  --lec-red-line:#68464f;
}
html {
  scroll-padding-top:28px;
}
body.lec-page {
  display:flow-root;
  margin:0!important;
  padding:0!important;
  background:radial-gradient(var(--lec-dot) .8px,transparent .8px) 0 0 / 20px 20px,var(--lec-bg)!important;
  color:var(--lec-ink)!important;
  font-family:var(--lec-font)!important;
  line-height:1.9;
  -webkit-font-smoothing:antialiased;
}
.lec-page *::before,.lec-page *::after {
  box-sizing:border-box;
}
.lec-page * {
  box-sizing:border-box;
  scrollbar-width:thin;
  scrollbar-color:var(--lec-line) transparent;
}
.lec-page ::selection {
  background:var(--lec-blue-line);
  color:var(--lec-ink);
}
.lec-page a:focus-visible,.lec-page button:focus-visible,.lec-page summary:focus-visible {
  outline:3px solid var(--lec-accent);
  outline-offset:4px;
}
.lec-page button,.lec-page summary {
  cursor:pointer;
}
.lec-page button {
  font-family:var(--lec-font);
}
#lec-progress {
  position:fixed;
  top:0;
  left:0;
  width:0;
  height:2px;
  background:var(--lec-accent);
  z-index:110;
}
.lec-page #write {
  width:848px;
  max-width:calc(100% - 48px);
  margin:34px auto 64px;
  padding:48px 58px 72px;
  background:var(--lec-paper);
  color:var(--lec-ink);
  border:1px solid var(--lec-line);
  border-top:1px solid var(--lec-line);
  border-radius:16px;
  position:relative;
  font:16px/1.95 var(--lec-font);
  box-shadow:0 8px 32px #22344b07;
  counter-reset:egc;
  overflow-wrap:anywhere;
}
.lec-page #write.container {
  box-shadow:none;
}
.lec-page #write>.back-link {
  display:none;
}
.lec-page #write>* {
  width:auto!important;
  max-width:100%;
}
.lec-page #write>.lec-code-wrap {
  min-width:0;
}
.lec-page #write .lec-spacer {
  display:none;
}
.lec-page #write>table {
  width:max-content!important;
}
#write h1,#write h2,#write h3,#write h4,#write h5,#write h6 {
  color:var(--lec-ink)!important;
  line-height:1.5;
  scroll-margin-top:28px;
  page-break-after:avoid;
  break-after:avoid;
}
#write h1 {
  font:700 34px/1.4 var(--lec-font);
  letter-spacing:-.035em;
  position:relative;
  border:0!important;
  margin:0 0 34px!important;
  padding:0 68px 24px 0!important;
  border-bottom:1px solid var(--lec-line)!important;
}
#write h2 {
  font-size:24px!important;
  position:relative;
  font-weight:680;
  letter-spacing:-.02em;
  margin:2.2em 0 .9em!important;
  padding:0 0 12px!important;
  border:0!important;
  border-bottom:1px solid var(--lec-line)!important;
  background:none!important;
  border-radius:0!important;
}
#write h2[data-lec-section]::before {
  content:attr(data-lec-section);
  display:inline-block;
  min-width:36px;
  height:32px;
  margin-right:12px;
  padding:7px 8px;
  border:1px solid var(--lec-blue-line);
  border-radius:9px 9px 3px 9px;
  background:var(--lec-accent-soft);
  color:var(--lec-accent);
  font:650 14px/16px var(--lec-mono);
  vertical-align:3px;
}
#write h3 {
  font-size:20px!important;
  font-weight:650;
  margin:1.8em 0 .8em!important;
  padding:0!important;
  border:0!important;
  background:none!important;
}
#write h4 {
  font-size:17px!important;
  font-weight:650;
  margin:1.5em 0 .7em!important;
  padding:0!important;
  border:0!important;
  background:none!important;
}
#write h5,#write h6 {
  font-size:16px;
  font-weight:650;
  margin:1.3em 0 .6em;
}
#write p {
  line-height:1.95;
  margin:0 0 1.1em;
}
#write li {
  margin:.3em 0;
  line-height:1.9;
}
#write strong {
  color:var(--lec-ink);
  font-weight:650;
}
#write a {
  color:var(--lec-accent);
  text-decoration:underline;
  text-underline-offset:3px;
  text-decoration-color:var(--lec-blue-line);
}
#write a:hover {
  text-decoration-color:var(--lec-accent);
}
#write hr {
  border:0;
  border-top:1px solid var(--lec-line);
  margin:2.1em 0;
}
#write h4.lec-eg {
  counter-increment:egc;
}
#write h4.lec-eg::before {
  content:'例题 ' counter(egc);
  display:inline-block;
  margin-right:10px;
  padding:2px 8px;
  border:1px solid var(--lec-indigo-line);
  border-radius:4px;
  color:var(--lec-indigo);
  background:var(--lec-indigo-bg);
  font:600 12px/1.7 var(--lec-font);
  vertical-align:1px;
}
#write h4 a {
  color:var(--lec-ink)!important;
  text-decoration:underline!important;
  text-decoration-color:var(--lec-blue-line)!important;
}
#write blockquote,.typora-export blockquote {
  --callout:var(--lec-muted);
  --callout-bg:var(--lec-code-bg);
  --callout-line:var(--lec-line);
  margin:1.4em 0!important;
  padding:15px 20px!important;
  border:1px solid var(--callout-line)!important;
  border-left:3px solid var(--callout)!important;
  border-radius:0 6px 6px 0!important;
  background:var(--callout-bg)!important;
  color:var(--lec-ink)!important;
  box-shadow:none!important;
}
#write blockquote>:first-child {
  margin-top:0!important;
}
#write blockquote>:last-child {
  margin-bottom:0!important;
}
#write blockquote p {
  line-height:1.85;
}
#write blockquote[data-lec-label]::before {
  content:attr(data-lec-label);
  display:block;
  margin-bottom:8px;
  color:var(--callout);
  font:650 13px/1.6 var(--lec-font);
}
#write blockquote.lec-tip {
  --callout:var(--lec-green);
  --callout-bg:var(--lec-green-bg);
  --callout-line:var(--lec-green-line);
}
#write blockquote.lec-warn {
  --callout:var(--lec-orange);
  --callout-bg:var(--lec-orange-bg);
  --callout-line:var(--lec-orange-line);
}
#write blockquote.lec-key {
  --callout:var(--lec-purple);
  --callout-bg:var(--lec-purple-bg);
  --callout-line:var(--lec-purple-line);
}
#write blockquote.lec-example {
  --callout:var(--lec-indigo);
  --callout-bg:var(--lec-indigo-bg);
  --callout-line:var(--lec-indigo-line);
}
#write blockquote.lec-pitfall {
  --callout:var(--lec-red);
  --callout-bg:var(--lec-red-bg);
  --callout-line:var(--lec-red-line);
}
#write blockquote blockquote {
  margin:.8em 0!important;
  background:var(--lec-paper)!important;
}
#write blockquote>h4:first-child {
  margin-top:0!important;
}
#write :not(pre)>code {
  font-family:var(--lec-mono);
  font-size:.88em;
  background:var(--lec-accent-soft)!important;
  color:var(--lec-accent)!important;
  padding:2px 5px;
  border:0;
  border-radius:3px;
}
#write img {
  max-width:100%;
  height:auto;
  display:block;
  margin:1.6em auto;
  border-radius:4px;
}
#write .md-image {
  max-width:100%;
}
#write .katex-display,#write mjx-container[display=true],#write .MathJax_Display {
  overflow-x:auto;
  overflow-y:hidden;
  max-width:100%;
  padding:8px 0;
}
#write .katex,#write mjx-container {
  color:var(--lec-ink);
}
#write table {
  display:block;
  width:max-content;
  max-width:100%;
  overflow:auto;
  border-collapse:collapse;
  border-radius:0;
  box-shadow:none;
  font-size:14px;
  line-height:1.75;
  margin:1.6em 0;
}
#write table th {
  font-weight:650;
  background:var(--lec-accent-soft)!important;
  color:var(--lec-ink)!important;
  border:1px solid var(--lec-line)!important;
  padding:10px 14px!important;
  white-space:nowrap;
}
#write table td {
  border:1px solid var(--lec-line)!important;
  padding:10px 14px!important;
  min-width:70px;
}
#write table tr {
  background:var(--lec-paper)!important;
  border:0;
}
#write table tr:nth-child(2n) {
  background:var(--lec-code-bg)!important;
}
#write tbody tr:hover {
  background:var(--lec-accent-soft)!important;
}
.lec-code-wrap {
  margin:1.6em 0;
  border:1px solid var(--lec-code-border);
  border-radius:10px;
  overflow:hidden;
  background:var(--lec-code-bg);
  box-shadow:4px 4px 0 var(--lec-accent-soft);
}
.lec-code-header {
  display:flex;
  align-items:center;
  gap:12px;
  padding:10px 13px;
  background:var(--lec-code-head);
  cursor:pointer;
  user-select:none;
  border-bottom:1px solid transparent;
  min-height:47px;
}
.lec-code-wrap.is-open .lec-code-header {
  border-bottom-color:var(--lec-code-border);
}
.lec-lang-name {
  font:650 12px var(--lec-mono);
  border:1px solid var(--lec-blue-line);
  background:var(--lec-accent-soft);
  padding:5px 8px;
  border-radius:5px;
  color:var(--lec-accent);
  text-transform:uppercase;
  flex:none;
}
.lec-code-title {
  font-size:13px;
  font-weight:550;
  color:var(--lec-ink);
  flex:1;
  min-width:0;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.lec-code-title:empty {
  display:none;
}
.lec-code-lines {
  font:12px var(--lec-mono);
  color:var(--lec-code-sub);
  flex:none;
  margin-left:auto;
}
.lec-header-actions {
  display:flex;
  gap:6px;
  flex-shrink:0;
}
.lec-header-btn {
  border:1px solid var(--lec-code-border);
  border-radius:4px;
  background:var(--lec-paper);
  color:var(--lec-code-sub);
  padding:4px 9px;
  font:13px/1.5 var(--lec-font);
  cursor:pointer;
}
.lec-header-btn:hover {
  color:var(--lec-accent);
  border-color:var(--lec-accent);
}
.lec-header-btn.is-done {
  color:var(--lec-green);
}
.lec-code-inner {
  overflow:hidden;
  max-height:0;
  transition:max-height .24s ease;
}
.lec-code-inner.is-settled {
  overflow:visible;
}
.lec-code-inner>pre,.lec-code-inner>pre.md-fences {
  margin:0!important;
  padding:15px!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  background:var(--lec-code-bg)!important;
  font:14px/1.75 var(--lec-mono);
}
.lec-code-inner pre code {
  font:inherit;
  color:var(--lec-ink);
  background:none!important;
}
.lec-code-inner .CodeMirror,.lec-code-inner .CodeMirror-scroll {
  background:var(--lec-code-bg)!important;
  color:var(--lec-ink)!important;
  font:14px/1.75 var(--lec-mono)!important;
}
.lec-code-inner .CodeMirror-linenumber {
  color:var(--lec-code-sub)!important;
}
.lec-code-inner .CodeMirror-gutters {
  background:var(--lec-code-bg)!important;
  border-right:1px solid var(--lec-code-border)!important;
}
.lec-code-inner .CodeMirror-lines {
  padding:4px 0!important;
}
.lec-code-inner .CodeMirror-line {
  font:inherit!important;
  background:none!important;
}
html[data-theme=dark] .lec-code-inner .cm-s-inner {
  color:var(--lec-ink)!important;
}
html[data-theme=dark] .lec-code-inner .cm-keyword {
  color:#c0b7f0!important;
}
html[data-theme=dark] .lec-code-inner .cm-number {
  color:#e5bf86!important;
}
html[data-theme=dark] .lec-code-inner .cm-string {
  color:#a7cba8!important;
}
html[data-theme=dark] .lec-code-inner .cm-comment {
  color:#8c9db3!important;
}
html[data-theme=dark] .lec-code-inner .cm-variable,html[data-theme=dark] .lec-code-inner .cm-variable-2,html[data-theme=dark] .lec-code-inner .cm-operator {
  color:var(--lec-ink)!important;
}
.lec-outline {
  width:848px;
  max-width:calc(100% - 48px);
  margin:24px auto 0;
  font-family:var(--lec-font);
  color:var(--lec-muted);
}
.lec-outline summary {
  font-size:14px;
  cursor:pointer;
}
.lec-outline nav {
  display:grid;
  gap:3px;
  margin-top:13px;
}
.lec-outline a {
  font-size:13px;
  line-height:1.7;
  padding:5px 9px;
  border-left:2px solid transparent;
  text-decoration:none;
  color:var(--lec-muted);
  display:block;
  overflow-wrap:anywhere;
}
.lec-outline a[data-level='3'] {
  padding-left:22px;
  font-size:12px;
}
.lec-outline a:hover {
  color:var(--lec-accent);
}
.lec-outline a[aria-current=location] {
  border-left-color:var(--lec-accent);
  color:var(--lec-accent);
  background:var(--lec-accent-soft);
}
.lec-status {
  position:absolute;
  width:1px;
  height:1px;
  overflow:hidden;
  clip-path:inset(50%);
}
.lec-demo {
  margin:1.7em 0;
  border:1px solid var(--lec-line);
  border-radius:6px;
  overflow:hidden;
  background:var(--lec-paper);
  box-shadow:none;
}
.lec-demo-head {
  display:flex;
  align-items:center;
  gap:10px;
  padding:12px 15px;
  background:var(--lec-code-head);
  border-bottom:1px solid var(--lec-line);
}
.lec-demo-badge {
  font:650 12px var(--lec-font);
  color:var(--lec-accent);
}
.lec-demo-title {
  font-size:14px;
  font-weight:600;
  color:var(--lec-ink);
  flex:1;
  min-width:0;
}
.lec-demo-open {
  font-size:13px;
  color:var(--lec-accent)!important;
  text-decoration:none!important;
  flex-shrink:0;
}
.lec-demo iframe {
  display:block;
  width:100%!important;
  border:0!important;
  margin:0!important;
  background:var(--lec-code-bg);
}
/* 算法实验笔记：书签标题、章节页签与批注便签。 */
#write h1::after {
  content:'{ }';
  position:absolute;
  right:2px;
  top:0;
  display:grid;
  place-items:center;
  width:48px;
  height:48px;
  border:1px solid var(--lec-blue-line);
  border-radius:14px 14px 5px 14px;
  background:var(--lec-accent-soft);
  color:var(--lec-accent);
  font:600 21px var(--lec-mono);
  transform:rotate(7deg);
}
.lec-title-ink {
  background:linear-gradient(transparent 75%,var(--lec-highlight) 75%,var(--lec-highlight) 96%,transparent 96%);
  padding-bottom:2px;
  -webkit-box-decoration-break:clone;
  box-decoration-break:clone;
}
#write h2::after {
  content:'';
  position:absolute;
  left:0;
  bottom:-2px;
  width:46px;
  height:4px;
  border-radius:4px;
  background:var(--lec-orange-line);
}
.lec-page #write::before {
  content:'';
  position:absolute;
  top:108px;
  left:-6px;
  width:12px;
  height:12px;
  border:1px solid var(--lec-line);
  border-radius:50%;
  background:var(--lec-bg);
  box-shadow:0 120px 0 var(--lec-bg),0 240px 0 var(--lec-bg);
  pointer-events:none;
}
#write blockquote[data-lec-label] {
  position:relative;
  border-left:1px solid var(--callout-line)!important;
  border-top:3px solid var(--callout)!important;
  border-radius:8px!important;
}
#write blockquote[data-lec-label]::before {
  display:inline-block;
  border:1px solid var(--callout-line);
  padding:2px 8px;
  border-radius:4px;
  margin-bottom:10px;
  background:var(--lec-paper);
}
#write blockquote[data-lec-label]::after {
  content:'';
  position:absolute;
  top:-8px;
  right:18px;
  width:38px;
  height:13px;
  background:var(--callout-line);
  opacity:.65;
  transform:rotate(-8deg);
  border-radius:1px;
}
#write h4.lec-eg::before {
  border-radius:7px 7px 2px 7px;
  padding:3px 10px;
  box-shadow:2px 2px 0 var(--lec-indigo-line);
}
.lec-outline a {
  border-radius:0 7px 7px 0;
}
.lec-outline a[aria-current=location] {
  font-weight:600;
}
@media(min-width:1200px) {
  .lec-page.lec-has-outline #write {
    margin-left:calc(50% - 352px);
    margin-right:0;
  }
  .lec-outline {
    position:fixed;
    top:36px;
    left:calc(50% - 596px);
    width:208px;
    max-height:calc(100vh - 72px);
    overflow:auto;
    margin:0;
    padding-right:10px;
  }
  .lec-outline summary {
    list-style:none;
    font-weight:600;
    font-size:13px;
    pointer-events:none;
    color:var(--lec-ink);
    padding:0 9px;
  }
  .lec-outline summary::-webkit-details-marker {
    display:none;
  }
}
@media(max-width:760px) {
  .lec-page #write {
    max-width:calc(100% - 28px);
    margin:20px auto 40px;
    padding:30px 22px 42px;
    font-size:16px;
    line-height:1.9;
  }
  .lec-outline {
    max-width:calc(100% - 40px);
    margin-top:20px;
  }
  .lec-outline a[data-level='3'] {
    font-size:13px;
  }
  #write h1 {
    font-size:27px;
    margin-bottom:28px!important;
  }
  #write h2 {
    font-size:22px!important;
  }
  #write h3 {
    font-size:19px!important;
  }
  #write blockquote {
    padding:13px 14px!important;
  }
  .lec-code-header {
    flex-wrap:wrap;
    gap:8px;
    padding:9px 10px;
  }
  .lec-code-title {
    flex-basis:45%;
  }
  .lec-code-lines {
    font-size:11px;
  }
  .lec-header-btn {
    font-size:12px;
    padding:4px 7px;
  }
  .lec-code-inner>pre {
    padding:12px!important;
  }
}
@media(prefers-reduced-motion:reduce) {
  .lec-page * {
    scroll-behavior:auto!important;
    transition:none!important;
    animation:none!important;
  }
}
@page {
  size:A4;
  margin:18mm 16mm;
}
@media print {
  :root,html[data-theme=dark] {
    color-scheme:light;
    --lec-bg:#fff;
    --lec-dot:transparent;
    --lec-highlight:transparent;
    --lec-paper:#fff;
    --lec-ink:#111;
    --lec-muted:#555;
    --lec-line:#ccc;
    --lec-accent:#233e56;
    --lec-accent-soft:#f1f3f5;
    --lec-code-bg:#f7f7f7;
    --lec-code-head:#f1f1f1;
    --lec-code-border:#ccc;
    --lec-code-sub:#555;
    --lec-blue-bg:#f5f7f9;
    --lec-green-bg:#f5f7f5;
    --lec-orange-bg:#faf8f4;
    --lec-purple-bg:#f7f5f8;
    --lec-indigo-bg:#f5f6f9;
    --lec-red-bg:#faf6f6;
  }
  #write h1::after,#write h2::after,.lec-page #write::before,#write blockquote[data-lec-label]::after {display:none!important;}
  .lec-title-ink {background:none;}
  .lec-outline,#lec-progress,.lec-header-actions {
    display:none!important;
  }
  .lec-page {
    background:#fff!important;
  }
  .lec-page #write {
    width:100%!important;
    max-width:none!important;
    margin:0!important;
    padding:0!important;
    border:0!important;
    box-shadow:none!important;
    font-size:11pt!important;
    line-height:1.75;
  }
  #write h1 {
    font-size:24pt;
  }
  #write h2 {
    font-size:17pt!important;
  }
  #write h3 {
    font-size:14pt!important;
  }
  #write h4 {
    font-size:12pt!important;
  }
  #write blockquote {
    break-inside:avoid;
    box-shadow:none;
  }
  .lec-code-inner {
    max-height:none!important;
    overflow:visible!important;
  }
  .lec-code-inner .CodeMirror-scroll {
    overflow:visible!important;
  }
  .lec-code-wrap {
    box-shadow:none;
    break-inside:auto;
  }
  .lec-code-header {
    padding:6px 10px;
  }
  .lec-code-inner>pre {
    font-size:9pt!important;
  }
  .lec-demo iframe {
    display:none;
  }
  .lec-demo-head {
    border:0;
  }
  #write table {
    overflow:visible;
    max-width:100%;
  }
  #write img {
    max-height:220mm;
    object-fit:contain;
  }
  #write a {
    color:inherit;
  }
  html[data-theme=dark] .lec-code-inner .cm-s-inner,html[data-theme=dark] .lec-code-inner .cm-variable,html[data-theme=dark] .lec-code-inner .cm-operator {
    color:#111!important;
  }
  html[data-theme=dark] .lec-code-inner .cm-keyword {
    color:#385881!important;
  }
  html[data-theme=dark] .lec-code-inner .cm-comment {
    color:#666!important;
  }
  html[data-theme=dark] .lec-code-inner .cm-string {
    color:#385d3e!important;
  }
  html[data-theme=dark] .lec-code-inner .cm-number {
    color:#745520!important;
  }
}
/* 目录保留 Markdown 行内样式与公式；控制按钮不再占据顶部栏。 */
.lec-outline a code {
  font:500 .92em var(--lec-mono);
  color:var(--lec-accent);
  background:var(--lec-accent-soft);
  border-radius:3px;
  padding:1px 3px;
}
.lec-outline a strong,.lec-outline a b {font-weight:650;}
.lec-outline a em,.lec-outline a i {font-style:italic;}
.lec-outline mjx-container,.lec-outline .MathJax,.lec-outline .katex {
  font-size:1em;
  margin:0!important;
  color:inherit;
  max-width:100%;
}
.lec-outline a svg {max-width:100%;}
.lec-outline a img {max-height:1.3em;max-width:100%;vertical-align:middle;}
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
  'use strict';
  const article = document.querySelector('#write') || document.querySelector('.typora-export') || document.querySelector('.container');
  if (!article || document.documentElement.dataset.lecEnhanced === '1') return;
  document.documentElement.dataset.lecEnhanced = '1';
  if (!article.id) article.id = 'write';
  document.body.classList.add('lec-page');
  const mainTitle=article.querySelector('h1');
  if(mainTitle){const ink=document.createElement('span');ink.className='lec-title-ink';while(mainTitle.firstChild)ink.append(mainTitle.firstChild);mainTitle.append(ink);}
  const status=document.createElement('div');status.className='lec-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');document.body.append(status);
  article.querySelectorAll('p').forEach(p=>{if(!p.textContent.trim()&&!p.querySelector('img,svg,iframe,video,audio,canvas,mjx-container,.MathJax,.katex,.mathjax-block,br'))p.classList.add('lec-spacer');});
  const headings=Array.from(article.querySelectorAll('h2,h3'));
  // 继承 Markdown 已渲染的行内结构；不把标题压成纯文本。
  function copyHeadingContent(heading, link, index) {
    const copy=heading.cloneNode(true);
    copy.removeAttribute('id');
    const renderedMath=copy.querySelector('mjx-container,.MathJax,.katex');
    copy.querySelectorAll('script,style,button,input,textarea,select').forEach(node=>{
      if(!renderedMath && node.tagName==='SCRIPT' && /^math\/tex/.test(node.type))node.replaceWith(document.createTextNode(node.textContent));
      else node.remove();
    });
    // TOC 项本身就是链接，标题中的链接只保留内容，避免嵌套链接。
    copy.querySelectorAll('a').forEach(node=>node.replaceWith(...node.childNodes));
    const ids=new Map();const used=new Set();
    copy.querySelectorAll('[id]').forEach((node,n)=>{
      const old=node.id;let id='lec-toc-'+index+'-'+n;
      while(document.getElementById(id)||used.has(id))id+='-';
      used.add(id);if(!ids.has(old))ids.set(old,id);node.id=id;
    });
    copy.querySelectorAll('*').forEach(node=>{
      for(const attribute of Array.from(node.attributes)){
        if(/^on/i.test(attribute.name)||['tabindex','contenteditable'].includes(attribute.name)){node.removeAttribute(attribute.name);continue;}
        let value=attribute.value;
        if((attribute.localName==='href')&&value.startsWith('#')&&ids.has(value.slice(1)))value='#'+ids.get(value.slice(1));
        if(['aria-labelledby','aria-describedby'].includes(attribute.name))value=value.split(/\s+/).map(id=>ids.get(id)||id).join(' ');
        value=value.replace(/url\((['"]?)#([^)'"]+)\1\)/g,(all,quote,id)=>ids.has(id)?'url(#'+ids.get(id)+')':all);
        if(value!==attribute.value){if(attribute.namespaceURI)node.setAttributeNS(attribute.namespaceURI,attribute.name,value);else node.setAttribute(attribute.name,value);}
      }
    });
    link.replaceChildren(...copy.childNodes);
  }
  const tocLinks=[];
  if(headings.length){
    const outline=document.createElement('details');outline.className='lec-outline';
    const summary=document.createElement('summary');summary.textContent='本讲目录';
    const nav=document.createElement('nav');nav.setAttribute('aria-label','本讲目录');
    let section=0;
    headings.forEach((heading,index)=>{
      if(!heading.id || document.getElementById(heading.id)!==heading){let id='lec-section-'+(index+1);while(document.getElementById(id))id+='-';heading.id=id;}
      if(heading.tagName==='H2'){section++;if(!/^(?:\d+(?:[.．、\s]|$)|[一二三四五六七八九十]+[、．.\s]|第.{1,8}[章节])/.test(heading.textContent.trim()))heading.dataset.lecSection=String(section).padStart(2,'0');}
      const link=document.createElement('a');link.href='#'+encodeURIComponent(heading.id);link.dataset.level=heading.tagName.slice(1);copyHeadingContent(heading,link,index);
      link.addEventListener('click',()=>{if(!matchMedia('(min-width:1200px)').matches)outline.open=false;});nav.append(link);tocLinks.push(link);
      // MathJax 异步完成时同步目录公式，观察范围不包含目录自身。
      let pending=false;
      new MutationObserver(()=>{if(!pending){pending=true;queueMicrotask(()=>{pending=false;copyHeadingContent(heading,link,index);});}}).observe(heading,{childList:true,subtree:true,characterData:true});
    });
    outline.append(summary,nav);document.body.prepend(outline);document.body.classList.add('lec-has-outline');
    const wide=matchMedia('(min-width:1200px)');const resize=()=>{outline.open=wide.matches;};resize();wide.addEventListener('change',resize);
    summary.addEventListener('click',event=>{if(wide.matches)event.preventDefault();});
    article.querySelectorAll('.md-toc').forEach(toc=>toc.hidden=true);
  }
  // 1. 阅读进度条
  const bar = document.createElement('div');
  bar.id = 'lec-progress';
  document.body.prepend(bar);
  let queued=false;
  function updateReading(){
    queued=false;
    const distance=Math.max(1,document.documentElement.scrollHeight-innerHeight);
    bar.style.width=Math.max(0,Math.min(100,window.scrollY/distance*100))+'%';
    let current=0;headings.forEach((heading,index)=>{if(heading.getBoundingClientRect().top<=40)current=index;});
    tocLinks.forEach((link,index)=>{if(index===current)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
  }
  const queueReading=()=>{if(!queued){queued=true;requestAnimationFrame(updateReading);}};
  window.addEventListener('scroll',queueReading,{passive:true});window.addEventListener('resize',queueReading);queueReading();

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
    if (pre.closest('.CodeMirror') || pre.closest('.lec-code-wrap')) return;

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
    toggleBtn.type='button';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'lec-header-btn';
    copyBtn.type='button';
    copyBtn.textContent = '复制';
    copyBtn.addEventListener('click', function (e) {
      e.stopPropagation();                  // 别连带触发 header 的折叠
      // 首行标记可能已被删掉 → 复制时重新取一次当前 DOM
      const src = isCM ? pre.querySelectorAll('.CodeMirror-code pre') : null;
      const text = src && src.length
        ? Array.from(src).map(function (l) { return l.textContent.replace(/​/g, '').replace(/ /g, ' '); }).join('\n')
        : code ? code.textContent : '';
      Promise.resolve().then(()=>navigator.clipboard.writeText(text)).then(function () {
        copyBtn.textContent = '已复制';
        copyBtn.classList.add('is-done');
        setTimeout(function () {
          copyBtn.textContent = '复制';
          copyBtn.classList.remove('is-done');
        }, 2000);
        status.textContent='代码已复制';
      }).catch(function(){copyBtn.textContent='复制失败';status.textContent='无法访问剪贴板，请手动选择代码复制';setTimeout(()=>copyBtn.textContent='复制',2000);});
    });

    actions.appendChild(toggleBtn);
    actions.appendChild(copyBtn);
    header.appendChild(actions);

    const inner = document.createElement('div');
    inner.className = 'lec-code-inner';
    inner.id='lec-code-'+document.querySelectorAll('.lec-code-wrap').length;
    toggleBtn.setAttribute('aria-controls',inner.id);

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
      toggleBtn.textContent = open ? '收起' : '展开';
      toggleBtn.setAttribute('aria-expanded',String(open));
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

    try{if (frame.contentDocument && frame.contentDocument.readyState === 'complete') fit();}catch{}
    window.addEventListener('resize', fit);
  });
})();
"""


def render_polished_html(source, css_href='lecture-theme.css', js_href='lecture-enhance.js'):
    """按真实 HTML 标签位置更新增强层，不触碰脚本/注释内的 HTML 字符串。"""
    import html as html_lib
    from html.parser import HTMLParser
    from urllib.parse import urlsplit
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))

    class InjectionParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.removals = []
            self.head = None
            self.body = None
            self.script_start = None

        def position(self):
            line, column = self.getpos()
            return offsets[line - 1] + column

        def end(self, start):
            return source.index('>', start) + 1

        def remove(self, start, end):
            if source.startswith('\r\n', end): end += 2
            elif source.startswith('\n', end): end += 1
            self.removals.append((start, end, ''))

        @staticmethod
        def generated(tag, attrs):
            if tag == 'link':
                return urlsplit(attrs.get('href') or '').path.rsplit('/', 1)[-1] == 'lecture-theme.css'
            if tag == 'script':
                return (attrs.get('id') == 'lecture-theme-init' or
                        urlsplit(attrs.get('src') or '').path.rsplit('/', 1)[-1] == 'lecture-enhance.js')
            return False

        def handle_starttag(self, tag, attributes):
            attrs = dict(attributes)
            if self.generated(tag, attrs):
                start = self.position()
                if tag == 'link': self.remove(start, start + len(self.get_starttag_text()))
                elif tag == 'script': self.script_start = start

        def handle_startendtag(self, tag, attributes):
            if self.generated(tag, dict(attributes)):
                start = self.position()
                self.remove(start, start + len(self.get_starttag_text()))

        def handle_endtag(self, tag):
            start = self.position()
            if tag == 'script' and self.script_start is not None:
                self.remove(self.script_start, self.end(start))
                self.script_start = None
            elif tag == 'head' and self.head is None: self.head = start
            elif tag == 'body' and self.body is None: self.body = start

    parser = InjectionParser()
    parser.feed(source)
    parser.close()
    if parser.head is None or parser.body is None:
        raise ValueError('不是完整 HTML 文档，需包含真实 </head> 与 </body> 标签')
    init = '<script id="lecture-theme-init">try{document.documentElement.dataset.theme=localStorage.getItem("showball-theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light")}catch(e){}</script>\n'
    link = '<link rel="stylesheet" href="'+html_lib.escape(css_href, quote=True)+'">\n'
    script = '<script src="'+html_lib.escape(js_href, quote=True)+'"></script>\n'
    edits = parser.removals + [(parser.head, parser.head, init + link), (parser.body, parser.body, script)]
    for start, end, replacement in sorted(edits, key=lambda item:item[0], reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def polish_html(target=None, dry_run=False):
    """生成算法实验笔记增强层。--dry-run 仅检查，不写文件。"""
    import os
    root = MEMOS_DIR.resolve()
    if target and str(target).lower() != 'all':
        path = Path(target)
        if not path.is_absolute() and path.parts[0].lower() != MEMOS_DIR.name.lower():
            path = MEMOS_DIR / path
        files = [path]
    else:
        files = {p for p in MEMOS_DIR.glob('*.html') if p.name.lower().startswith('lec-')}
        for lecture in load_json(MEMOS_DIR / 'lectures.json', []):
            href = lecture.get('href', '')
            if not href: continue
            path = Path(href)
            if path.parts and path.parts[0].lower() == MEMOS_DIR.name.lower():
                path = MEMOS_DIR.joinpath(*path.parts[1:])
            elif not path.is_absolute():
                path = MEMOS_DIR / path
            if path.is_file() and path.resolve().is_relative_to(root): files.add(path)
        files = sorted(files, key=lambda p:str(p).lower())
    prepared = []
    for path in files:
        if not path.is_file() or path.suffix.lower() != '.html' or not path.resolve().is_relative_to(root):
            print(f'❌ 不是 memos 内有效的讲义 HTML: {path}'); continue
        try:
            css_href = os.path.relpath(MEMOS_DIR / 'lecture-theme.css', path.parent).replace('\\', '/')
            js_href = os.path.relpath(MEMOS_DIR / 'lecture-enhance.js', path.parent).replace('\\', '/')
            old = path.read_text(encoding='utf-8')
            prepared.append((path, old, render_polished_html(old, css_href, js_href)))
        except (OSError, ValueError) as error:
            print(f'❌ 跳过 {path.name}: {error}')
    if not prepared:
        print('❌ 未找到可加工的讲义 HTML'); return []
    if not dry_run:
        (MEMOS_DIR / 'lecture-theme.css').write_text(LECTURE_THEME_CSS, encoding='utf-8')
        (MEMOS_DIR / 'lecture-enhance.js').write_text(_build_enhance_js(), encoding='utf-8')
    for path, old, enhanced in prepared:
        if not dry_run and old != enhanced: path.write_text(enhanced, encoding='utf-8')
        print(f'{"🔎 将加工" if dry_run else "✅ 已增强"}: {path.name}')
    print(f'{"只读检查" if dry_run else "算法实验笔记主题已应用"}：{len(prepared)} 份讲义')
    return [path for path, _, _ in prepared]


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
  polish [文件名|all] [--dry-run]   算法实验笔记主题；只读预览不写文件

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
        import argparse
        parser = argparse.ArgumentParser(prog='python script.py polish', description='生成算法实验笔记风格讲义，保留 Typora 原文')
        parser.add_argument('target', nargs='?', default='all', help='讲义文件名或 all')
        parser.add_argument('--dry-run', action='store_true', help='只列出将加工的讲义，不写文件')
        args = parser.parse_args(sys.argv[2:])
        polish_html(args.target, dry_run=args.dry_run)
    elif command == "init":
        init_examples()
    elif command == "help":
        show_help()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
