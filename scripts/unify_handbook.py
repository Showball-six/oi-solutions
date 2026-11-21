"""Use the main site shell and open handbooks directly at their first chapter.

Run after updating the static handbook export. Chapter contents and URLs stay intact.
"""
import html
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'handbook'


def relative(target, page):
    return posixpath.relpath(target, str(page.parent.relative_to(ROOT)).replace('\\', '/'))


def shell(page):
    home = relative('index.html', page)
    nav = [('courses','memos.html','课程讲义'),('exams','exams.html','笔试练习'),('favorites','favorite.html','题目题解'),('templates','templates.html','代码模板'),('tools','tools.html','工具')]
    return '<a class="skip-link" href="#main-content">跳到正文</a><header class="topbar"><div class="topbar-inner"><a class="logo" href="'+home+'"><span class="logo-icon">S</span><span>Showball <small>OI</small></span></a><nav class="nav-cards" id="site-nav" aria-label="主导航">'+''.join(f'<a class="nav-card" data-page="{key}" href="{relative(url,page)}">{name}</a>' for key,url,name in nav)+'</nav><div class="topbar-actions"><time class="topbar-time" id="clock"></time><button class="theme-button" data-theme-toggle aria-label="切换主题">主题</button><button class="menu-button" data-menu-toggle aria-controls="site-nav" aria-expanded="false">导航</button></div></div></header>'


def rebase(content, old, new):
    def replace(match):
        attr, quote, value = match.groups()
        parsed = urlsplit(html.unescape(value))
        if not value or value.startswith('#') or parsed.scheme or parsed.netloc:
            return match.group(0)
        resolved = urlsplit(urljoin('/'+old.relative_to(ROOT).as_posix(), html.unescape(value)))
        path = posixpath.relpath(resolved.path.lstrip('/'), new.parent.relative_to(ROOT).as_posix())
        return attr+'='+quote+html.escape(urlunsplit(('', '', path, resolved.query, resolved.fragment)),quote=True)+quote
    return re.sub(r'<[a-zA-Z][^>]*>',lambda tag: re.sub(r'\b(href|src)=([\"\'])(.*?)\2',replace,tag.group(0),flags=re.S),content,flags=re.S)


def read_books(base):
    manifest = base / 'assets/books.json'
    previous = {b['id']:b for b in json.loads(manifest.read_text(encoding='utf-8'))} if manifest.exists() else {}
    books=[]
    for course in sorted((base/'courses').glob('*/index.html'),key=lambda p:int(p.parent.name)):
        source=course.read_text(encoding='utf-8')
        chapters=[]
        for href,title in re.findall(r'<a href="([^"]+)"><span class="chapter-number">.*?</span><h2>(.*?)</h2>',source,re.S):
            path=urlsplit(urljoin('/'+course.relative_to(base.parent).as_posix(),html.unescape(href))).path.lstrip('/')
            chapters.append({'path':unquote(path),'title':html.unescape(re.sub('<[^>]*>','',title))})
        if chapters:
            title=html.unescape(re.search(r'<h1>(.*?)</h1>',source).group(1))
            books.append({'id':int(course.parent.name),'title':title,'chapters':chapters})
        elif int(course.parent.name) in previous:
            books.append(previous[int(course.parent.name)])
    return books


def main():
    manifest = BASE / 'assets/books.json'
    books = read_books(BASE)
    for book in books:
        for chapter in book['chapters']: chapter['path']=unquote(chapter['path'])
    manifest.write_text(json.dumps(books,ensure_ascii=False,indent=2),encoding='utf-8')
    by_path={chapter['path']:book for book in books for chapter in reversed(book['chapters'])}
    # CSP-S and NOIP share a source; use the first canonical handbook in reading links.
    for book in reversed(books):
        for chapter in book['chapters']: by_path[chapter['path']]=book
    source_main={}
    for page in BASE.rglob('*.html'):
        source=page.read_text(encoding='utf-8')
        found=re.search(r'<main\b[^>]*>[\s\S]*?</main>',source)
        if found:
            main_html=re.sub(r'<details class="book-chapters">[\s\S]*?</details>','',found.group(0))
            source_main[page]=main_html
    for page, main_html in source_main.items():
        if page in (BASE/'index.html',BASE/'courses/index.html'):
            destination=relative('memos.html',page)+'#handbook-grid'
            page.write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={destination}"><title>课程讲义 · Showball OI</title></head><body><a href="{destination}">进入课程讲义</a></body></html>',encoding='utf-8')
            continue
        source=page.read_text(encoding='utf-8')
        original_attrs=re.search(r'<body([^>]*)>',source).group(1)
        root_attr=re.search(r'data-root="([^"]+)"',original_attrs)
        book=by_path.get(page.relative_to(ROOT).as_posix())
        if page.parent.parent == BASE/'courses' and page.parent.name.isdigit():
            book=next((b for b in books if b['id']==int(page.parent.name)),None)
            if book:
                first=ROOT/Path(book['chapters'][0]['path'])
                # On Windows source URLs are encoded, filesystem names are not.
                main_html=rebase(source_main[first],first,page)
        main_html=re.sub(r'(<main\b[^>]*\bid=)[\"\'][^\"\']+[\"\']',r'\1"main-content"',main_html,count=1)
        main_html=main_html.replace('href="#main"','href="#main-content"')
        if book:
            links=''.join(f'<a href="{html.escape(relative(ch["path"],page))}">{html.escape(ch["title"])}</a>' for ch in book['chapters'])
            chapter_nav='<details class="book-chapters"><summary>章节目录</summary><nav aria-label="章节目录">'+links+'</nav></details>'
            main_html=re.sub(r'(<main\b[^>]*>)',r'\1'+chapter_nav,main_html,count=1)
        title=re.search(r'<title>(.*?)</title>',source).group(1)
        if book and page.parent.parent == BASE/'courses': title=book['chapters'][0]['title']+' · Showball OI'
        title=re.sub(r' · 信息学知识手册$', ' · Showball OI',title)
        head='<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>'+title+'</title>'
        # Retain exported article styles (formula/fonts/highlighting), then apply site tokens.
        for asset in ['handbook/assets/source/971002830b8a88c44f98.css','handbook/assets/theme.css','assets/theme.css','assets/hub.css','handbook/assets/reader.css']:
            head+=f'<link rel="stylesheet" href="{relative(asset,page)}">'
        for asset in ['assets/app.js','handbook/assets/app.js']:
            head+=f'<script defer src="{relative(asset,page)}"></script>'
        head+="<script>try{document.documentElement.dataset.theme=localStorage.getItem('showball-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light')}catch{}</script>"
        attrs=' class="handbook-hub" data-page="courses"'+(f' data-root="{root_attr.group(1)}"' if root_attr else '')
        page.write_text('<!doctype html><html lang="zh-CN"><head>'+head+'</head><body'+attrs+'>'+shell(page)+main_html+'<footer class="site-footer">© 2026 Showball OI · 学习与训练</footer><div class="toast" role="status" aria-live="polite"></div></body></html>',encoding='utf-8')
    print(f'Unified {len(source_main)} handbook pages; {len(books)} direct-reading entries')


if __name__=='__main__': main()
