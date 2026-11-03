"""Render the homepage's phone screens in every site language.

The screens are Cooldown's drawn UI from its store screenshot template (cooldown repo,
play-store/screenshots/template.html), laid out at 360 x 770 dp without captions or a phone frame and saved
at 2x as 720 x 1540 WebP, so they follow the app's own strings, theme and icons.

  python3 src/render_screens.py            # every language
  python3 src/render_screens.py de ja      # only these site languages

Needs ~/projects/manage_apps (tools/screenshots.py) and the cooldown repo, plus Playwright and Pillow.
Writes assets/img/<site lang>/cooldown-<screen>.webp (English stays at assets/img/cooldown-<screen>.webp).
"""
import io
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path.home() / 'projects/manage_apps/tools'))
import screenshots as S  # noqa: E402
from common import app  # noqa: E402

# Site language -> the store screenshot copy/locale used by the template.
LANGS = {'en': 'en-US', 'de': 'de-DE', 'es': 'es-419', 'fr': 'fr-FR', 'hi': 'hi-IN', 'id': 'id', 'it': 'it-IT',
         'ja': 'ja-JP', 'ko': 'ko-KR', 'pt': 'pt-BR', 'zh': 'zh-CN'}
SCREENS = {
    'overview': 'overviewUI(theme("Classic", true))',
    'insights': 'trendsUI(theme("Classic", true))',
    'events': 'trendsUI(theme("Classic", true), "heating")',
    'widget': 'homeUI()',
}
W, H, SCALE = 360, 770, 2


def out_dir(lang):
    return SITE / 'assets/img' / ('' if lang == 'en' else lang)


def main(langs):
    from PIL import Image
    from playwright.sync_api import sync_playwright

    a = app('cooldown')
    c = S.config(a)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in langs:
            locale = LANGS[lang]
            copy = json.loads((c['dir'] / 'copy' / f'{locale}.json').read_text())
            strings, localized = S.android_strings(c['res'], locale)
            if not localized:
                sys.exit(f'{lang}: no Android strings for {locale}')
            found, _ = S.captures(c, locale)
            base = {'lang': locale, 'locale': locale, 'copy': copy, 'strings': strings,
                    'appName': strings.get('app_name', a['name']), 'appIcon': S.data_uri(c['icon']),
                    'captures': found, **S.app_data(c, locale), 'slide': 'overview', 'size': [W, H]}
            target = out_dir(lang)
            target.mkdir(parents=True, exist_ok=True)
            for name, ui in SCREENS.items():
                errors, missing = [], []
                page = browser.new_page(viewport={'width': W, 'height': H}, device_scale_factor=SCALE)
                page.route('**/*', S.serve(c, missing))
                page.add_init_script(f'window.DATA = {json.dumps(base, ensure_ascii=False)};')
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(f'http://{S.HOST}/template.html')
                page.wait_for_selector('body[data-ready="1"]', timeout=15000)
                # Swap the slide for the bare screen, then let the kit scroll lists as it does for slides.
                page.evaluate(f'''async () => {{
                    const canvas = document.getElementById("canvas");
                    canvas.className = "canvas";
                    canvas.style.width = "{W}px"; canvas.style.height = "{H}px";
                    canvas.innerHTML = `<div class="ui" style="height:{H}px">${{{ui}}}</div>`;
                    await Promise.all([document.fonts.ready, ...[...document.images].map((i) => i.decode())]);
                    fit();
                }}''')
                if errors or missing:
                    sys.exit(f'{lang} {name}: {errors} {missing}')
                png = page.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': H})
                page.close()
                file = target / f'cooldown-{name}.webp'
                Image.open(io.BytesIO(png)).convert('RGB').save(file, 'WEBP', quality=82, method=6)
                print(file.relative_to(SITE), file.stat().st_size // 1024, 'KB')
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:] or [l for l in LANGS if l != 'en'])
