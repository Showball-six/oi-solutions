"""Regression checks for direct handbook reading and the shared site shell."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'http://127.0.0.1:8765'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, timeout=30000)
        context = browser.new_context(viewport={'width':1440,'height':1000},color_scheme='light')
        page = context.new_page()
        errors=[]
        page.on('pageerror', lambda error:errors.append(str(error)))
        page.goto(ORIGIN+'/memos.html')
        page.locator('#handbook-grid a').first.click()
        assert page.locator('.prose').count()==1, '手册入口应直接显示正文'
        assert '计算机基础知识' in page.locator('.prose h1').inner_text()
        assert page.locator('.nav-card').count()==5, '手册应使用主站导航'
        assert page.locator('.sidebar').count()==0, '不能再出现独立专栏侧栏'
        assert page.locator('.back-to-site').count()==0, '统一导航不应再插入返回主站的重复入口'
        page.locator('.book-chapters summary').click()
        page.locator('.book-chapters a').nth(1).click()
        assert '第2章' in page.locator('.prose h1').inner_text()
        page.get_by_role('button',name='切换到深色模式').click()
        assert page.locator('html').get_attribute('data-theme')=='dark'
        page.screenshot(path=str(ROOT/'.cache/exams/handbook-desktop.png'))
        page.goto(ORIGIN+'/handbook/search/index.html?q=二分')
        page.wait_for_selector('#search-results .search-result')
        page.locator('#search-results .search-result').first.click()
        assert page.locator('.prose').count()==1
        for route in ['/','/exams.html','/exams/practice.html?paper=2023-03-gesp-1']:
            page.goto(ORIGIN+route)
            assert page.locator('a[href*="SOURCES.md"]').count()==0
            assert page.get_by_text('来源与迁移说明',exact=True).count()==0
        phone=browser.new_page(viewport={'width':390,'height':844})
        phone.goto(ORIGIN+'/handbook/courses/1/index.html')
        assert phone.locator('.prose').count()==1
        assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth')
        phone.get_by_role('button',name='导航',exact=True).click()
        assert phone.locator('.nav-cards').is_visible()
        phone.screenshot(path=str(ROOT/'.cache/exams/handbook-mobile.png'))
        assert not errors, errors
        browser.close()
        print('Handbook OK: direct content, chapter navigation, shared theme, search, mobile, no maintenance links')


if __name__=='__main__': main()
