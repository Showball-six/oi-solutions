"""Import a pinned upstream archive. No network is needed to rebuild.

python scripts/import_exams.py --archive .cache/exams/upstream.zip
Dependencies: python -m pip install --no-user --target .cache/exams/python -r scripts/requirements-exams.txt
"""
import argparse
import collections
import copy
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.cache/exams/python'))
from markdown_it import MarkdownIt

MD = MarkdownIt('commonmark', {'html': False, 'breaks': True}).enable('table')
REPO = 'https://github.com/sirwym/olympiad-practice-system'


def math_inline(state, silent):
    """Protect TeX from Markdown emphasis/escape handling; KaTeX renders later."""
    start = state.pos
    opening = next((left for left in ('$$', '$', r'\(', r'\[') if state.src.startswith(left, start)), None)
    if opening is None:
        return False
    closing = {r'\(': r'\)', r'\[': r'\]'}.get(opening, opening)
    end = state.src.find(closing, start + len(opening))
    while end != -1 and state.src[end - 1] == '\\':
        end = state.src.find(closing, end + len(closing))
    if end == -1:
        return False
    if not silent:
        token = state.push('math_literal', '', 0)
        token.content = state.src[start:end + len(closing)]
    state.pos = end + len(closing)
    return True


MD.inline.ruler.before('escape', 'math_literal', math_inline)
MD.add_render_rule('math_literal', lambda renderer, tokens, idx, options, env: html.escape(tokens[idx].content))


def render(text):
    return MD.render(str(text or ''))


def normalize_paper(raw, slug, revision):
    paper = copy.deepcopy(raw)
    paper.update(id=slug, revision=revision, source_url=f'{REPO}/tree/{revision}/papers/{slug}')
    paper['version'] = hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    paper['questions'] = []
    paper['warnings'] = []
    for index, original in enumerate(raw.get('questions', []), 1):
        q = copy.deepcopy(original)
        q['uid'] = f'q{index}'
        answer = q.get('answer', '')
        if isinstance(answer, bool):
            answer = 'True' if answer else 'False'
        elif isinstance(answer, list):
            answer = ''.join(map(str, answer))
        answer = str(answer if answer is not None else '').strip()
        if answer.lower() in ('none', 'null', ''):
            answer = ''
        q['answer'] = answer
        q['score'] = float(q.get('score') or 0)
        kind = q.get('type')
        options = q.get('options') or []
        keys = [str(o.get('key', '')) for o in options]
        valid = bool(answer) and kind in ('choice', 'multi_choice', 'judge', 'fill')
        if kind == 'choice':
            valid = valid and answer in keys
        elif kind == 'multi_choice':
            answer = ''.join(sorted(set(answer.upper())))
            q['answer'] = answer
            valid = valid and bool(keys) and all(k in keys for k in answer)
        elif kind == 'judge':
            lookup = {'true': 'True', 'false': 'False', '正确': 'True', '错误': 'False', '√': 'True', '×': 'False'}
            q['answer'] = lookup.get(answer.lower(), answer)
            valid = valid and q['answer'] in ('True', 'False')
        q['gradable'] = bool(valid)
        q['html'] = render(q.get('content', ''))
        if q.get('code'):
            q['html'] += '<pre><code>' + html.escape(str(q['code'])) + '</code></pre>'
        if q.get('explanation') or q.get('analysis'):
            q['explanation_html'] = render(q.get('explanation') or q.get('analysis'))
        q['options'] = [dict(o, html=render(o.get('text', ''))) for o in options]
        if not valid and kind != 'program':
            paper['warnings'].append(f"{q['uid']}: 答案缺失或格式不适用，暂不自动评分")
        paper['questions'].append(q)
    paper['objective_score'] = sum(q['score'] for q in paper['questions'] if q['gradable'])
    computed = sum(q['score'] for q in paper['questions'])
    if paper.get('total_score') is not None and abs(float(paper['total_score']) - computed) > .01:
        paper['warnings'].append(f"原卷标注满分 {paper['total_score']}，题目分值合计 {computed:g}，保留原数据")
    return paper


def import_archive(archive, output):
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        root = z.namelist()[0].split('/')[0]
        revision = root.rsplit('-', 1)[-1]
        if revision == 'main':
            raise ValueError('请使用 GitHub API zipball 下载带 commit 标识的压缩包，而非 main 分支命名的归档')
        files = {name[len(root)+1:]: name for name in z.namelist() if not name.endswith('/')}
        external = json.loads(z.read(files['external-assets.json'])) if 'external-assets.json' in files else {}
        catalog, report = [], []
        resources = set()
        for path in sorted(files):
            if not re.fullmatch(r'papers/[^/]+/index.json', path):
                continue
            slug = path.split('/')[1]
            raw = json.loads(z.read(files[path]))
            resource_warnings = []
            # Resolve all local image references before moving JSON one directory up.
            def image_rule(tokens, idx, options, env):
                token = tokens[idx]
                src = token.attrGet('src') or ''
                parsed = urlsplit(src)
                if parsed.scheme or parsed.netloc:
                    if src in external and external[src] in files:
                        resources.add(external[src])
                        token.attrSet('src', external[src])
                        token.attrSet('loading', 'lazy')
                        return MD.renderer.renderToken(tokens, idx, options, env)
                    resource_warnings.append(f'外部图片需核对：{src}')
                    return '<span class="resource-missing">[外部图片未迁入：' + html.escape(src) + ']</span>'
                clean = unquote(parsed.path)
                if clean.startswith('../assets/'):
                    candidate = clean[3:]
                elif clean.startswith('assets/'):
                    candidate = clean
                else:
                    candidate = str(PurePosixPath('papers') / slug / clean)
                # Normalize relative segments and refuse traversal.
                parts = []
                for part in candidate.split('/'):
                    if part == '..':
                        if parts: parts.pop()
                        else: return '[无效图片路径]'
                    elif part not in ('', '.'):
                        parts.append(part)
                candidate = '/'.join(parts)
                if candidate not in files:
                    resource_warnings.append(f'图片缺失：{src}')
                    return '<span class="resource-missing">[原始图片缺失]</span>'
                resources.add(candidate)
                token.attrSet('src', candidate)  # relative to /exams/practice.html
                token.attrSet('loading', 'lazy')
                return MD.renderer.renderToken(tokens, idx, options, env)
            MD.add_render_rule('image', lambda renderer, tokens, idx, options, env: image_rule(tokens, idx, options, env))
            paper = normalize_paper(raw, slug, revision)
            paper['warnings'].extend(resource_warnings)
            target = output / 'papers' / f'{slug}.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding='utf-8')
            catalog.append({k: paper.get(k, '') for k in ('id', 'title', 'category', 'level', 'date', 'time_limit', 'total_score', 'objective_score', 'version')}
                           | {'count': len(paper['questions']), 'href': f'exams/practice.html?paper={slug}', 'path': f'papers/{slug}.json', 'warnings': len(paper['warnings'])})
            if paper['warnings']:
                report.append({'id': slug, 'warnings': paper['warnings']})
        for path in files:
            if path.startswith(('assets/css/', 'assets/fonts/')) or (path.startswith('assets/js/') and 'katex' in path):
                resources.add(path)
        for path in sorted(resources):
            dest = output / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(files[path]))
        catalog.sort(key=lambda p: (str(p.get('date') or ''), str(p['id'])), reverse=True)
        (output / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
        manifest = {'repository': REPO, 'revision': revision, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'imported': '2026-11-21', 'papers': len(catalog), 'categories': dict(collections.Counter(p['category'] for p in catalog)), 'review': report}
        (output / 'import-report.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        (output / 'UPSTREAM-README.md').write_bytes(z.read(files['README.md']))
        (output / 'external-assets.json').write_text(json.dumps(external, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k: v for k, v in manifest.items() if k != 'review'}, ensure_ascii=False))
        print('需核对试卷:', len(report), '资源:', len(resources))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'exams')
    args = parser.parse_args()
    import_archive(args.archive, args.output)
