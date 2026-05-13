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

    pid = input("题号 (如 P3372, CF1A, ABC086A): ").strip().upper()
    if not pid:
        print("❌ 题号不能为空")
        return

    title = input("题目标题: ").strip()
    if not title:
        print("❌ 标题不能为空")
        return

    # 直接询问题目链接
    problem_url = input("题目链接 (粘贴 URL，留空则为 #): ").strip() or "#"

    source = input("来源 (洛谷/CF/AtCoder，默认洛谷): ").strip() or "洛谷"

    print("\n可选难度:")
    difficulties = ["入门", "普及-", "普及/提高-", "普及+/提高",
                    "提高+/省选-", "省选/NOI-", "NOI"]
    for i, d in enumerate(difficulties, 1):
        print(f" {i}. {d}")

    diff_choice = input("选择难度 (1-7，默认4): ").strip()
    diff = difficulties[int(diff_choice)-1] if diff_choice.isdigit() and 1 <= int(diff_choice) <= 7 else "普及/提高"

    tags_input = input("标签 (用逗号分隔，可选): ").strip()
    tags = [t.strip() for t in tags_input.split(',')] if tags_input else []

    # 创建记录
    record = create_json_record(pid, title, diff, source, tags, problem_url)

    print("\n" + "-"*50)
    print(f"ID: {record['id']}")
    print(f"题号: {pid}")
    print(f"标题: {title}")
    print(f"链接: {problem_url}")
    print(f"难度: {diff}")
    print(f"标签: {', '.join(tags) if tags else '(无)'}")
    print("-"*50)

    confirm = input("\n确认创建？ (y/n): ").strip().lower()
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

    title = input("讲义标题: ").strip()
    if not title:
        print("❌ 标题不能为空"); return

    lectures_preview = load_json(LECTURES_FILE, default=[])
    nums_preview = [int(l['id'].split('-')[1]) for l in lectures_preview if '-' in l.get('id', '')]
    next_num_preview = max(nums_preview, default=0) + 1
    auto_slug = f"lec-{str(next_num_preview).zfill(3)}"
    slug_input = input(f"Slug (回车使用自动生成的 '{auto_slug}'，或输入自定义): ").strip().lower()
    slug = slug_input if slug_input else auto_slug

    courses_data = load_json(COURSES_FILE)
    course_names = [c['title'] for c in courses_data.get('courses', [])]
    print("\n可选课程 (空格分隔编号，可多选，直接回车跳过):")
    for i, name in enumerate(course_names, 1):
        print(f"  {i}. {name}")
    course_input = input("选择课程: ").strip()
    courses = [COURSE_IDS[int(x)-1] for x in course_input.split()
               if x.isdigit() and 1 <= int(x) <= len(COURSE_IDS)]

    topic_names = ["动态规划", "基础算法", "数据结构", "数学", "图论", "杂项", "字符串"]
    print("\n可选知识点 (空格分隔编号，可多选，直接回车跳过):")
    for i, name in enumerate(topic_names, 1):
        print(f"  {i}. {name}")
    topic_input = input("选择知识点: ").strip()
    topics = [TOPIC_IDS[int(x)-1] for x in topic_input.split()
              if x.isdigit() and 1 <= int(x) <= len(TOPIC_IDS)]

    tags_input = input("标签 (逗号分隔，可选): ").strip()
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
    confirm = input("确认? (y/n): ").strip().lower()
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
    choice = input("课程编号: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(courses)):
        print("❌ 无效选择"); return
    course = courses[int(choice) - 1]

    title = input("内容标题 (如 AC自动机专题): ").strip()
    if not title:
        print("❌ 标题不能为空"); return

    contents = course.setdefault('contents', [])
    nums = [int(c['id'].split('-')[1]) for c in contents if '-' in c.get('id', '')]
    next_num = max(nums, default=0) + 1
    content_id = f"content-{str(next_num).zfill(3)}"

    # 关联讲义
    lectures_data = load_json(LECTURES_FILE, default=[])
    course_lecs = [l for l in lectures_data if course['id'] in l.get('courses', [])]
    linked_lecs = []
    if course_lecs:
        print(f"\n该课程下的讲义 (空格分隔编号，直接回车跳过):")
        for i, l in enumerate(course_lecs, 1):
            print(f"  {i}. {l['title']}")
        lec_input = input("选择讲义: ").strip()
        linked_lecs = [course_lecs[int(x)-1]['id'] for x in lec_input.split()
                       if x.isdigit() and 1 <= int(x) <= len(course_lecs)]

    # 添加练习题
    problems = []
    platforms = ["luogu", "codeforces", "atcoder"]
    print("\n添加练习题 (输入 q 结束):")
    while True:
        pid = input("  题号 (q结束): ").strip()
        if pid.lower() == 'q' or not pid: break
        prob_title = input("  题目标题: ").strip()
        print("  平台: 1.洛谷  2.Codeforces  3.AtCoder")
        plat = input("  选择: ").strip()
        if not plat.isdigit() or not (1 <= int(plat) <= 3):
            print("  ❌ 无效平台，跳过"); continue
        problems.append({"pid": pid, "platform": platforms[int(plat)-1], "title": prob_title})
        print(f"  ✓ 已添加 {pid}")

    content = {"id": content_id, "title": title, "lectures": linked_lecs, "problems": problems}
    contents.append(content)
    save_json(COURSES_FILE, data)
    print(f"✅ 已添加课程内容「{title}」({content_id}) 到「{course['title']}」")


def interactive_add_problem_to_content():
    """向课程内容添加练习题"""
    print("\n" + "="*50)
    print("➕ 向课程内容添加练习题")
    print("="*50)

    data = load_json(COURSES_FILE)
    courses = data.get('courses', [])

    print("选择课程:")
    for i, c in enumerate(courses, 1):
        print(f"  {i}. {c['title']}")
    choice = input("课程编号: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(courses)):
        print("❌ 无效选择"); return
    course = courses[int(choice) - 1]

    contents = course.get('contents', [])
    if not contents:
        print("❌ 该课程暂无内容，请先用 add-content 添加"); return

    print("选择课程内容:")
    for i, c in enumerate(contents, 1):
        print(f"  {i}. {c['title']}")
    choice2 = input("内容编号: ").strip()
    if not choice2.isdigit() or not (1 <= int(choice2) <= len(contents)):
        print("❌ 无效选择"); return
    content = contents[int(choice2) - 1]

    platforms = ["luogu", "codeforces", "atcoder"]
    print("平台: 1.洛谷  2.Codeforces  3.AtCoder")
    plat = input("选择: ").strip()
    if not plat.isdigit() or not (1 <= int(plat) <= 3):
        print("❌ 无效选择"); return

    pid   = input("题号: ").strip()
    title = input("题目标题: ").strip()
    if not pid or not title:
        print("❌ 题号和标题不能为空"); return

    content.setdefault('problems', []).append({"pid": pid, "platform": platforms[int(plat)-1], "title": title})
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

    name = input("学生姓名: ").strip()
    if not name:
        print("❌ 姓名不能为空"); return

    lg_uid    = input("洛谷 UID (数字，留空跳过): ").strip() or None
    cf_handle = input("Codeforces handle (留空跳过): ").strip() or None
    ac_handle = input("AtCoder handle (留空跳过): ").strip() or None

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

    luogu_pids, cf_pids, ac_pids = set(), set(), set()
    for course in courses_data.get('courses', []):
        for content in course.get('contents', []):
            for p in content.get('problems', []):
                if p['platform'] == 'luogu':        luogu_pids.add(p['pid'])
                elif p['platform'] == 'codeforces': cf_pids.add(p['pid'])
                elif p['platform'] == 'atcoder':    ac_pids.add(p['pid'])

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
        print(f"\n处理学生: {student['name']} ({sid})")

        if student.get('luogu_uid') and luogu_pids:
            uid = student['luogu_uid']
            headers = {"User-Agent": "Mozilla/5.0"}
            for pid in luogu_pids:
                if result[sid]['luogu'].get(pid) == 'ac':
                    print(f"  洛谷 {pid}: 已AC，跳过")
                    continue
                try:
                    import re as _re
                    # AC check (status=2)
                    r = requests.get(f"https://www.luogu.com.cn/problem/list?uid={uid}&status=2&keyword={pid}",
                                     headers=headers, timeout=10)
                    scripts = _re.findall(r'<script[^>]*>(.*?)</script>', r.text, _re.DOTALL)
                    ac_pids_found = set()
                    attempted_pids_found = set()
                    for s in scripts:
                        if 'instance' in s:
                            try:
                                d = json.loads(s)
                                ac_pids_found = {p['pid'] for p in d.get('data',{}).get('problems',{}).get('result',[])}
                            except: pass
                    # attempted check (status=1)
                    r2 = requests.get(f"https://www.luogu.com.cn/problem/list?uid={uid}&status=1&keyword={pid}",
                                      headers=headers, timeout=10)
                    for s in _re.findall(r'<script[^>]*>(.*?)</script>', r2.text, _re.DOTALL):
                        if 'instance' in s:
                            try:
                                d = json.loads(s)
                                attempted_pids_found = {p['pid'] for p in d.get('data',{}).get('problems',{}).get('result',[])}
                            except: pass
                    if pid in ac_pids_found:
                        result[sid]['luogu'][pid] = 'ac'
                        print(f"  洛谷 {pid}: AC")
                    elif pid in attempted_pids_found:
                        result[sid]['luogu'][pid] = 'attempted'
                        print(f"  洛谷 {pid}: 尝试")
                except Exception as e:
                    print(f"  洛谷 {pid} 错误: {e}")
                time.sleep(0.5)

        if student.get('codeforces_handle') and cf_pids:
            pending_cf = {p for p in cf_pids if result[sid]['codeforces'].get(p) != 'ac'}
            if not pending_cf:
                print(f"  CF: 所有题目已AC，跳过")
            else:
                handle = student['codeforces_handle']
                try:
                    r = requests.get(
                        f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=10000",
                        timeout=15)
                    for sub in r.json().get('result', []):
                        prob = sub.get('problem', {})
                        pid_str = str(prob.get('contestId', '')) + prob.get('index', '')
                        if pid_str in pending_cf:
                            if sub.get('verdict') == 'OK':
                                result[sid]['codeforces'][pid_str] = 'ac'
                            elif pid_str not in result[sid]['codeforces']:
                                result[sid]['codeforces'][pid_str] = 'attempted'
                    print(f"  CF {handle}: 完成")
                except Exception as e:
                    print(f"  CF {handle} 错误: {e}")

        if student.get('atcoder_handle') and ac_pids:
            pending_ac = {p for p in ac_pids if result[sid]['atcoder'].get(p) != 'ac'}
            if not pending_ac:
                print(f"  AtCoder: 所有题目已AC，跳过")
            else:
                user = student['atcoder_handle']
                try:
                    r = requests.get(
                        f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={user}",
                        timeout=15)
                    if r.status_code != 200:
                        print(f"  AtCoder {user}: API 不可用 (HTTP {r.status_code})")
                    else:
                        for sub in r.json():
                            pid_str = sub.get('problem_id', '')
                            if pid_str in pending_ac:
                                if sub.get('result') == 'AC':
                                    result[sid]['atcoder'][pid_str] = 'ac'
                                elif pid_str not in result[sid]['atcoder']:
                                    result[sid]['atcoder'][pid_str] = 'attempted'
                        print(f"  AtCoder {user}: 完成")
                except Exception as e:
                    print(f"  AtCoder {user}: API 错误 ({e})")

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": result
    }
    save_json(SUBS_FILE, output)
    print(f"\n✅ submissions.json 已更新（{len(students)} 名学生）")


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

其他：
  init                  初始化示例数据
  help                  显示此帮助信息
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        return

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
    elif command == "init":
        init_examples()
    elif command == "help":
        show_help()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()