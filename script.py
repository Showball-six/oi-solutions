#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OI 工具箱 - 数据管理辅助脚本
用途：快速创建/管理JSON数据文件

使用方法：
  python3 script.py --help
  python3 script.py create <pid> <title> <diff>
  python3 script.py init
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

SOLUTIONS_DIR = Path("solutions")
SOLUTIONS_DIR.mkdir(exist_ok=True)


def load_existing_records():
    """加载所有现有的JSON记录"""
    records = []
    if SOLUTIONS_DIR.exists():
        for json_file in SOLUTIONS_DIR.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    records.append(record)
            except Exception as e:
                print(f"⚠️  无法加载 {json_file.name}: {e}")
    return sorted(records, key=lambda x: int(x.get('id', 0)))


def get_next_id(records):
    """获取下一个ID"""
    if not records:
        return "001"
    max_id = max(int(r.get('id', 0)) for r in records)
    return str(max_id + 1).zfill(3)


def create_json_record(pid, title, diff, source="洛谷", tags=None, problem_url=None):
    """创建一条JSON记录"""
    records = load_existing_records()
    next_id = get_next_id(records)
    
    # 根据题号生成文件名
    filename_base = pid.lower().replace(' ', '_')
    html_file = f"solutions/{filename_base}.html"
    json_file = f"solutions/{filename_base}.json"
    
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
    
    return record, json_file


def save_record(record, json_path):
    """保存JSON记录"""
    path = Path(json_path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存：{json_path}")


def create_html_template(html_path, pid, title, source="洛谷"):
    """创建题解HTML模板"""
    path = Path(html_path)
    if path.exists():
        print(f"⚠️  文件已存在：{html_path}（跳过）")
        return
    
    # 生成题目链接
    problem_url = "#"
    if source == "洛谷" and pid.startswith('P'):
        problem_url = f"https://www.luogu.com.cn/problem/{pid}"
    elif source == "CF" and pid.startswith('CF'):
        cf_pid = pid[2:]  # 去掉CF前缀
        # 简单处理，实际可能需要更复杂的解析
        problem_url = f"https://codeforces.com/problemset/problem/1/A"
    elif source == "AtCoder":
        problem_url = "https://atcoder.jp/"
    
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
    
    print("\n可选难度:")
    difficulties = ["入门", "普及-", "普及/提高-", "普及/提高", 
                   "提高/省选-", "省选/NOI-", "NOI"]
    for i, d in enumerate(difficulties, 1):
        print(f"  {i}. {d}")
    
    diff_choice = input("选择难度 (1-7，默认4): ").strip()
    diff = difficulties[int(diff_choice)-1] if diff_choice.isdigit() else "普及/提高"
    
    source = input("来源 (洛谷/CF/AtCoder，默认洛谷): ").strip() or "洛谷"
    
    tags_input = input("标签 (用逗号分隔，可选): ").strip()
    tags = [t.strip() for t in tags_input.split(',')] if tags_input else []
    
    # 创建记录
    record, json_path = create_json_record(pid, title, diff, source, tags)
    html_path = record["href"]
    
    print("\n" + "-"*50)
    print(f"ID: {record['id']}")
    print(f"题号: {pid}")
    print(f"标题: {title}")
    print(f"难度: {diff}")
    print(f"标签: {', '.join(tags) if tags else '(无)'}")
    print("-"*50)
    
    confirm = input("\n确认创建？ (y/n): ").strip().lower()
    if confirm == 'y':
        create_html_template(html_path, pid, title, source)
        save_record(record, json_path)
        print("\n✨ 创建成功！")
    else:
        print("\n❌ 已取消")


def init_examples():
    """初始化示例数据"""
    print("\n初始化示例数据...")
    
    examples = [
        {
            "id": "001",
            "pid": "P3372",
            "title": "线段树 1",
            "source": "洛谷",
            "href": "solutions/lg-p3372.html",
            "diff": "普及/提高",
            "tags": ["线段树", "数据结构"]
        },
        {
            "id": "002",
            "pid": "CF1A",
            "title": "Theatre Square",
            "source": "CF",
            "href": "solutions/cf-1a.html",
            "diff": "入门",
            "tags": ["数学"]
        }
    ]
    
    for example in examples:
        json_path = Path(example["href"]).with_suffix('.json')
        html_path = example["href"]
        
        # 创建HTML
        create_html_template(html_path, example["pid"], example["title"], example["source"])
        
        # 保存JSON
        save_record(example, str(json_path))
    
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


def show_help():
    """显示帮助信息"""
    help_text = """
OI 工具箱 - 数据管理脚本

用法：
  python3 script.py <command>

命令：
  create      交互式创建新题目
  list        列出所有题目
  init        初始化示例数据
  help        显示此帮助信息

示例：
  python3 script.py create
  python3 script.py list
  python3 script.py init
    """
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        interactive_create()
    elif command == "list":
        list_records()
    elif command == "init":
        init_examples()
    elif command == "help":
        show_help()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
