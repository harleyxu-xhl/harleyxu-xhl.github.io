"""Render the Wattlab page's phone screens in English and Simplified Chinese.

The screens are Wattlab's UI as its promo video draws it (wattlab repo, branding/promo-video/promo.html): Compose
layouts in dp, the app's own strings, tokens and icons, and readings its domain code produced from recorded traces
(promo-data.json). This script opens that page at a moment of the video, lays the phone flat and saves the bare
360 x 760 dp screen at 2x as a 720 x 1520 WebP. Chinese text comes from the app's values-zh-rCN strings.

  python3 src/wattlab/render_screens.py          # both languages
  python3 src/wattlab/render_screens.py zh       # only this one

Needs the wattlab repo at ~/projects/wattlab, Playwright, Pillow and the Inter font.
Writes assets/img/wattlab/<screen>.webp (English) and assets/img/wattlab/zh/<screen>.webp.
"""
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent.parent
WATTLAB = Path.home() / 'projects/wattlab'
PROMO = WATTLAB / 'branding/promo-video'
HOST = 'promo.local'

# Screen -> second of the video at which the phone shows it at rest.
SCREENS = {
    'charge': 7.6,     # Charge tab, 90 W charger + original cable: 30 W, Fast
    'slow': 15.9,      # Charge tab, the same charger with a generic cable: Slow, charging at basic USB speed
    'result': 13.6,    # Test result: 31 W, fastest on this phone so far
}
# Setups are the user's own labels in the app; the Chinese ones use the app's words for charger and cable.
SETUPS_ZH = {
    '90 W charger + original cable': '90 W 充电头 + 原装线',
    '18 W charger + original cable': '18 W 充电头 + 原装线',
    '90 W charger + generic cable': '90 W 充电头 + 普通线',
    'Computer USB port': '电脑 USB 口',
}
FLAT = '''
  #phoneWrap { transform: none !important; filter: none !important; opacity: 1 !important; visibility: visible !important; }
  #viewport, #stage { height: 1600px !important; }
  #world { perspective: none !important; }
  #copies, #ov, #end, #vignette, #controls, #tc { display: none !important; }
  .frame { border: 0 !important; border-radius: 0 !important; }
  svg.pov { left: 0 !important; top: 0 !important; }
'''


def unescape(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    return text.replace('\\n', '\n').replace("\\'", "'").replace('\\"', '"').replace('\\@', '@')


def zh_strings(wanted):
    """The app's Simplified Chinese strings for the keys the promo page uses; keys without one keep English."""
    found = {}
    for node in ET.parse(WATTLAB / 'app/src/main/res/values-zh-rCN/strings.xml').getroot():
        name = node.get('name')
        if name not in wanted:
            continue
        if node.tag == 'string':
            found[name] = unescape(''.join(node.itertext()))
        elif node.tag == 'plurals':
            other = unescape(next(i for i in node if i.get('quantity') == 'other').text or '')
            found[name] = {'one': other, 'other': other}
    return found


def assets(lang):
    source = (PROMO / 'assets.js').read_text()
    if lang == 'en':
        return source
    wanted = set(json.loads(re.search(r'"strings":(\{.*?\}),"glyph"', source, re.S).group(1)))
    patch = {'strings': zh_strings(wanted), 'setups': SETUPS_ZH}
    return source + f'''
(() => {{
  const patch = {json.dumps(patch, ensure_ascii=False)};
  Object.assign(window.WL.strings, patch.strings);
  for (const row of window.WL.data.ranking) row.name = patch.setups[row.name] ?? row.name;
}})();
'''


def main(langs):
    from PIL import Image
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in langs:
            script = assets(lang)

            def serve(route, _request, script=script):
                name = route.request.url.split(HOST, 1)[1].split('?')[0].lstrip('/')
                if name == 'assets.js':
                    return route.fulfill(body=script, content_type='text/javascript; charset=utf-8')
                target = (PROMO / name).resolve()
                if target.is_relative_to(PROMO) and target.is_file():
                    return route.fulfill(path=str(target))
                route.fulfill(status=404, body='')

            errors = []
            page = browser.new_page(viewport={'width': 1920, 'height': 1600}, device_scale_factor=1)
            page.route(f'http://{HOST}/**', serve)
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://{HOST}/promo.html?render=1')
            page.wait_for_function('window.promoReady === true', timeout=20000)
            if lang == 'zh':
                page.evaluate('''() => {
                    document.documentElement.lang = "zh-CN";
                    document.body.style.fontFamily = '"Inter", "Noto Sans CJK SC", sans-serif';
                }''')
            page.add_style_tag(content=FLAT)
            target = SITE / 'assets/img/wattlab' / ('' if lang == 'en' else lang)
            target.mkdir(parents=True, exist_ok=True)
            for name, second in SCREENS.items():
                page.evaluate('async (t) => { renderFrame(t); await document.fonts.ready; }', second)
                box = page.locator('#screen').bounding_box()
                if errors:
                    sys.exit(f'{lang} {name}: {errors}')
                png = page.screenshot(clip=box)
                file = target / f'{name}.webp'
                image = Image.open(io.BytesIO(png)).convert('RGB')
                image.save(file, 'WEBP', quality=84, method=6)
                print(file.relative_to(SITE), image.size, file.stat().st_size // 1024, 'KB')
            page.close()
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:] or ['en', 'zh'])
