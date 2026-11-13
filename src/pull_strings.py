"""Copy the app strings the homepage quotes from the cooldown repo into src/app_strings.json.

The temperature scale shows the app's own advice and alert text for each level, and the heat risk card is
described in the card's own words, all in the app's translations, so those lines are copied from the Android
resources instead of being written again for the site.

  python3 src/pull_strings.py

Needs ~/projects/manage_apps (tools/screenshots.py) and the cooldown repo. build.py reads the JSON; run this
again when the app changes one of these strings.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / 'projects/manage_apps/tools'))
import screenshots as S  # noqa: E402
from common import app  # noqa: E402
from render_screens import LANGS  # noqa: E402

KEYS = [
    'temperature_advice_normal', 'temperature_advice_warm', 'temperature_advice_overheated',
    'temperature_advice_critical',
    'high_temperature_alert_warning_title', 'high_temperature_alert_battery_warning',
    'high_temperature_alert_critical_title', 'high_temperature_alert_battery_critical',
    'alert_card_title',
    'risk_score_title', 'risk_score_format', 'risk_level_high', 'risk_evidence_title',
    'risk_factor_temperature_hot', 'risk_evidence_temperature', 'risk_factor_charging', 'risk_evidence_charging',
]


def main():
    c = S.config(app('cooldown'))
    out = {}
    for lang, locale in LANGS.items():
        strings, localized = S.android_strings(c['res'], locale)
        if not localized:
            sys.exit(f'{lang}: no Android strings for {locale}')
        # %1$s is the battery temperature in every one of these and %1$d the risk score; the page fills {t} and {n}.
        out[lang] = {k: re.sub(r'%1\$d', '{n}', re.sub(r'%1\$s', '{t}', strings[k])) for k in KEYS}
    (SRC / 'app_strings.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print('app_strings.json:', len(out), 'languages,', len(KEYS), 'strings')


if __name__ == '__main__':
    main()
