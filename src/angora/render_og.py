"""Render Angora's 1200 x 630 Open Graph card in English and Chinese from src/angora/og.html.

  python3 src/angora/render_og.py          # both languages
  python3 src/angora/render_og.py zh       # only Chinese
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent.parent
HOST = 'site.local'
HTML_LANG = {'en': 'en', 'zh': 'zh-Hans'}


def card(lang):
    text = json.loads((HERE / 'i18n' / f'{lang}.json').read_text())
    return {
        'lang': HTML_LANG[lang],
        'tagline': text['tagline'],
        'h1': text['h1'],
        'free': text['og_free'],
        'fileReason': text['verified_reason'],
        'badgeKeep': text['badge_keep'],
        'badgeRemove': text['badge_remove'],
        'sumLabel': text['stat_reclaimable'],
    }


def main(langs):
    from playwright.sync_api import sync_playwright

    def serve(route, _request):
        rel = route.request.url.split(HOST, 1)[1].split('?')[0].lstrip('/')
        target = (SITE / rel).resolve()
        if target.is_relative_to(SITE) and target.is_file():
            return route.fulfill(path=str(target))
        route.fulfill(status=404, body='')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in langs:
            page = browser.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
            page.route(f'http://{HOST}/**', serve)
            page.add_init_script(f'window.OG = {json.dumps(card(lang), ensure_ascii=False)};')
            page.goto(f'http://{HOST}/src/angora/og.html')
            page.wait_for_selector('body[data-ready="1"]', timeout=15000)
            target = SITE / 'assets/img/angora' / ('' if lang == 'en' else lang) / 'og.png'
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target))
            page.close()
            print(target.relative_to(SITE), target.stat().st_size // 1024, 'KB')
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:] or ['en', 'zh'])
