"""Helpers for Pipit's page: compression simulation, aspect ratio specs, and format data."""
import json

ICONS = {
    'viewfinder': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M192,64V168a8,8,0,0,1-16,0V83.31L69.66,197.66a8,8,0,0,1-11.32-11.32L172.69,72H88a8,8,0,0,1,0-16H192A8,8,0,0,1,192,64Z"/></svg>',
    'crop': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M224,192H72V40a8,8,0,0,0-16,0V56H24a8,8,0,0,0,0,16H56V192a16,16,0,0,0,16,16H192v32a8,8,0,0,0,16,0V224h32a8,8,0,0,0,0-16H208v-16A16,16,0,0,0,224,192ZM72,192V72H192v16H88a8,8,0,0,0-8,8v96Z"/></svg>',
    'compress': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M208,40H48A16,16,0,0,0,32,56V200a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V56A16,16,0,0,0,208,40ZM48,56H208V96H48ZM208,200H48V112H208v88Zm-64-56a8,8,0,0,1-8,8H120v16a8,8,0,0,1-16,0V152H88a8,8,0,0,1,0-16h16V120a8,8,0,0,1,16,0v16h16A8,8,0,0,1,144,144Z"/></svg>',
    'shield': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M208,40H48A16,16,0,0,0,32,56v58.78c0,89.61,75.82,119.34,91,124.39a15.54,15.54,0,0,0,10,0c15.18-5.05,91-34.78,91-124.39V56A16,16,0,0,0,208,40Zm0,74.78c0,76.68-63.09,103.84-80,110.12C111.09,218.62,48,191.46,48,114.78V56H208Z"/></svg>',
    'batch': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M216,40H72A16,16,0,0,0,56,56V72H40A16,16,0,0,0,24,88V200a16,16,0,0,0,16,16H184a16,16,0,0,0,16-16V184h16a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM184,200H40V88H184Zm32-32H200V88a16,16,0,0,0-16-16H72V56H216Z"/></svg>',
    'check': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/></svg>',
    'arrow': '<svg class="arrow" viewBox="0 0 48 14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M2.2,7H43.8M40.8,2.5L45.8,7M40.8,11.5L45.8,7"/></svg>',
}

# The simulation presets for the hero compressor console
PRESETS = [
    {
        'id': 'kb20',
        'targetKb': 20,
        'label': '20 KB',
        'key': 'preset_20kb',
        'chipKey': 'chip_visa',
        'actualKb': 19.4,
        'dimensions': '720 × 540 px',
        'ratio': '4:3',
        'reduction': '-99.4%',
        'autoDownscale': True,
        'format': 'JPEG',
    },
    {
        'id': 'kb50',
        'targetKb': 50,
        'label': '50 KB',
        'key': 'preset_50kb',
        'chipKey': 'chip_exam',
        'actualKb': 48.7,
        'dimensions': '1024 × 768 px',
        'ratio': '4:3',
        'reduction': '-98.6%',
        'autoDownscale': True,
        'format': 'JPEG',
    },
    {
        'id': 'kb100',
        'targetKb': 100,
        'label': '100 KB',
        'key': 'preset_100kb',
        'chipKey': 'chip_portal',
        'actualKb': 96.5,
        'dimensions': '1600 × 1200 px',
        'ratio': '4:3',
        'reduction': '-97.3%',
        'autoDownscale': True,
        'format': 'JPEG',
    },
    {
        'id': 'kb200',
        'targetKb': 200,
        'label': '200 KB',
        'key': 'preset_200kb',
        'chipKey': 'chip_web',
        'actualKb': 192.0,
        'dimensions': '2048 × 1536 px',
        'ratio': '4:3',
        'reduction': '-94.6%',
        'autoDownscale': False,
        'format': 'JPEG',
    },
    {
        'id': 'orig',
        'targetKb': 0,
        'label': '3.5 MB',
        'key': 'preset_orig',
        'chipKey': 'chip_orig',
        'actualKb': 3584.0,
        'dimensions': '4096 × 3072 px',
        'ratio': '4:3',
        'reduction': 'Original',
        'autoDownscale': False,
        'format': 'JPEG',
    },
]


def presets_html(text):
    """Render the preset buttons for Pipit's hero console."""
    buttons = []
    for i, p in enumerate(PRESETS):
        name = p['label']
        checked = ' checked' if i == 1 else ''   # default to 50 KB
        buttons.append(f'''          <label class="preset-btn">
            <input type="radio" name="pipit_preset" value="{p['id']}"{checked}>
            <span>{name}</span>
          </label>''')
    return '\n'.join(buttons)


def presets_json(text):
    """Serialize the preset scenarios for client-side JS."""
    data = []
    for p in PRESETS:
        item = dict(p)
        item['chipText'] = text[p['chipKey']]
        item['note'] = text[f"{p['id']}_note"]
        data.append(item)
    return json.dumps(data, ensure_ascii=False)
