"""Render the 1200 x 630 Open Graph card for every site language from src/og.html.

  python3 src/render_og.py            # every language except English
  python3 src/render_og.py en         # also writes assets/img/og.png (English is kept as first drawn by default)

Text comes from src/i18n/<lang>.json (tagline, h1, og_free); the screen from assets/img/<lang>/cooldown-overview.webp,
so run render_screens.py first. Writes assets/img/<lang>/og.png.
"""
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
HOST = 'site.local'
LANGS = ['en', 'de', 'es', 'fr', 'hi', 'id', 'it', 'ja', 'ko', 'pt', 'zh']
HTML_LANG = {'es': 'es-419', 'pt': 'pt-BR', 'zh': 'zh-Hans'}


def main(langs):
    from playwright.sync_api import sync_playwright

    def serve(route):
        rel = route.request.url.split(HOST, 1)[1].split('?')[0].lstrip('/')
        target = (SITE / rel).resolve()
        if target.is_relative_to(SITE) and target.is_file():
            return route.fulfill(path=str(target))
        route.fulfill(status=404, body='')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in langs:
            text = json.loads((SITE / 'src/i18n' / f'{lang}.json').read_text())
            img = 'assets/img/' if lang == 'en' else f'assets/img/{lang}/'
            og = {'lang': HTML_LANG.get(lang, lang), 'tagline': text['tagline'], 'h1': text['h1'],
                  'free': text['og_free'], 'screen': f'/{img}cooldown-overview.webp'}
            page = browser.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
            page.route(f'http://{HOST}/**', serve)
            page.add_init_script(f'window.OG = {json.dumps(og, ensure_ascii=False)};')
            page.goto(f'http://{HOST}/src/og.html')
            page.wait_for_selector('body[data-ready="1"]', timeout=15000)
            target = SITE / img / 'og.png'
            page.screenshot(path=str(target))
            page.close()
            print(target.relative_to(SITE), target.stat().st_size // 1024, 'KB')
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:] or [l for l in LANGS if l != 'en'])
