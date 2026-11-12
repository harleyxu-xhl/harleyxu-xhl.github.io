"""Render Wattlab's 1200 x 630 Open Graph card in both of its languages from src/wattlab/og.html.

  python3 src/wattlab/render_og.py          # both languages
  python3 src/wattlab/render_og.py zh       # only this one

Text comes from src/wattlab/i18n/<lang>.json (tagline, h1, og_free, flow, tiers.fast); the gauge is the page's own,
from parts.py, at the fastest result in data.json. Writes assets/img/wattlab/og.png and assets/img/wattlab/zh/og.png.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent.parent
HOST = 'site.local'
HTML_LANG = {'en': 'en', 'zh': 'zh-Hans'}

sys.path.insert(0, str(HERE))
import parts  # noqa: E402


def card(lang):
    text = json.loads((HERE / 'i18n' / f'{lang}.json').read_text())
    first = parts.DATA['setups'][0]
    meter = (f'{parts.gauge_svg(first["avgMw"])}<p class="marks">{parts.gauge_marks()}</p>'
             f'<p class="read"><span class="chip">{parts.icon(parts.TIER_ICON[first["tier"]])}'
             f'<span>{text["tiers"][first["tier"]]}</span></span>'
             f'<span class="num"><b class="watts">{parts.watts(first["avgMw"])}</b><span class="unit">W</span></span></p>')
    flow = (f'<span class="end">0</span><span class="flow-mid">{parts.icon("plug")}'
            '<svg class="arrow" viewBox="0 0 48 14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">'
            f'<path d="M2.2,7H43.8M40.8,2.5L45.8,7M40.8,11.5L45.8,7"/></svg>{parts.icon("battery", "batt")}'
            f'<span>{text["flow"]}</span></span><span class="end">100&nbsp;W</span>')
    return {'lang': HTML_LANG[lang], 'tagline': text['tagline'], 'h1': text['h1'], 'free': text['og_free'],
            'meter': meter, 'flow': flow}


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
            page.goto(f'http://{HOST}/src/wattlab/og.html')
            page.wait_for_selector('body[data-ready="1"]', timeout=15000)
            target = SITE / 'assets/img/wattlab' / ('' if lang == 'en' else lang) / 'og.png'
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target))
            page.close()
            print(target.relative_to(SITE), target.stat().st_size // 1024, 'KB')
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:] or ['en', 'zh'])
