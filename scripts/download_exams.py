"""Download a reproducible, selective upstream snapshot into an ignored cache."""
import concurrent.futures
import base64
import json
import hashlib
import re
import time
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'aa1326aad53a790a58b670f0b1f3fc26802cee01'
CACHE = ROOT / '.cache/exams'


def get(url):
    for attempt in range(2):
        try:
            return urllib.request.urlopen(url, timeout=12).read()
        except Exception:
            if attempt == 1: raise
            time.sleep(.5)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    tree_path = CACHE / 'tree.json'
    if not tree_path.exists():
        tree_path.write_bytes(get(f'https://api.github.com/repos/sirwym/olympiad-practice-system/git/trees/{REVISION}?recursive=1'))
    tree = json.loads(tree_path.read_bytes())['tree']
    paths = {x['path'] for x in tree if x['type'] == 'blob'}
    blobs = {x['path']: x['sha'] for x in tree if x['type'] == 'blob'}
    selected = [p for p in paths if re.fullmatch(r'papers/[^/]+/index.json', p)] + ['README.md']
    snapshot = CACHE / REVISION
    def download(path):
        target = snapshot / path
        if target.exists(): return path
        last = None
        if any(ord(c) > 127 for c in path):
            try:
                obj = json.loads(get(f'https://api.github.com/repos/sirwym/olympiad-practice-system/git/blobs/{blobs[path]}'))
                data = base64.b64decode(obj['content'])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                return path
            except Exception as error:
                last = error
        origins = [f'https://raw.githubusercontent.com/sirwym/olympiad-practice-system/{REVISION}/', f'https://cdn.jsdelivr.net/gh/sirwym/olympiad-practice-system@{REVISION}/']
        for attempt in range(4):
            origin = origins[attempt % len(origins)]
            try:
                data = get(origin + quote(path, safe='/'))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                return path
            except Exception as error:
                last = error
                time.sleep(.3)
        try:
            obj = json.loads(get(f'https://api.github.com/repos/sirwym/olympiad-practice-system/git/blobs/{blobs[path]}'))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(obj['content']))
            return path
        except Exception as error:
            raise RuntimeError(f'{path}: {last}; blob fallback: {error}')
    def batch(items, worker=download):
        errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(worker, path): path for path in sorted(items)}
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                try: future.result()
                except Exception as error: errors.append(str(error))
                if i % 20 == 0 or i == len(items): print(f'downloaded {i}/{len(items)}', flush=True)
        if errors: raise RuntimeError(f'{len(errors)} resources failed; rerun to resume cache. '+errors[0])
    batch(selected)
    resources = {p for p in paths if p.startswith(('assets/css/','assets/fonts/')) or (p.startswith('assets/js/') and 'katex' in p)}
    for path in selected:
        if not path.endswith('.json'): continue
        text = (snapshot / path).read_text(encoding='utf-8')
        # Download every image in the paper directory, and referenced shared images.
        resources.update(p for p in paths if p.startswith(path.rsplit('/',1)[0]+'/') and p != path)
        for match in re.findall(r'(?:\.\./)?assets/[^\s"<>\\)]+', text):
            resource = match.removeprefix('../')
            if resource in paths: resources.add(resource)
    batch(resources)
    external = {}
    for path in selected:
        if not path.endswith('.json'): continue
        for url in re.findall(r'!\[[^\]]*\]\((https?://[^\s)"\\]+)', (snapshot / path).read_text(encoding='utf-8')):
            extension = Path(url.split('?')[0]).suffix.lower()
            if extension not in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'): extension = '.png'
            external[url] = 'external/' + hashlib.sha256(url.encode()).hexdigest()[:24] + extension
    def download_external(url):
        target = snapshot / external[url]
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(get(url))
    batch(external, download_external)
    (snapshot / 'external-assets.json').write_text(json.dumps(external, ensure_ascii=False, indent=2), encoding='utf-8')
    selected += ['external-assets.json'] + list(external.values())
    output = CACHE / 'upstream.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(set(selected) | resources):
            z.write(snapshot / path, f'upstream-{REVISION}/{path}')
    print('snapshot', output, 'files', len(set(selected) | resources), flush=True)


if __name__ == '__main__':
    main()
