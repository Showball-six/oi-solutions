#!/usr/bin/env python3
"""测试洛谷用户主页 API（公开，无需登录）"""

import requests
import json
import re

uid = "1020186"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

print(f"测试用户主页 API（公开）")
print(f"URL: https://www.luogu.com.cn/user/{uid}\n")

try:
    r = requests.get(f"https://www.luogu.com.cn/user/{uid}", headers=headers, timeout=10)
    print(f"HTTP 状态码: {r.status_code}\n")

    if r.status_code == 200:
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)

        for i, s in enumerate(scripts):
            if s.strip().startswith('{'):
                try:
                    d = json.loads(s)

                    if 'currentData' in d:
                        print(f"✓✓✓ 找到 currentData!")
                        current = d['currentData']

                        if 'passedProblems' in current:
                            passed = current['passedProblems']
                            print(f"\n✓ passedProblems (AC的题目): {len(passed)} 道")
                            print(f"示例: {passed[:10]}")

                        if 'submittedProblems' in current:
                            submitted = current['submittedProblems']
                            print(f"\n✓ submittedProblems (提交过的题目): {len(submitted)} 道")
                            print(f"示例: {submitted[:10]}")

                        # 检查是否有 B2017, P3808, P3804
                        test_pids = ['B2017', 'P3808', 'P3804']
                        print(f"\n检查练习题状态:")
                        for pid in test_pids:
                            if pid in passed:
                                print(f"  {pid}: ✓ AC")
                            elif pid in submitted:
                                print(f"  {pid}: ? 尝试")
                            else:
                                print(f"  {pid}: – 未做")

                        break
                except json.JSONDecodeError:
                    pass

except Exception as e:
    print(f"错误: {e}")





