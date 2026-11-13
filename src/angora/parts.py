"""Helpers for Angora's page: duplicate groups simulation, storage breakdown, and icons."""
import json

ICONS = {
    'files': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M216,40H72A16,16,0,0,0,56,56V72H40A16,16,0,0,0,24,88V200a16,16,0,0,0,16,16H184a16,16,0,0,0,16-16V184h16a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM184,200H40V88H184Zm32-32H200V88a16,16,0,0,0-16-16H72V56H216Z"/></svg>',
    'shield': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M208,40H48A16,16,0,0,0,32,56v58.78c0,89.61,75.82,119.34,91,124.39a15.54,15.54,0,0,0,10,0c15.18-5.05,91-34.78,91-124.39V56A16,16,0,0,0,208,40Zm0,74.78c0,76.68-63.09,103.84-80,110.12C111.09,218.62,48,191.46,48,114.78V56H208Z"/></svg>',
    'check': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/></svg>',
    'trash': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M216,48H176V40a24,24,0,0,0-24-24H104A24,24,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40a8,8,0,0,1,8-8h48a8,8,0,0,1,8,8v8H96Zm96,168H64V64H192ZM112,104v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Z"/></svg>',
    'storage': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M224,48H32A16,16,0,0,0,16,64V96a16,16,0,0,0,16,16V192a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V112a16,16,0,0,0,16-16V64A16,16,0,0,0,224,48ZM32,64H224V96H32Zm176,128H48V112H208v80Zm-32-40a12,12,0,1,1,12-12A12,12,0,0,1,176,152Z"/></svg>',
    'spark': '<svg class="ic" viewBox="0 0 256 256" aria-hidden="true"><path fill="currentColor" d="M213.66,82.34l-56-56a8,8,0,0,0-11.32,0l-56,56a8,8,0,0,0,0,11.32l56,56a8,8,0,0,0,11.32,0l56-56A8,8,0,0,0,213.66,82.34ZM152,124.69,107.31,80,152,35.31,196.69,80Zm-69.66,77-24-24a8,8,0,0,0-11.32,0l-24,24a8,8,0,0,0,0,11.32l24,24a8,8,0,0,0,11.32,0l24-24A8,8,0,0,0,82.34,201.66ZM47,208l13-13,13,13-13,13Z"/></svg>',
}

GROUPS = [
    {
        'id': 'grp1',
        'file': 'VID_20250705_172210.mp4',
        'type': 'video',
        'sizeMb': 209.4,
        'tagKey': 'grp1_tag',
        'copies': [
            {'path': '/DCIM/Camera/VID_20250705_172210.mp4', 'date': '2025/07/05', 'action': 'keep', 'defaultRemove': False},
            {'path': '/Download/VID_20250705_172210.mp4', 'date': '2025/07/06', 'action': 'remove', 'defaultRemove': True},
        ],
        'reclaimMb': 209.4,
    },
    {
        'id': 'grp2',
        'file': 'IMG_20260812_0945_RAW.dng',
        'type': 'photo',
        'sizeMb': 49.4,
        'tagKey': 'grp2_tag',
        'copies': [
            {'path': '/DCIM/Camera/IMG_20260812_0945_RAW.dng', 'date': '2026/08/12', 'action': 'keep', 'defaultRemove': False},
            {'path': '/Pictures/WhatsApp/IMG_20260812_0945_RAW.dng', 'date': '2026/08/12', 'action': 'remove', 'defaultRemove': True},
        ],
        'reclaimMb': 49.4,
    },
    {
        'id': 'grp3',
        'file': 'Q3_Financial_Audit_Report.pdf',
        'type': 'doc',
        'sizeMb': 28.6,
        'tagKey': 'grp3_tag',
        'copies': [
            {'path': '/Documents/Q3_Financial_Audit_Report.pdf', 'date': '2026/09/01', 'action': 'keep', 'defaultRemove': False},
            {'path': '/Download/Telegram/Q3_Financial_Audit_Report(1).pdf', 'date': '2026/09/02', 'action': 'remove', 'defaultRemove': True},
        ],
        'reclaimMb': 28.6,
    },
]


def groups_html(text):
    """Render the 3 interactive duplicate file groups."""
    cards = []
    for g in GROUPS:
        tag = text[g['tagKey']]
        rows = []
        for i, c in enumerate(g['copies']):
            checked = ' checked' if c['defaultRemove'] else ''
            badge = text['badge_remove'] if c['defaultRemove'] else text['badge_keep']
            badge_class = 'badge-remove' if c['defaultRemove'] else 'badge-keep'
            rows.append(f'''            <li class="dup-copy-row">
              <label class="dup-row-label">
                <input type="checkbox" class="dup-check" data-group="{g['id']}" data-mb="{g['sizeMb']}"{checked}>
                <span class="dup-path">{c['path']}</span>
              </label>
              <div class="dup-meta">
                <span class="dup-date">{c['date']}</span>
                <span class="dup-badge {badge_class}">{badge}</span>
              </div>
            </li>''')
        rows_str = '\n'.join(rows)
        cards.append(f'''        <div class="dup-group-card" id="{g['id']}">
          <div class="dup-group-header">
            <div>
              <h4 class="dup-file-name">{g['file']}</h4>
              <span class="dup-reason">{text['verified_reason']} · {g['sizeMb']} MB</span>
            </div>
            <span class="dup-tag">{tag}</span>
          </div>
          <ul class="dup-copies-list">
{rows_str}
          </ul>
        </div>''')
    return '\n'.join(cards)


def groups_json(text):
    """JSON serialization for client-side live calculator."""
    data = []
    for g in GROUPS:
        item = dict(g)
        item['tag'] = text[g['tagKey']]
        data.append(item)
    return json.dumps(data, ensure_ascii=False)
