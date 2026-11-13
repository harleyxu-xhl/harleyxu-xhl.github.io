"""Render the homepage's phone screens in every site language.

The screens are Cooldown's drawn UI from its store screenshot template (cooldown repo,
play-store/screenshots/template.html), laid out 360 dp wide without captions or a phone frame and saved as
WebP, so they follow the app's own strings, theme and icons. Each one is drawn for the part of it the page
shows; the heat risk card, which the template lacks, is drawn here after RiskScoreCard in MainActivity.kt.

  python3 src/render_screens.py            # every language
  python3 src/render_screens.py de ja      # only these site languages

Needs ~/projects/manage_apps (tools/screenshots.py) and the cooldown repo, plus Playwright and Pillow.
Writes assets/img/<site lang>/cooldown-<screen>.webp (English stays at assets/img/cooldown-<screen>.webp) and
the pixel size of every image to src/screens.json, which build.py reads.
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
W = 360

# name -> the template expression that draws it, its height in dp (None: as tall as its content), the pixel
# scale, and a script to run once it is laid out. T is the app's dark Classic theme.
SCREENS = {
    'overview': {'ui': 'overviewUI(T)', 'h': 770},
    'insights': {'ui': 'trendsUI(T)', 'h': 770},
    # The page shows the top 540 dp of each screen. Insights scrolled until the heating events lead, with the
    # diagnostics card that follows them in the app; the padding only gives the list room to scroll that far.
    'events': {
        'ui': 'appScreen(T, { nav: "insights", body: `<div class="list">${insightsCard(T)}${diagnosticsCard(T)}</div>` })',
        'h': 770,
        'after': '''const list = document.querySelector(".list");
            list.style.paddingBottom = "320px";
            list.parentElement.scrollTop = document.getElementById("heating").offsetTop - 12;''',
    },
    # A shorter home screen, so the dock closes the part the page shows instead of an empty wallpaper.
    'widget': {'ui': 'homeUI()', 'h': 620},
    # The heat risk card alone, on the app's background.
    'risk': {'ui': 'riskUI(T)', 'h': None, 'scale': 3},
}

# RiskScoreCard (MainActivity.kt) for a Pro user, with the score RiskScorePolicy gives a 42.3°C battery that is
# charging and not rising fast: 12 base + 55 for the temperature + 16 for charging.
RISK = r'''
function riskUI(T) {
  const score = 83, accent = T.hot;
  const text = S("risk_score_format", score), at = text.indexOf(String(score));
  const scale = (t) => `<span style="font-size:13px;font-weight:400;letter-spacing:.5px;color:${T.onSurfaceVariant}">${esc(t)}</span>`;
  const readout = at < 0 ? esc(text) : scale(text.slice(0, at)) + score + scale(text.slice(at + String(score).length));
  const detail = (t) => `<div style="font-size:13px;line-height:20px;color:${T.onSurfaceVariant}">${esc(t)}</div>`;
  const factor = (title, evidence) => `<div class="col" style="gap:3px">
      <div style="font-size:14px;line-height:20px;font-weight:500">${esc(title)}</div>${detail(evidence)}</div>`;
  return `<div style="padding:16px;background:${T.background};color:${T.onSurface}">${card(T, `<div class="col" style="padding:16px;gap:10px">
    <div class="col" style="gap:2px">
      <div style="font-weight:600">${esc(S("risk_score_title"))}</div>
      <div class="row" style="gap:12px;align-items:baseline">
        <div class="grow" style="font-size:22px;line-height:28px;font-weight:600">${readout}</div>
        <div class="row"><i style="width:8px;height:8px;border-radius:50%;background:${accent}"></i>
          <span style="margin-left:6px;font-size:14px;line-height:20px;font-weight:600;color:${accent}">${esc(S("risk_level_high"))}</span></div>
      </div></div>
    <div class="row" style="gap:4px;height:4px">
      <i style="width:${score}%;height:4px;border-radius:2px;background:${accent}"></i>
      <i style="flex:1;height:4px;border-radius:2px;background:${T.surfaceVariant}"></i></div>
    ${detail(S("risk_recent_trend", 5, delta(0.6)))}
    <div style="font-weight:600">${esc(S("risk_evidence_title"))}</div>
    ${factor(S("risk_factor_temperature_hot"), S("risk_evidence_temperature", temp(42.3)))}
    ${factor(S("risk_factor_charging"), S("risk_evidence_charging"))}
  </div>`)}</div>`;
}
'''

DRAW = '''async () => {
    %(risk)s
    const T = theme("Classic", true);
    const canvas = document.getElementById("canvas");
    canvas.className = "canvas";
    canvas.style.width = "%(w)spx"; canvas.style.height = "%(height)s";
    canvas.innerHTML = `<div class="ui" style="%(ui_style)s">${%(ui)s}</div>`;
    await Promise.all([document.fonts.ready, ...[...document.images].map((i) => i.decode())]);
    fit();
    %(after)s
    return canvas.firstElementChild.offsetHeight;
}'''


def out_dir(lang):
    return SITE / 'assets/img' / ('' if lang == 'en' else lang)


def main(langs):
    from PIL import Image
    from playwright.sync_api import sync_playwright

    a = app('cooldown')
    c = S.config(a)
    sizes_file = SITE / 'src/screens.json'
    sizes = json.loads(sizes_file.read_text()) if sizes_file.exists() else {}
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
                    'captures': found, **S.app_data(c, locale), 'slide': 'overview', 'size': [W, 770]}
            target = out_dir(lang)
            target.mkdir(parents=True, exist_ok=True)
            for name, screen in SCREENS.items():
                errors, missing = [], []
                high = screen['h']
                page = browser.new_page(viewport={'width': W, 'height': high or 770},
                                        device_scale_factor=screen.get('scale', 2))
                page.route('**/*', S.serve(c, missing))
                page.add_init_script(f'window.DATA = {json.dumps(base, ensure_ascii=False)};')
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(f'http://{S.HOST}/template.html')
                page.wait_for_selector('body[data-ready="1"]', timeout=15000)
                # Swap the slide for the bare screen, then let the kit lay it out as it does for slides.
                height = page.evaluate(DRAW % {
                    'risk': RISK, 'w': W, 'ui': screen['ui'], 'after': screen.get('after', ''),
                    'height': f'{high}px' if high else 'auto',
                    'ui_style': f'height:{high}px' if high else 'position:static',
                })
                if errors or missing:
                    sys.exit(f'{lang} {name}: {errors} {missing}')
                if not high:
                    page.set_viewport_size({'width': W, 'height': height})
                png = page.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': height})
                page.close()
                file = target / f'cooldown-{name}.webp'
                image = Image.open(io.BytesIO(png)).convert('RGB')
                image.save(file, 'WEBP', quality=82, method=6)
                sizes.setdefault(lang, {})[name] = list(image.size)
                print(file.relative_to(SITE), image.size, file.stat().st_size // 1024, 'KB')
        browser.close()
    sizes_file.write_text(json.dumps({k: sizes[k] for k in LANGS if k in sizes}, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:] or list(LANGS))
