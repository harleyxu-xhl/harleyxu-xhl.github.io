"""Helpers for Somna's page: sleep efficiency gauge, bedtime presets, and CBT-I data."""
import json
import math

ICONS = {
    'moon': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M233.54,142.23a8,8,0,0,0-8-2,88.08,88.08,0,0,1-109.8-109.8,8,8,0,0,0-10-10,104.84,104.84,0,0,0-52.91,37A104,104,0,0,0,136,224a103.09,103.09,0,0,0,62.52-20.88,104.84,104.84,0,0,0,37-52.91A8,8,0,0,0,233.54,142.23Z"/></svg>',
    'bed': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M208,80H24A16,16,0,0,0,8,96V208a8,8,0,0,0,16,0V184H232v24a8,8,0,0,0,16,0V136A56.06,56.06,0,0,0,208,80ZM24,112H104v56H24ZM120,112H208a40,40,0,0,1,40,40v16H120ZM24,96h80a16,16,0,0,1,16,16v0H24Z"/></svg>',
    'spark': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M213.66,82.34l-56-56a8,8,0,0,0-11.32,0l-56,56a8,8,0,0,0,0,11.32l56,56a8,8,0,0,0,11.32,0l56-56A8,8,0,0,0,213.66,82.34ZM152,124.69,107.31,80,152,35.31,196.69,80Zm-69.66,77-24-24a8,8,0,0,0-11.32,0l-24,24a8,8,0,0,0,0,11.32l24,24a8,8,0,0,0,11.32,0l24-24A8,8,0,0,0,82.34,201.66ZM47,208l13-13,13,13-13,13Z"/></svg>',
    'clock': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm64-88a8,8,0,0,1-8,8H128a8,8,0,0,1-8-8V72a8,8,0,0,1,16,0v48h48A8,8,0,0,1,192,128Z"/></svg>',
    'check': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/></svg>',
    'play': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M240,128a15.74,15.74,0,0,1-7.6,13.51L88.32,229.65A16,16,0,0,1,64,216.13V39.87a16,16,0,0,1,24.32-13.52L232.4,114.49A15.74,15.74,0,0,1,240,128Z"/></svg>',
    'pause': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M216,48V208a16,16,0,0,1-16,16H160a16,16,0,0,1-16-16V48a16,16,0,0,1,16-16h40A16,16,0,0,1,216,48ZM96,32H56A16,16,0,0,0,40,48V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V48A16,16,0,0,0,96,32Z"/></svg>',
}

# The 3 interactive scenarios for the hero console
PRESETS = [
    {
        'id': 'insomnia',
        'key': 'preset_insomnia',
        'bedtime': '22:30',
        'latency': 60,
        'wakings': 75,
        'wakeTime': '07:00',
        'timeInBedMin': 510,     # 8h 30m
        'asleepMin': 375,        # 6h 15m
        'efficiency': 74,
        'targetMet': False,
        'tier': 'low',
        'window': '00:00 – 07:00',
        'sleepWindowDuration': '7h 00m',
    },
    {
        'id': 'broken',
        'key': 'preset_broken',
        'bedtime': '23:00',
        'latency': 25,
        'wakings': 120,
        'wakeTime': '07:30',
        'timeInBedMin': 510,     # 8h 30m
        'asleepMin': 365,        # 6h 05m
        'efficiency': 71,
        'targetMet': False,
        'tier': 'low',
        'window': '00:30 – 07:00',
        'sleepWindowDuration': '6h 30m',
    },
    {
        'id': 'week4',
        'key': 'preset_week4',
        'bedtime': '23:45',
        'latency': 15,
        'wakings': 20,
        'wakeTime': '07:00',
        'timeInBedMin': 435,     # 7h 15m
        'asleepMin': 400,        # 6h 40m
        'efficiency': 92,
        'targetMet': True,
        'tier': 'optimal',
        'window': '23:30 – 07:00',
        'sleepWindowDuration': '7h 30m',
    },
]


def efficiency_ring_svg(efficiency=74, size=240, stroke=14):
    """Draw a circular gauge for sleep efficiency with the 85% target mark."""
    r = (size - stroke) / 2
    c = 2 * math.pi * r
    # Efficiency is 0-100. Arc starts from top (-90 deg).
    offset = c * (1 - efficiency / 100)
    
    # 85% mark coordinates: angle in radians from top
    angle_85 = -math.pi / 2 + (0.85 * 2 * math.pi)
    cx, cy = size / 2, size / 2
    r_inner = r - stroke / 2 - 4
    r_outer = r + stroke / 2 + 4
    x1 = cx + r_inner * math.cos(angle_85)
    y1 = cy + r_inner * math.sin(angle_85)
    x2 = cx + r_outer * math.cos(angle_85)
    y2 = cy + r_outer * math.sin(angle_85)
    
    return f'''<svg class="eff-ring" viewBox="0 0 {size} {size}" width="{size}" height="{size}" aria-hidden="true">
  <circle class="ring-bg" cx="{cx}" cy="{cy}" r="{r}" stroke-width="{stroke}" fill="none"/>
  <circle class="ring-fill" cx="{cx}" cy="{cy}" r="{r}" stroke-width="{stroke}" fill="none"
          stroke-dasharray="{c:.2f}" stroke-dashoffset="{offset:.2f}"
          transform="rotate(-90 {cx} {cy})"/>
  <line class="target-mark" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width="2.5"/>
</svg>'''


def presets_html(text):
    """Render the 3 preset radio buttons for Somna's hero console."""
    buttons = []
    for i, p in enumerate(PRESETS):
        name = text[p['key']]
        checked = ' checked' if i == 0 else ''
        buttons.append(f'''          <label class="preset-btn">
            <input type="radio" name="somna_preset" value="{p['id']}"{checked}>
            <span>{name}</span>
          </label>''')
    return '\n'.join(buttons)


def presets_json(text):
    """Serialize the preset scenarios for client-side JS."""
    data = []
    for p in PRESETS:
        item = dict(p)
        item['name'] = text[p['key']]
        item['diagnosis'] = text[f"{p['id']}_diagnosis"]
        item['prescription'] = text[f"{p['id']}_prescription"]
        item['statusLabel'] = text['optimal_label'] if p['targetMet'] else text['low_label']
        item['asleepFormatted'] = text['hours_mins'].format(h=p['asleepMin'] // 60, m=p['asleepMin'] % 60)
        item['awakeFormatted'] = text['hours_mins'].format(h=(p['timeInBedMin'] - p['asleepMin']) // 60, m=(p['timeInBedMin'] - p['asleepMin']) % 60)
        data.append(item)
    return json.dumps(data, ensure_ascii=False)
