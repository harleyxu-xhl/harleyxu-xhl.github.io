"""The drawn parts of the Wattlab page: the power gauge, the ranked setups and the capacity scale.

Geometry, colours and number formats follow the app (wattlab repo): Gauge.kt and ChargePresentation.kt for the
half-circle gauge, Formatters.kt for watts, branding/tokens.json for the tier colours. Readings come from
src/wattlab/data.json. build.py and render_og.py call these to fill the page and the share card.
"""
import html
import json
import math
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent / 'data.json').read_text())

# Dark tokens (the app's default look, and the page's hero in both colour schemes).
CANVAS = '#111214'
TIER_COLOR = {'slow': '#8E8A80', 'standard': '#B8901E', 'fast': '#FFC21A'}
TRACK_TINT = 0.22   # Gauge.kt TRACK_TINT_ALPHA: each tier's colour, faint, over the canvas

# Gauge.kt in dp: a 328 x 171 box, a 14 dp stroke on a half circle, 4 dp gaps where a speed tier starts.
W, H, CX, CY, R, STROKE, GAP = 328, 171, 164, 164, 157, 14, 4

# Phosphor icons the app uses for these lines (PhosphorIcons.kt), on a 256 grid.
ICONS = {
    'lightning': 'M215.79,118.17a8,8,0,0,0-5-5.66L153.18,90.9l14.66-73.33a8,8,0,0,0-13.69-7l-112,120a8,8,0,0,0,3,13l57.63,21.61L88.16,238.43a8,8,0,0,0,13.69,7l112-120A8,8,0,0,0,215.79,118.17ZM109.37,214l10.47-52.38a8,8,0,0,0-5-9.06L62,132.71l84.62-90.66L136.16,94.43a8,8,0,0,0,5,9.06l52.8,19.8Z',
    'hourglass': 'M200,75.64V40a16,16,0,0,0-16-16H72A16,16,0,0,0,56,40V76a16.07,16.07,0,0,0,6.4,12.8L114.67,128,62.4,167.2A16.07,16.07,0,0,0,56,180v36a16,16,0,0,0,16,16H184a16,16,0,0,0,16-16V180.36a16.09,16.09,0,0,0-6.35-12.77L141.27,128l52.38-39.6A16.05,16.05,0,0,0,200,75.64ZM72,40H184V75.64L178.23,80H77.33L72,76ZM128,118L98.67,96h58.4ZM184,216H72V180l48-36v24a8,8,0,0,0,16,0V144.08l48,36.28Z',
    'usb': 'M252.44,121.34l-48-32A8,8,0,0,0,192,96v24H72V72h33a32,32,0,1,0,0-16H72A16,16,0,0,0,56,72v48H8a8,8,0,0,0,0,16H56v48a16,16,0,0,0,16,16h32v8a16,16,0,0,0,16,16h32a16,16,0,0,0,16-16V176a16,16,0,0,0-16-16H120a16,16,0,0,0-16,16v8H72V136H192v24a8,8,0,0,0,12.44,6.66l48-32a8,8,0,0,0,0-13.32ZM136,48a16,16,0,1,1-16,16A16,16,0,0,1,136,48ZM120,176h32v32H120ZM208,145.05V111l25.58,17Z',
    'plug': 'M237.66,66.34a8,8,0,0,0-11.32,0L192,100.69,155.31,64l34.35-34.34a8,8,0,1,0-11.32-11.32L144,52.69,117.66,26.34a8,8,0,0,0-11.32,11.32L112.69,44l-53,53a40,40,0,0,0,0,56.57l15.71,15.71L26.34,218.34a8,8,0,0,0,11.32,11.32l49.09-49.09,15.71,15.71a40,40,0,0,0,56.57,0l53-53,6.34,6.35a8,8,0,0,0,11.32-11.32L203.31,112l34.35-34.34A8,8,0,0,0,237.66,66.34ZM147.72,185a24,24,0,0,1-33.95,0L71,142.23a24,24,0,0,1,0-33.95l53-53L200.69,132Z',
    'battery': 'M200,56H32A24,24,0,0,0,8,80v96a24,24,0,0,0,24,24H200a24,24,0,0,0,24-24V80A24,24,0,0,0,200,56ZM208,176a8,8,0,0,1-8,8H32a8,8,0,0,1-8-8V80a8,8,0,0,1,8-8H200a8,8,0,0,1,8,8ZM256,96v64a8,8,0,0,1-16,0V96a8,8,0,0,1,16,0ZM138.81,123.79a8,8,0,0,1,.35,7.79l-16,32a8,8,0,0,1-14.32-7.16L119.06,136H100a8,8,0,0,1-7.16-11.58l16-32a8,8,0,1,1,14.32,7.16L112.94,120H132A8,8,0,0,1,138.81,123.79Z',
}
TIER_ICON = {'slow': 'hourglass', 'standard': 'lightning', 'fast': 'lightning'}


def icon(name, cls=''):
    return f'<svg class="ic{" " + cls if cls else ""}" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="{ICONS[name]}"/></svg>'


def watts(mw):
    """Formatters.kt: one decimal below 9.95 W, none from there up, rounded half to even."""
    places = Decimal('0.1') if abs(mw) < 9950 else Decimal('1')
    return str((Decimal(mw) / 1000).quantize(places, rounding=ROUND_HALF_EVEN))


def grouped(n):
    return f'{n:,}'


def fraction(mw):
    """ChargePresentation.gaugeFraction: the square root of the share of the 100 W full scale."""
    return math.sqrt(max(0, mw) / DATA['fullScaleMw'])


def _tint(color):
    fg, bg = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (color, CANVAS))
    return '#' + ''.join(f'{round(f * TRACK_TINT + b * (1 - TRACK_TINT)):02x}' for f, b in zip(fg, bg))


def _point(radius, angle):
    a = math.radians(angle)
    return CX + radius * math.cos(a), CY + radius * math.sin(a)


def _arc(start, end):
    (x0, y0), (x1, y1) = _point(R, start), _point(R, end)
    return f'M{x0:.2f},{y0:.2f}A{R},{R} 0 0,1 {x1:.2f},{y1:.2f}'


def gauge_svg(mw):
    """The gauge as Gauge.kt draws it: a track split where each tier starts, and the fill up to the reading.
    The fill is one half circle of path length 1, so its dash length is the gauge fraction."""
    bounds = [0, fraction(DATA['thresholdsMw']['standard']), fraction(DATA['thresholdsMw']['fast']), 1]
    gap = math.degrees(GAP / R)
    tints = [_tint(TIER_COLOR[t]) for t in ('slow', 'standard', 'fast')]
    parts = []
    for i, tint in enumerate(tints):
        start = 180 + 180 * bounds[i] + (gap / 2 if i > 0 else 0)
        end = 180 + 180 * bounds[i + 1] - (gap / 2 if i < 2 else 0)
        parts.append(f'<path d="{_arc(start, end)}" stroke="{tint}"/>')
    ends = (f'<circle cx="{CX - R}" cy="{CY}" r="{STROKE / 2:g}" fill="{tints[0]}"/>'
            f'<circle cx="{CX + R}" cy="{CY}" r="{STROKE / 2:g}" fill="{tints[2]}"/>')
    fill = (f'<path class="gauge-fill" d="{_arc(180, 360)}" pathLength="1" stroke-linecap="round" '
            f'stroke-dasharray="{fraction(mw):.4f} 1"/>')
    return (f'<svg class="gauge" viewBox="0 0 {W} {H}" aria-hidden="true">'
            f'<g fill="none" stroke-width="{STROKE}">{"".join(parts)}</g>{ends}'
            f'<g fill="none" stroke-width="{STROKE}">{fill}</g></svg>')


def gauge_marks():
    """Where the tiers start, written outside the arc, as percentages of the gauge box."""
    marks = []
    for key in ('standard', 'fast'):
        mw = DATA['thresholdsMw'][key]
        x, y = _point(R + STROKE / 2 + 13, 180 + 180 * fraction(mw))
        marks.append(f'<span style="left:{x / W * 100:.2f}%;top:{y / H * 100:.2f}%">{watts(mw).removesuffix(".0")}</span>')
    return ''.join(marks)


def setups(text):
    """(rows of the ranked list, JSON for the script) from data.json and the page's text."""
    best = DATA['setups'][0]['avgMw']
    rows, state = [], []
    for i, s in enumerate(DATA['setups']):
        name, note = text['setups'][s['id']], text['notes'][s['id']]
        tier = text['tiers'][s['tier']]
        reason = text['reasons'][s['reason']] if s['reason'] else ''
        value = watts(s['avgMw'])
        share = max(0.02, s['avgMw'] / best)   # the app's compare bars keep 2% for the slowest
        rows.append(
            f'          <label class="setup" data-tier="{s["tier"]}">\n'
            f'            <input type="radio" name="setup" value="{i}"{" checked" if i == 0 else ""}>\n'
            f'            <span class="setup-rank" aria-hidden="true">{i + 1}</span>\n'
            f'            <span class="setup-name">{html.escape(name)}</span>\n'
            f'            <span class="setup-watts">{value}&nbsp;W</span>\n'
            f'            <span class="setup-bar" aria-hidden="true"><i style="width:{share * 100:.1f}%"></i></span>\n'
            f'            <span class="sr-only">{html.escape(tier)}</span>\n'
            f'          </label>')
        said = text['announce'].replace('{name}', name).replace('{watts}', value).replace('{tier}', tier)
        state.append({'mw': s['avgMw'], 'watts': value, 'tier': s['tier'], 'tierName': tier,
                      'icon': ICONS[TIER_ICON[s['tier']]], 'reason': reason, 'note': note,
                      'said': ' '.join(filter(None, (said, reason and reason + text['stop'], note)))})
    return '\n'.join(rows), json.dumps(state, ensure_ascii=False)


def capacity():
    """Positions on the capacity scale, as percentages of an axis from 5,700 to 6,400 mAh."""
    h = DATA['health']
    low, high = 5700, 6400
    at = lambda mah: f'{(mah - low) / (high - low) * 100:.2f}%'
    spread = round(h['capacityMah'] * h['margin'])
    lo, hi = h['capacityMah'] - spread, h['capacityMah'] + spread
    charges = ''.join(f'<i class="cap-charge" style="left:{at(m)}"></i>' for m in sorted(set(h['chargesMah'])))
    return {
        'cap_value': grouped(h['capacityMah']),
        'cap_margin': f'±{round(h["margin"] * 100)}%',
        'cap_low': grouped(lo), 'cap_high': grouped(hi),
        'cap_low_at': at(lo), 'cap_high_at': at(hi), 'cap_width': f'{(hi - lo) / (high - low) * 100:.2f}%',
        'cap_at': at(h['capacityMah']),
        'cap_rated': grouped(h['ratedMah']), 'cap_rated_at': at(h['ratedMah']),
        'cap_marks': charges,
        'cap_count': str(len(h['chargesMah'])),
        'cap_percent': str(h['percent']),
        'cap_cycles': grouped(h['cycles']),
    }
