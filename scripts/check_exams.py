"""Validate the imported catalog, rendered resources and scoring boundaries."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'exams'


class ResourceCheck(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag not in ('script', 'iframe', 'object'), f'Unsafe tag: {tag}'
        assert not any(k.startswith('on') for k in attrs), 'Event handler in content'
        if tag == 'img':
            src = attrs.get('src', '')
            assert not urlsplit(src).scheme, f'External image: {src}'
            target = (BASE / unquote(src)).resolve()
            assert target.is_relative_to(BASE) and target.is_file(), f'Missing resource: {src}'


def main():
    catalog = json.loads((BASE / 'catalog.json').read_text(encoding='utf-8'))
    assert len({p['id'] for p in catalog}) == len(catalog), 'Duplicate paper id'
    count = 0
    for entry in catalog:
        p = json.loads((BASE / entry['path']).read_text(encoding='utf-8'))
        assert len(p['questions']) == entry['count']
        assert len({q['uid'] for q in p['questions']}) == len(p['questions'])
        assert sum(q['score'] for q in p['questions'] if q['gradable']) == p['objective_score']
        for q in p['questions']:
            if q['type'] == 'program' or not q['answer']: assert not q['gradable']
            for text in [q['html'], q.get('explanation_html', '')] + [o['html'] for o in q['options']]:
                ResourceCheck().feed(text)
            count += 1
    print(f'Validated {len(catalog)} papers, {count} questions; local images and scoring boundaries OK')


if __name__ == '__main__':
    main()
