"""Modern lecture behavior and real Typora exports; needs localhost:8765."""
import importlib.util
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='http://127.0.0.1:8765'


def main():
    spec=importlib.util.spec_from_file_location('lecture_cli',ROOT/'script.py')
    cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
    folder=ROOT/'.cache/lectures';folder.mkdir(parents=True,exist_ok=True)
    source='''<!doctype html><html><head><meta charset="utf-8"><title>二分与边界</title></head><body><div id="write"><h1>二分与边界</h1><h2 id="concept"><strong>基本概念</strong>与 <code>lower_bound</code></h2><blockquote><p><strong>注意：</strong>检查边界。</p></blockquote><blockquote><p>这是普通引用，不应被强制标记为定义。</p></blockquote><h3><em>循环</em>不变量</h3><h4>例题：查找位置</h4><pre lang="cpp"><code>// @open 示例\nif (left &lt; right) return left;\n</code></pre><h2>实现</h2><pre lang="cpp"><code>// @fold 长代码\n'''+('\n'.join('int value_'+str(i)+' = '+str(i)+';' for i in range(30)))+'''</code></pre><table><thead><tr><th>条件</th><th>含义</th></tr></thead><tbody><tr><td>left&lt;right</td><td>区间非空</td></tr></tbody></table></div></body></html>'''
    (folder/'fixture.html').write_text(cli.render_polished_html(source,'/memos/lecture-theme.css','/memos/lecture-enhance.js'),encoding='utf-8')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True,timeout=30000)
        context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='light',permissions=['clipboard-read','clipboard-write'])
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(ORIGIN+'/.cache/lectures/fixture.html')
        assert page.locator('.lec-toolbar').count()==0
        assert page.locator('.lec-outline nav a').count()==3
        assert page.locator('.lec-outline nav a').first.locator('strong').inner_text()=='基本概念'
        assert page.locator('.lec-outline nav a').first.locator('code').inner_text()=='lower_bound'
        assert page.locator('.lec-outline nav a').nth(1).locator('em').inner_text()=='循环'
        page.locator('#concept code').evaluate('(el)=>el.textContent="upper_bound"')
        page.wait_for_function("document.querySelector('.lec-outline code').textContent==='upper_bound'")
        assert page.locator('#write h2').first.get_attribute('id')=='concept'
        assert page.locator('blockquote').first.get_attribute('data-lec-label')=='注意'
        assert page.locator('blockquote').first.inner_text().strip()=='检查边界。'
        assert not page.locator('blockquote').nth(1).get_attribute('data-lec-label')
        assert page.locator('.lec-code-wrap').count()==2
        assert page.locator('.lec-code-wrap').first.locator('button[aria-expanded]').get_attribute('aria-expanded')=='true'
        second=page.locator('.lec-code-wrap').nth(1)
        assert second.locator('button[aria-expanded]').get_attribute('aria-expanded')=='false'
        second.get_by_role('button',name='展开',exact=True).focus();page.keyboard.press('Enter')
        assert second.locator('button[aria-expanded]').get_attribute('aria-expanded')=='true'
        page.locator('.lec-code-wrap').first.get_by_role('button',name='复制',exact=True).click()
        assert 'if (left < right) return left;' in page.evaluate('navigator.clipboard.readText()')
        assert '@open' not in page.evaluate('navigator.clipboard.readText()')
        page.add_script_tag(url='/memos/lecture-enhance.js')
        assert page.locator('.lec-toolbar').count()==0 and page.locator('.lec-code-wrap').count()==2
        assert page.locator('.lec-outline button').count()==0
        page.evaluate("document.documentElement.dataset.theme='dark'")
        assert page.locator('html').get_attribute('data-theme')=='dark'
        page.screenshot(path=str(folder/'fixture-dark.png'),full_page=True)
        page.emulate_media(media='print')
        assert not page.locator('.lec-toolbar').is_visible()
        assert page.locator('.lec-code-inner').nth(1).evaluate('(el)=>getComputedStyle(el).maxHeight')=='none'
        page.emulate_media(media='screen')
        for filename in ['lec-001.html','Lec-array-basics.html','Lec-prime-sieve.html']:
            page.goto(ORIGIN+'/memos/'+filename);page.wait_for_selector('.lec-outline')
            assert page.locator('.lec-outline nav a').count()>0
            if filename=='Lec-prime-sieve.html':
                assert page.locator('.lec-outline mjx-container svg').count()>0, '目录不能丢失标题里的公式'
                assert '\\sqrt' not in page.locator('.lec-outline').inner_text(), '不能在渲染公式后重复显示 TeX 源码'
                assert page.locator('.lec-outline a a').count()==0
                assert page.evaluate('''()=>{const ids=[...document.querySelectorAll('.lec-outline [id]')].map(e=>e.id);return new Set(ids).size===ids.length&&ids.every(id=>!document.querySelector('#write [id="'+id+'"]'));}''')
            assert page.locator('.lec-code-wrap .lec-code-wrap').count()==0
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),filename
            blocks=page.locator('.lec-code-wrap')
            if blocks.count():
                first=blocks.first
                if first.locator('button[aria-expanded]').get_attribute('aria-expanded')=='false':first.get_by_role('button',name='展开',exact=True).click()
                first.locator('.lec-code-inner').wait_for(state='visible')
            page.screenshot(path=str(folder/(filename+'.png')))
        mobile=browser.new_page(viewport={'width':390,'height':844},color_scheme='light')
        mobile.goto(ORIGIN+'/memos/Lec-array-basics.html')
        assert not mobile.locator('.lec-outline').get_attribute('open')
        mobile.locator('.lec-outline summary').click()
        mobile.locator('.lec-outline a').first.click()
        assert not mobile.locator('.lec-outline').get_attribute('open')
        assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
        mobile.screenshot(path=str(folder/'lecture-mobile.png'))
        denied=browser.new_context();denied.add_init_script("Object.defineProperty(navigator,'clipboard',{get(){throw new Error('blocked')}})")
        failed=denied.new_page();failed.goto(ORIGIN+'/.cache/lectures/fixture.html');failed.locator('.lec-code-wrap').first.get_by_role('button',name='复制',exact=True).click()
        failed.get_by_role('button',name='复制失败',exact=True).wait_for()
        assert not errors,errors
        browser.close()
        print('Lectures OK: outline, themes, code markers/copy/toggle, idempotence, print, actual CodeMirror exports, phone, clipboard failure')


if __name__=='__main__': main()
