"""End-to-end verification against the local static server; uses installed Edge."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.cache/exams'
ORIGIN = 'http://127.0.0.1:8765'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, timeout=30000)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='light')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(ORIGIN + '/index.html')
        page.wait_for_function("document.querySelectorAll('.recent-row').length > 0")
        page.locator('#global-search-input').fill('GESP')
        page.wait_for_selector('.search-result')
        assert page.locator('.search-result-type').all_text_contents().count('试卷') > 0
        page.keyboard.press('Escape')
        page.screenshot(path=str(OUT / 'home-desktop.png'), full_page=True)
        page.goto(ORIGIN + '/exams.html?category=CSP-J')
        page.wait_for_selector('.paper-row')
        assert page.locator('.paper-row').count() == 7
        page.locator('#exam-year').select_option('2025')
        assert page.locator('.paper-row').count() == 1
        assert 'year=2025' in page.url
        page.locator('#clear-filters').click()
        assert page.locator('.paper-row').count() == 20
        page.locator('#next-page').click()
        assert 'page=2' in page.url
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(OUT / 'exams-desktop.png'), full_page=True)
        paper = json.loads((ROOT / 'exams/papers/2023-03-gesp-1.json').read_text(encoding='utf-8'))
        first = paper['questions'][0]
        practice = ORIGIN + '/exams/practice.html?paper=' + paper['id']
        page.goto(practice)
        page.wait_for_selector('.question')
        page.locator(f'input[data-answer="{first["uid"]}"][value="{first["answer"]}"]').check()
        page.reload()
        page.wait_for_selector('.question')
        assert page.locator(f'input[data-answer="{first["uid"]}"][value="{first["answer"]}"]').is_checked()
        page.locator('#submit-paper').click()
        page.get_by_role('button', name='返回检查', exact=True).click()
        assert not page.locator('#result-summary').is_visible()
        # A second tab may have raised the best score while this page was open.
        page.evaluate("""max => {const k=Object.keys(localStorage).find(k=>k.startsWith('showball-exam:v1:2023-03-gesp-1:')&&!k.endsWith(':best'));localStorage.setItem(k+':best',JSON.stringify(max));}""",paper['objective_score'])
        page.locator('#submit-paper').click()
        page.get_by_role('button', name='确认交卷', exact=True).click()
        assert page.locator('#result-summary').is_visible()
        assert page.locator('#q1').get_attribute('class') == 'question correct'
        assert page.locator('#submit-paper').is_disabled()
        assert str(paper['objective_score']).removesuffix('.0') in page.locator('#best-score').inner_text()
        page.locator('#reset-paper').click()
        page.keyboard.press('Escape')
        assert page.locator('#result-summary').is_visible(), 'Esc must cancel resetting a completed paper'
        assert page.locator('#submit-paper').is_disabled()
        page.locator('#wrong-only').check()
        assert not page.locator('#q1').is_visible()
        page.reload();page.wait_for_selector('.question')
        assert page.locator('#result-summary').is_visible()
        page.screenshot(path=str(OUT / 'practice-desktop.png'), full_page=True)
        page.locator('#reset-paper').click();page.get_by_role('button',name='清除并重新练习').click()
        page.locator('#start-timed').click();page.get_by_role('button',name='开始计时',exact=True).click()
        page.reload();page.wait_for_selector('.question')
        assert '剩余' in page.locator('#timer-label').inner_text()
        second=context.new_page();second.goto(practice);second.wait_for_selector('.question')
        assert '剩余' in second.locator('#timer-label').inner_text()
        # Simulate a stored expired deadline, as when a student returns after time runs out.
        page.evaluate("""() => { const k=Object.keys(localStorage).find(k=>k.startsWith('showball-exam:v1:2023-03-gesp-1:')&&!k.endsWith(':best')); const s=JSON.parse(localStorage.getItem(k));s.deadline=Date.now()-1000;localStorage.setItem(k,JSON.stringify(s)); }""")
        page.reload();page.wait_for_selector('#result-summary',state='visible')
        assert page.locator('#submit-paper').is_disabled()
        second.wait_for_selector('#result-summary',state='visible')
        assert second.locator('#submit-paper').is_disabled()
        for kind in ['multi_choice','judge','fill']:
            candidate = next((data for path in (ROOT/'exams/papers').glob('*.json') if (data:=json.loads(path.read_text(encoding='utf-8'))) and any(q['type']==kind and q['gradable'] for q in data['questions'])),None)
            q=next(q for q in candidate['questions'] if q['type']==kind and q['gradable'])
            testpage=browser.new_context().new_page();testpage.goto(ORIGIN+'/exams/practice.html?paper='+candidate['id']);testpage.wait_for_selector('.question')
            if kind=='fill': testpage.locator(f'textarea[data-answer="{q["uid"]}"]').fill(q['answer'])
            else:
                for value in list(q['answer']) if kind=='multi_choice' else [q['answer']]:testpage.locator(f'input[data-answer="{q["uid"]}"][value="{value}"]').check()
            testpage.locator('#submit-paper').click();testpage.get_by_role('button',name='确认交卷',exact=True).click()
            assert testpage.locator('#'+q['uid']).get_attribute('class')=='question correct',kind
        for path in ['/memos.html','/memos/detail.html?type=course&id=syntax-basics','/favorite.html','/templates.html','/tools.html']:
            page.goto(ORIGIN + path)
            page.wait_for_timeout(400)
            assert page.locator('.topbar').count() == 1
            assert page.locator('.nav-card').count() == 5
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.goto(ORIGIN + '/index.html');page.get_by_role('button',name='切换到深色模式').click()
        assert page.locator('html').get_attribute('data-theme') == 'dark'
        page.screenshot(path=str(OUT / 'home-dark.png'), full_page=True)
        mobile = browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,color_scheme='light')
        phone = mobile.new_page()
        for path,name in [('/index.html','home'),('/exams.html','exams'),('/memos.html','courses'),('/exams/practice.html?paper=2023-03-gesp-1','practice')]:
            phone.goto(ORIGIN+path);phone.wait_for_timeout(500)
            assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth'), path
            phone.screenshot(path=str(OUT / f'{name}-mobile.png'),full_page=True)
        phone.get_by_role('button',name='导航',exact=True).click()
        assert phone.locator('.nav-cards').is_visible()
        phone.keyboard.press('Escape')
        assert not phone.locator('.nav-cards').is_visible()
        blocked=browser.new_context()
        blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
        denied=blocked.new_page();denied.goto(practice);denied.wait_for_selector('.question')
        denied.locator(f'input[data-answer="{first["uid"]}"][value="{first["answer"]}"]').check()
        assert denied.locator('#storage-warning').is_visible()
        assert not errors, errors
        browser.close()
        print('Browser OK: search, filters, pagination, answer/save/reload, dialogs, grading, reset, timer expiry, themes, mobile, storage failure, legacy routes')


if __name__ == '__main__':
    main()
