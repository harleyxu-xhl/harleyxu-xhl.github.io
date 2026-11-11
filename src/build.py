"""Build the homepage in every language: index.html (English) and <lang>/index.html, plus sitemap.xml.

  python3 src/build.py

src/page.html is the page with {{key}} slots ({{key|attr}} escapes for an attribute, {{key|json}} writes a JSON
string). src/i18n/<lang>.json holds each language's text; every file must have exactly the keys of en.json. Text may
use {t_hero}, {t_alert}, {threshold}, {w1}, {w2}, {min}, {max} and {avg}, which become temperatures written the way
the app writes them in that language (30,9°C or 30.9°C). src/reviews.json holds the English Google Play reviews
shown on every page, quoted as written. Edit the sources and rebuild; never edit the generated pages by hand.
Screens and Open Graph images come from src/render_screens.py and src/render_og.py.
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SRC = SITE / 'src'
ORIGIN = 'https://harleyxu-xhl.github.io'

# code: (html lang, hreflang, og:locale, name in its own language, decimal comma, Play download count)
# The count mirrors Google Play's public figure in Play's own wording; update every language when Play moves on.
LANGS = {
    'en': ('en', 'en', 'en_US', 'English', False, '50K+'),
    'de': ('de', 'de', 'de_DE', 'Deutsch', True, '50.000+'),
    'es': ('es-419', 'es', 'es_LA', 'Español', True, '50 mil+'),
    'fr': ('fr', 'fr', 'fr_FR', 'Français', True, '50 k+'),
    'hi': ('hi', 'hi', 'hi_IN', 'हिन्दी', False, '50 हज़ार+'),
    'id': ('id', 'id', 'id_ID', 'Bahasa Indonesia', True, '50 rb+'),
    'it': ('it', 'it', 'it_IT', 'Italiano', True, '50.000+'),
    'ja': ('ja', 'ja', 'ja_JP', '日本語', False, '5万+'),
    'ko': ('ko', 'ko', 'ko_KR', '한국어', False, '5만+'),
    'pt': ('pt-BR', 'pt', 'pt_BR', 'Português', True, '50 mil+'),
    'zh': ('zh-Hans', 'zh-Hans', 'zh_CN', '简体中文', False, '5万+'),
}
TEMPS = {'t_hero': 30.9, 't_alert': 42.3, 'threshold': 42, 'w1': 28.0, 'w2': 38.4, 'min': 27.9, 'max': 42.2, 'avg': 34.8}

PLAY = 'https://play.google.com/store/apps/details?id=com.harley.{app}&amp;referrer=utm_source%3Dwebsite%26utm_medium%3Dhomepage%26utm_campaign%3D{campaign}'

# Sent once, before anything renders, from the English page only: a browser whose first language has its own page
# goes there, unless this browser picked a language here before or came from another page of this site.
REDIRECT = '''  <script>
    (() => {
      const pages = %s;
      try {
        if (localStorage.getItem("lang")) return;
        if (document.referrer && new URL(document.referrer).origin === location.origin) return;
        const first = ((navigator.languages && navigator.languages[0]) || navigator.language || "").toLowerCase().split("-")[0];
        const page = pages[first === "in" ? "id" : first];
        if (page) location.replace(page + location.search + location.hash);
      } catch (e) {}
    })();
  </script>'''


def path(code):
    return '/' if code == 'en' else f'/{code}/'


def temp(value, comma):
    text = f'{value:.0f}°C' if isinstance(value, int) else f'{value:.1f}°C'
    return text.replace('.', ',') if comma else text


def fill(template, values, where):
    def slot(m):
        key, mode = m.group(1), m.group(2)
        if key not in values:
            sys.exit(f'{where}: no value for {{{{{key}}}}}')
        value = values[key]
        if mode == 'attr':
            if '&' in value and re.search(r'&\w+;', value):
                sys.exit(f'{where}: {key} has an HTML entity but is used in an attribute')
            return html.escape(value, quote=True).replace('&#x27;', "'")
        if mode == 'json':
            return json.dumps(value, ensure_ascii=False)
        return value
    out = re.sub(r'\{\{(\w+)(?:\|(attr|json))?\}\}', slot, template)
    if '{{' in out:
        sys.exit(f'{where}: unfilled slot near {out[out.index("{{"):][:40]!r}')
    return out


def flatten(text):
    """Nested lists become key_0, key_1, ...; nested objects become key_sub."""
    flat = {}
    for key, value in text.items():
        if isinstance(value, list) and all(isinstance(v, str) for v in value):
            flat.update({f'{key}_{i}': v for i, v in enumerate(value)})
            flat[f'{key}_json'] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, dict) and key != 'months':
            flat.update({f'{key}_{k}': v for k, v in value.items()})
        else:
            flat[key] = value
    return flat


def review_items(code, text, reviews):
    items = []
    stars = html.escape(text['stars'], quote=True)
    for r in text.get('extra_reviews', []) + reviews:
        quote_lang = r.get('lang', 'en')
        attr = '' if quote_lang == LANGS[code][0].split('-')[0] else f' lang="{quote_lang}"'
        month = text['months'][r['month']]
        items.append(f'        <li class="review"><blockquote{attr}><p>“{r["text"]}”</p></blockquote>'
                     f'<div class="review-meta"><svg class="stars" role="img" aria-label="{stars}"><use href="#five-stars"/></svg>'
                     f'<span>Google&nbsp;Play · {month}</span></div></li>')
    return '\n'.join(items)


def lang_links(current):
    menu = []
    for code, (lang, hreflang, _, name, _, _) in LANGS.items():
        here = ' aria-current="true"' if code == current else ''
        menu.append(f'          <li><a href="{path(code)}" hreflang="{hreflang}" lang="{lang}" data-lang="{code}"{here}>{name}</a></li>')
    return '        <ul>\n' + '\n'.join(menu) + '\n        </ul>'


def main():
    template = (SRC / 'page.html').read_text()
    reviews = json.loads((SRC / 'reviews.json').read_text())
    texts = {code: json.loads((SRC / 'i18n' / f'{code}.json').read_text()) for code in LANGS}
    keys = set(texts['en']) | {'extra_reviews'}
    for code, text in texts.items():
        if set(text) - keys or set(texts['en']) - set(text):
            sys.exit(f'{code}.json: missing {sorted(set(texts["en"]) - set(text))}, extra {sorted(set(text) - keys)}')
        for key in ('levels', 'nots'):
            if len(text[key]) != len(texts['en'][key]):
                sys.exit(f'{code}.json: {key} needs {len(texts["en"][key])} entries')
        missing = {r['month'] for r in reviews + text.get('extra_reviews', [])} - set(text['months'])
        if missing:
            sys.exit(f'{code}.json: months missing {sorted(missing)}')

    alternates = [f'  <link rel="alternate" hreflang="{v[1]}" href="{ORIGIN}{path(c)}">' for c, v in LANGS.items()]
    alternates.append(f'  <link rel="alternate" hreflang="x-default" href="{ORIGIN}/">')
    pages = json.dumps({c: path(c) for c in LANGS if c != 'en'})

    for code, (lang, _, og_locale, name, comma, count) in LANGS.items():
        text = texts[code]
        temps = {k: temp(v, comma) for k, v in TEMPS.items()}

        def localize(value):
            if isinstance(value, str):
                for k, v in temps.items():
                    value = value.replace('{' + k + '}', v)
                if re.search(r'\{\w+\}', value):
                    sys.exit(f'{code}.json: unknown placeholder in {value[:60]!r}')
                return value
            if isinstance(value, list):
                return [localize(v) for v in value]
            if isinstance(value, dict):
                return {k: localize(v) for k, v in value.items()}
            return value

        text = {k: localize(v) for k, v in text.items()}
        menu = lang_links(code)
        img = '/assets/img/' if code == 'en' else f'/assets/img/{code}/'
        values = {
            **flatten({k: v for k, v in text.items() if k != 'extra_reviews'}),
            **temps,
            'html_lang': lang,
            'og_locale': og_locale,
            'lang_name': name,
            'url': ORIGIN + path(code),
            'alternates': '\n'.join(alternates),
            'og_image': f'{ORIGIN}{img}og.png',
            'redirect': REDIRECT % pages if code == 'en' else '',
            'img': img,
            'badge': '/assets/img/google-play-badge.png' if code == 'en' else f'{img}google-play-badge.png',
            'badge_w': '564' if code == 'en' else '646',
            'badge_h': '168' if code == 'en' else '192',
            'count': count,
            'play_hero': PLAY.format(app='cooldown', campaign='hero'),
            'play_pro': PLAY.format(app='cooldown', campaign='pro'),
            **{f'play_{a}': PLAY.format(app=a, campaign='more_apps') for a in ('angora', 'pipit', 'somna', 'wattlab')},
            'reviews': review_items(code, text, reviews),
            'lang_menu': menu,
        }
        page = fill(template, values, f'{code}')
        page = re.sub(r'\n{3,}', '\n\n', page).replace('\n\n  <script type="application/ld+json">', '\n  <script type="application/ld+json">', 1)
        target = SITE / ('index.html' if code == 'en' else f'{code}/index.html')
        target.parent.mkdir(exist_ok=True)
        target.write_text(page)
        print(target.relative_to(SITE))

    links = '\n'.join(f'    <xhtml:link rel="alternate" hreflang="{v[1]}" href="{ORIGIN}{path(c)}"/>' for c, v in LANGS.items())
    urls = '\n'.join(f'  <url>\n    <loc>{ORIGIN}{path(c)}</loc>\n{links}\n'
                     f'    <xhtml:link rel="alternate" hreflang="x-default" href="{ORIGIN}/"/>\n  </url>' for c in LANGS)
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                      'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + '\n</urlset>\n')
    print('sitemap.xml')


if __name__ == '__main__':
    main()
