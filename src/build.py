"""Build every page of the site in every language it has, plus sitemap.xml.

  python3 src/build.py

Pages. Cooldown is the homepage: index.html (English) and <lang>/index.html, from src/page.html and
src/i18n/<lang>.json, in Cooldown's 11 languages. Wattlab is wattlab/index.html and wattlab/zh/index.html, from
src/wattlab/page.html and src/wattlab/i18n/<lang>.json, in Wattlab's two languages. A page is offered in the
languages its app is offered in, so its screens and its text always match.

Templates have {{key}} slots ({{key|attr}} escapes for an attribute, {{key|json}} writes a JSON string). Every
language file of a page must have exactly the keys of its en.json. The top line of apps, the language menu, the
other apps' cards and the footer are the same on every page and are written here, in the order of APPS; their text
(names of sections, the other apps' one-liners) comes from src/i18n/<lang>.json, except that a page's own app
describes itself for the other pages in its own files (Wattlab's cooldown.kind and cooldown.what).

Cooldown's text may use {t_hero}, {t_alert}, {threshold}, {w1}, {w2}, {min}, {max} and {avg}, which become
temperatures written the way the app writes them in that language (30,9°C or 30.9°C). src/reviews.json holds the
English Google Play reviews shown on every Cooldown page, quoted as written. Wattlab's readings come from
src/wattlab/data.json through src/wattlab/parts.py, and its text may use the {cap_...} values of parts.capacity().

Edit the sources and rebuild; never edit the generated pages by hand. Screens and Open Graph images come from
src/render_screens.py and src/render_og.py (Cooldown) and src/wattlab/render_screens.py and
src/wattlab/render_og.py (Wattlab).
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SRC = SITE / 'src'
ORIGIN = 'https://harleyxu-xhl.github.io'

sys.path.insert(0, str(SRC / 'wattlab'))
import parts  # noqa: E402

# code: (html lang, hreflang, og:locale, name in its own language, decimal comma, Cooldown's Play download count)
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

# The apps in the order they appear everywhere: the top line, the other apps' cards and the privacy links.
APPS = {'cooldown': 'Cooldown', 'wattlab': 'Wattlab', 'somna': 'Somna', 'pipit': 'Pipit', 'angora': 'Angora'}
# Apps with a page of their own: the languages it is built in and the directory it lives in ('' is the site root).
PAGES = {
    'cooldown': {'langs': list(LANGS), 'dir': ''},
    'wattlab': {'langs': ['en', 'zh'], 'dir': 'wattlab/'},
}

PLAY = 'https://play.google.com/store/apps/details?id=com.harley.{app}&amp;referrer=utm_source%3Dwebsite%26utm_medium%3D{medium}%26utm_campaign%3D{campaign}'

GLOBE = '<svg viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M128,24h0A104,104,0,1,0,232,128,104.12,104.12,0,0,0,128,24Zm87.62,96H175.79C174,83.49,159.94,57.67,148.41,42.4A88.19,88.19,0,0,1,215.62,120ZM96.23,136h63.54c-2.31,41.61-22.23,67.11-31.77,77C118.45,203.1,98.54,177.6,96.23,136Zm0-16C98.54,78.39,118.46,52.89,128,43c9.55,9.93,29.46,35.43,31.77,77Zm11.36-77.6C96.06,57.67,82,83.49,80.21,120H40.37A88.19,88.19,0,0,1,107.59,42.4ZM40.37,136H80.21c1.82,36.51,15.85,62.33,27.38,77.6A88.19,88.19,0,0,1,40.37,136Zm108,77.6c11.53-15.27,25.56-41.09,27.38-77.6h39.84A88.19,88.19,0,0,1,148.41,213.6Z"/></svg>'
ARROW = '<svg viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M200,64V168a8,8,0,0,1-16,0V83.31L69.66,197.66a8,8,0,0,1-11.32-11.32L172.69,72H88a8,8,0,0,1,0-16H192A8,8,0,0,1,200,64Z"/></svg>'

# Sent once, before anything renders, from an English page only: a browser whose first language has its own page
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

MENU_SCRIPT = '''    (() => {
      // Picking a language remembers it, so the English page stops sending this browser to its own language.
      for (const link of document.querySelectorAll("a[data-lang]")) {
        link.addEventListener("click", () => { try { localStorage.setItem("lang", link.dataset.lang); } catch (e) {} });
      }
      // The menu closes on Escape or a click outside it.
      const menu = document.querySelector(".lang-menu");
      document.addEventListener("click", (event) => { if (menu.open && !menu.contains(event.target)) menu.open = false; });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
      });
    })();'''


def path(app, code):
    """The page of `app` in language `code`, or its English page when it is not built in that language."""
    page = PAGES[app]
    return '/' + page['dir'] + ('' if code == 'en' or code not in page['langs'] else f'{code}/')


def play(app, medium, campaign):
    return PLAY.format(app=app, medium=medium, campaign=campaign)


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


def localize(value, known, where):
    """Replace {name} in every string of `value` with known[name]."""
    if isinstance(value, str):
        for k, v in known.items():
            value = value.replace('{' + k + '}', v)
        if re.search(r'\{\w+\}', value):
            sys.exit(f'{where}: unknown placeholder in {value[:60]!r}')
        return value
    if isinstance(value, list):
        return [localize(v, known, where) for v in value]
    if isinstance(value, dict):
        return {k: localize(v, known, where) for k, v in value.items()}
    return value


def load(folder, codes, lists=()):
    """The language files of one page, checked against its en.json."""
    texts = {code: json.loads((folder / f'{code}.json').read_text()) for code in codes}
    keys = set(texts['en']) | {'extra_reviews'}
    for code, text in texts.items():
        where = f'{folder.relative_to(SRC)}/{code}.json'
        if set(text) - keys or set(texts['en']) - set(text):
            sys.exit(f'{where}: missing {sorted(set(texts["en"]) - set(text))}, extra {sorted(set(text) - keys)}')
        for key, value in texts['en'].items():
            if isinstance(value, dict) and key != 'months' and set(value) != set(text[key]):
                sys.exit(f'{where}: {key} needs exactly the keys {sorted(value)}')
        for key in lists:
            if len(text[key]) != len(texts['en'][key]):
                sys.exit(f'{where}: {key} needs {len(texts["en"][key])} entries')
    return texts


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


# ---- Parts every page shares ------------------------------------------------------------------

def nav(app, code, label):
    """The top line: this page's app, apps with a page of their own, and the rest as links to their cards below."""
    links = []
    for other, name in APPS.items():
        if other == app:
            links.append(f'      <a href="#{other}" aria-current="page">{name}</a>')
        elif other in PAGES:
            links.append(f'      <a href="{path(other, code)}">{name}</a>')
        else:
            links.append(f'      <a href="#{other}">{name}</a>')
    return (f'    <nav class="apps-nav" aria-label="{html.escape(label, quote=True)}">\n' + '\n'.join(links) + '\n    </nav>')


def lang_menu(app, current):
    menu = []
    for code in PAGES[app]['langs']:
        lang, hreflang, _, name, _, _ = LANGS[code]
        here = ' aria-current="true"' if code == current else ''
        menu.append(f'          <li><a href="{path(app, code)}" hreflang="{hreflang}" lang="{lang}" data-lang="{code}"{here}>{name}</a></li>')
    return '        <ul>\n' + '\n'.join(menu) + '\n        </ul>'


def more_apps(app, code, text, medium):
    """A card for each of the other apps. An app with a page of its own is named with a link to it."""
    cards = []
    for other, name in APPS.items():
        if other == app:
            continue
        title = f'<a href="{path(other, code)}">{name}</a>' if other in PAGES else name
        cards.append(f'''        <li class="app" id="{other}">
          <img src="/assets/img/icon-{other}.webp" width="160" height="160" loading="lazy" alt="">
          <div>
            <h3>{title}</h3>
            <p class="kind">{text[other]['kind']}</p>
            <p class="what">{text[other]['what']}</p>
            <a class="go" href="{play(other, medium, 'more_apps')}">{text['get_it']}{ARROW}</a>
          </div>
        </li>''')
    return '\n'.join(cards)


def footer(text):
    privacy = ', '.join(f'<a href="/{app}-website/privacy.html">{name}</a>' for app, name in APPS.items())
    return f'''  <footer class="foot wrap">
    <p><b>{text['contact']}</b><a href="mailto:tamariskx@gmail.com">tamariskx@gmail.com</a></p>
    <p><b>{text['privacy']}</b>{privacy}</p>
    <p class="fine">{text['trademark']}</p>
  </footer>'''


def alternates(app):
    links = [f'  <link rel="alternate" hreflang="{LANGS[c][1]}" href="{ORIGIN}{path(app, c)}">' for c in PAGES[app]['langs']]
    links.append(f'  <link rel="alternate" hreflang="x-default" href="{ORIGIN}{path(app, "en")}">')
    return '\n'.join(links)


def shared(app, code, text, medium):
    """Slots every template has. `text` is the site's text in this language (src/i18n) plus the page's own."""
    lang, _, og_locale, name, _, _ = LANGS[code]
    others = {c: path(app, c) for c in PAGES[app]['langs'] if c != 'en'}
    badge = '/assets/img/google-play-badge.png' if code == 'en' else f'/assets/img/{code}/google-play-badge.png'
    return {
        'html_lang': lang,
        'og_locale': og_locale,
        'lang_name': name,
        'url': ORIGIN + path(app, code),
        'alternates': alternates(app),
        'redirect': REDIRECT % json.dumps(others) if code == 'en' else '',
        'nav': nav(app, code, text['nav_label']),
        'globe': GLOBE,
        'lang_menu': lang_menu(app, code),
        'more_apps': more_apps(app, code, text, medium),
        'footer': footer(text),
        'menu_script': MENU_SCRIPT,
        'badge': badge,
        'badge_w': '564' if code == 'en' else '646',
        'badge_h': '168' if code == 'en' else '192',
    }


def write(app, code, page):
    page = re.sub(r'\n{3,}', '\n\n', page).replace('\n\n  <script type="application/ld+json">', '\n  <script type="application/ld+json">', 1)
    target = SITE / path(app, code).lstrip('/') / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page)
    print(target.relative_to(SITE))


# ---- Pages ------------------------------------------------------------------------------------

def build_cooldown(site):
    template = (SRC / 'page.html').read_text()
    reviews = json.loads((SRC / 'reviews.json').read_text())
    for code, text in site.items():
        missing = {r['month'] for r in reviews + text.get('extra_reviews', [])} - set(text['months'])
        if missing:
            sys.exit(f'i18n/{code}.json: months missing {sorted(missing)}')
    for code in PAGES['cooldown']['langs']:
        comma, count = LANGS[code][4], LANGS[code][5]
        temps = {k: temp(v, comma) for k, v in TEMPS.items()}
        text = localize(site[code], temps, f'i18n/{code}.json')
        img = '/assets/img/' if code == 'en' else f'/assets/img/{code}/'
        values = {
            **flatten({k: v for k, v in text.items() if k != 'extra_reviews'}),
            **temps,
            **shared('cooldown', code, text, 'homepage'),
            'og_image': f'{ORIGIN}{img}og.png',
            'img': img,
            'count': count,
            'play_hero': play('cooldown', 'homepage', 'hero'),
            'play_pro': play('cooldown', 'homepage', 'pro'),
            'reviews': review_items(code, text, reviews),
        }
        write('cooldown', code, fill(template, values, f'cooldown {code}'))


def build_wattlab(site):
    template = (SRC / 'wattlab/page.html').read_text()
    codes = PAGES['wattlab']['langs']
    own = load(SRC / 'wattlab/i18n', codes, lists=('nots',))
    capacity = parts.capacity()
    first = parts.DATA['setups'][0]
    for code in codes:
        # The announce line keeps its {name}, {watts} and {tier}: parts.setups() fills them for each setup.
        text = localize({k: v for k, v in own[code].items() if k != 'announce'}, capacity, f'wattlab/i18n/{code}.json')
        text['announce'] = own[code]['announce']
        rows, state = parts.setups(text)
        img = '/assets/img/wattlab/' if code == 'en' else f'/assets/img/wattlab/{code}/'
        values = {
            **{k: site[code][k] for k in ('skip', 'language', 'more_title')},
            **flatten(text),
            **capacity,
            **shared('wattlab', code, {**site[code], **text}, 'wattlab'),
            'og_image': f'{ORIGIN}{img}og.png',
            'img': img,
            'play_hero': play('wattlab', 'wattlab', 'hero'),
            'play_pro': play('wattlab', 'wattlab', 'pro'),
            'gauge': parts.gauge_svg(first['avgMw']),
            'gauge_marks': parts.gauge_marks(),
            'tier_icon': parts.ICONS[parts.TIER_ICON[first['tier']]],
            'watts_first': parts.watts(first['avgMw']),
            'icon_plug': parts.icon('plug'),
            'icon_battery': parts.icon('battery', 'batt'),
            'setups': rows,
            'setups_json': state,
        }
        write('wattlab', code, fill(template, values, f'wattlab {code}'))


def sitemap():
    urls = []
    for app, page in PAGES.items():
        links = '\n'.join(f'    <xhtml:link rel="alternate" hreflang="{LANGS[c][1]}" href="{ORIGIN}{path(app, c)}"/>' for c in page['langs'])
        urls += [f'  <url>\n    <loc>{ORIGIN}{path(app, c)}</loc>\n{links}\n'
                 f'    <xhtml:link rel="alternate" hreflang="x-default" href="{ORIGIN}{path(app, "en")}"/>\n  </url>' for c in page['langs']]
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                      'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(urls) + '\n</urlset>\n')
    print('sitemap.xml')


def main():
    site = load(SRC / 'i18n', list(LANGS), lists=('levels', 'nots'))
    build_cooldown(site)
    build_wattlab(site)
    sitemap()


if __name__ == '__main__':
    main()
