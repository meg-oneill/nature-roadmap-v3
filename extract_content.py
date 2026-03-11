#!/usr/bin/env python3
"""Extract ALL text content from index.html into a structured Word document.
Includes: HTML body content + JavaScript panelData (18 panels) + ACTIONS (30 actions) + roadmap grid."""

from bs4 import BeautifulSoup, NavigableString, Comment
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
import json

# Read HTML
with open('/home/user/nature-roadmap-v3/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── Extract JavaScript data BEFORE parsing with BeautifulSoup ──

# Extract panelData
panel_match = re.search(r'const panelData\s*=\s*\{(.+?)\n\};', html, re.DOTALL)
panel_data = {}
if panel_match:
    raw = panel_match.group(0)
    # Convert JS object to JSON-parseable format
    # Extract each panel entry
    panel_pattern = re.compile(
        r"'([^']+)':\s*\{[^}]*"
        r"principle:\s*'([^']*)'[^}]*"
        r"title:\s*'([^']*)'[^}]*"
        r"time:\s*'([^']*)'[^}]*"
        r"context:\s*'((?:[^'\\]|\\.)*)'[^}]*"
        r"actions:\s*\[(.*?)\][^}]*"
        r"gbca:\s*\[(.*?)\][^}]*"
        r"industry:\s*\[(.*?)\]",
        re.DOTALL
    )
    for m in panel_pattern.finditer(raw):
        pid = m.group(1)
        # Extract list items from array strings
        def extract_items(s):
            return [x.strip().strip("'").strip('"') for x in re.findall(r"'((?:[^'\\]|\\.)*)'", s)]
        panel_data[pid] = {
            'principle': m.group(2),
            'title': m.group(3),
            'time': m.group(4),
            'context': m.group(5).replace("\\'", "'"),
            'actions': extract_items(m.group(6)),
            'gbca': extract_items(m.group(7)),
            'industry': extract_items(m.group(8)),
        }
    print(f"Extracted {len(panel_data)} panels from panelData")

# Extract ACTIONS array
actions_data = []
actions_match = re.search(r'const ACTIONS\s*=\s*\[(.*?)\];', html, re.DOTALL)
if actions_match:
    raw_actions = actions_match.group(1)
    action_pattern = re.compile(
        r"\{\s*id:'([^']*)'[^}]*phase:'([^']*)'[^}]*principle:'([^']*)'[^}]*"
        r"title:'((?:[^'\\]|\\.)*)'[^}]*desc:'((?:[^'\\]|\\.)*)'[^}]*"
        r"deps:\[([^\]]*)\]",
        re.DOTALL
    )
    for m in action_pattern.finditer(raw_actions):
        deps = [d.strip().strip("'") for d in m.group(6).split(',') if d.strip().strip("'")]
        actions_data.append({
            'id': m.group(1),
            'phase': m.group(2),
            'principle': m.group(3),
            'title': m.group(4).replace("\\'", "'"),
            'desc': m.group(5).replace("\\'", "'"),
            'deps': deps,
        })
    print(f"Extracted {len(actions_data)} actions from ACTIONS")

# Extract roadmap grid content
roadmap_grid = []
grid_section = re.search(r'<div class="irm-grid"[^>]*>(.*?)</div>\s*</div>\s*</div>\s*<div class="irm-legend"', html, re.DOTALL)
if grid_section:
    grid_soup = BeautifulSoup(grid_section.group(1), 'html.parser')
    # Extract principles
    for p in grid_soup.find_all('div', class_='irm-principle'):
        roadmap_grid.append(('principle', p.get_text(strip=True)))
    # Extract targets
    for t in grid_soup.find_all('div', class_='irm-target'):
        classes = ' '.join(t.get('class', []))
        onclick = t.get('onclick', '')
        panel_id = ''
        if onclick:
            pm = re.search(r"openPanel\('([^']+)'\)", onclick)
            if pm:
                panel_id = pm.group(1)
        text = t.get_text(strip=True).replace('+', '').strip()
        is_baseline = 'baseline' in classes
        roadmap_grid.append(('target', text, panel_id, is_baseline))
    # Extract action chips
    for chip in grid_soup.find_all('div', class_='irm-action-chip'):
        roadmap_grid.append(('action_chip', chip.get_text(strip=True)))
    # Extract headers
    for h in grid_soup.find_all('div', class_='irm-header'):
        text = h.get_text(strip=True)
        if text:
            roadmap_grid.append(('header', text))
    print(f"Extracted {len(roadmap_grid)} roadmap grid items")

# ── Now parse HTML for body content ──
soup = BeautifulSoup(html, 'html.parser')

# Remove script and style tags
for tag in soup.find_all(['script', 'style', 'svg']):
    tag.decompose()

doc = Document()

# Style setup
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

# Add title
doc.add_heading('Nature Positive Roadmap — Full Content Extract', level=0)
doc.add_paragraph(
    'This document contains ALL text content from the website, organized by section. '
    'This includes visible content, content hidden behind clicks/tabs/accordions, '
    'the interactive roadmap grid, 18 expandable panel details, and 30 action descriptions.\n\n'
    'Edit the text below, and the changes will be mapped back to the HTML.\n'
    'Note: Section markers like [SECTION: ...] are for reference — do not remove them.'
)
doc.add_paragraph('─' * 60)

def clean_text(text):
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def add_grey_marker(doc, text):
    marker = doc.add_paragraph()
    marker.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = marker.add_run(text)
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(150, 150, 150)

# ── Process body content section by section ──
body = soup.find('body')
all_sections = []
for child in body.children:
    if isinstance(child, NavigableString):
        continue
    if child.name in ['nav']:
        continue
    if child.name:
        all_sections.append(child)

section_count = 0
seen_headings = set()

for section in all_sections:
    if isinstance(section, NavigableString) or not section.name:
        continue

    section_id = section.get('id', '')
    section_classes = ' '.join(section.get('class', []))

    heading = section.find(['h1', 'h2', 'h3'])
    heading_text = clean_text(heading.get_text()) if heading else ''

    label_parts = []
    if section_id:
        label_parts.append(f'id="{section_id}"')
    if section_classes:
        label_parts.append(f'class="{section_classes}"')
    label = ' | '.join(label_parts) if label_parts else f'<{section.name}>'

    full_text = clean_text(section.get_text())
    if not full_text or len(full_text) < 5:
        continue

    section_count += 1

    doc.add_paragraph('')
    add_grey_marker(doc, f'[SECTION {section_count}: {label}]')

    if heading_text:
        doc.add_heading(heading_text, level=1)
        seen_headings.add(heading_text)

    for element in section.descendants:
        if isinstance(element, NavigableString) or not element.name:
            continue

        if element.name == 'h1':
            t = clean_text(element.get_text())
            if t and t not in seen_headings:
                doc.add_heading(t, level=1)
                seen_headings.add(t)
        elif element.name == 'h2':
            t = clean_text(element.get_text())
            if t and t not in seen_headings:
                doc.add_heading(t, level=2)
                seen_headings.add(t)
        elif element.name == 'h3':
            t = clean_text(element.get_text())
            if t and t not in seen_headings:
                doc.add_heading(t, level=3)
                seen_headings.add(t)
        elif element.name == 'h4':
            t = clean_text(element.get_text())
            if t:
                doc.add_heading(t, level=4)
        elif element.name == 'p':
            t = clean_text(element.get_text())
            if t and len(t) > 2:
                doc.add_paragraph(t)
        elif element.name == 'li':
            t = clean_text(element.get_text())
            if t:
                doc.add_paragraph(t, style='List Bullet')
        elif element.name == 'blockquote':
            t = clean_text(element.get_text())
            if t:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(f'"{t}"')
                run.italic = True
        elif element.name == 'cite':
            t = clean_text(element.get_text())
            if t:
                p = doc.add_paragraph(f'— {t}')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif element.name == 'figcaption':
            t = clean_text(element.get_text())
            if t:
                p = doc.add_paragraph(f'[Caption: {t}]')
                p.runs[0].font.size = Pt(9)
                p.runs[0].font.color.rgb = RGBColor(100, 100, 100)
        elif element.name == 'div':
            # Capture roadmap grid content: irm-target, irm-action-chip, irm-principle, irm-header
            classes = element.get('class', [])
            if 'irm-target' in classes:
                t = clean_text(element.get_text()).replace('+', '').strip()
                if t:
                    is_baseline = 't-baseline' in classes
                    prefix = '[Baseline] ' if is_baseline else '[Target] '
                    doc.add_paragraph(prefix + t, style='List Bullet')
            elif 'irm-action-chip' in classes:
                t = clean_text(element.get_text())
                if t:
                    doc.add_paragraph(f'[Action] {t}', style='List Bullet')
            elif 'irm-principle' in classes:
                t = clean_text(element.get_text())
                if t:
                    doc.add_heading(t, level=3)
            elif 'irm-header' in classes:
                t = clean_text(element.get_text())
                if t and len(t) > 1:
                    doc.add_paragraph(f'[Grid Header] {t}')
            elif 'irm-enabler-row' in classes:
                t = clean_text(element.get_text())
                if t:
                    doc.add_paragraph(t)
            elif 'mini-rm-card' in classes:
                t = clean_text(element.get_text())
                if t:
                    doc.add_paragraph(f'  {t}', style='List Bullet')

    doc.add_paragraph('─' * 60)

# ══════════════════════════════════════════════════════════════
# PART 2: INTERACTIVE ROADMAP PANEL DATA (hidden behind clicks)
# ══════════════════════════════════════════════════════════════
doc.add_paragraph('')
doc.add_paragraph('')
doc.add_heading('INTERACTIVE ROADMAP — Expandable Panel Details', level=1)
doc.add_paragraph(
    'The following content appears when users click the "+" buttons on roadmap targets. '
    'Each panel contains context, required actions, what GBCA is doing, and what industry needs to do.'
)
doc.add_paragraph('─' * 60)

# Group panels by principle
principle_order = [
    ('Principle 1: Prevent Nature Loss', ['p1-measure', 'p1-nonetloss', 'p1-noloss']),
    ('Principle 2: Increase & Connect Nature', ['p2-measure', 'p2-bng', 'p2-additional']),
    ('Principle 3: Drive Circularity', ['p3-sector-measure', 'p3-sector-7', 'p3-sector-15', 'p3-sector-future',
                                         'p3-proj-measure', 'p3-proj-10', 'p3-proj-20', 'p3-proj-future']),
    ('Principle 4: Choose Low-Impact Materials', ['p4-measure', 'p4-implement', 'p4-bng', 'p4-eliminate']),
    ('Principle 5: Invest in Nature', ['p5-measure', 'p5-invest', 'p5-commonplace']),
]

for principle_name, panel_ids in principle_order:
    doc.add_heading(principle_name, level=2)

    for pid in panel_ids:
        if pid not in panel_data:
            continue
        p = panel_data[pid]

        doc.add_paragraph('')
        add_grey_marker(doc, f'[PANEL: {pid}]')
        doc.add_heading(p['title'], level=3)
        doc.add_paragraph(f"({p['time']})")

        doc.add_heading('Context', level=4)
        doc.add_paragraph(p['context'])

        doc.add_heading('Actions Needed in the Next Five Years', level=4)
        for item in p['actions']:
            doc.add_paragraph(item, style='List Bullet')

        doc.add_heading('What GBCA Is Doing', level=4)
        for item in p['gbca']:
            doc.add_paragraph(item, style='List Bullet')

        doc.add_heading('What Industry Needs to Do', level=4)
        for item in p['industry']:
            doc.add_paragraph(item, style='List Bullet')

        doc.add_paragraph('─' * 40)

# ══════════════════════════════════════════════════════════════
# PART 3: ACTION NETWORK (30 actions shown on hover)
# ══════════════════════════════════════════════════════════════
doc.add_paragraph('')
doc.add_paragraph('')
doc.add_heading('ACTION NETWORK — 30 Actions (shown on hover)', level=1)
doc.add_paragraph(
    'The following 30 actions appear in the interactive action network diagram. '
    'Each action has a title, description, phase, principle, and dependencies.'
)
doc.add_paragraph('─' * 60)

# Group by principle
principle_map = {
    'prevent': 'Principle 1: Prevent Nature Loss',
    'increase': 'Principle 2: Increase & Connect Nature',
    'circular': 'Principle 3: Drive Circularity',
    'materials': 'Principle 4: Choose Low-Impact Materials',
    'invest': 'Principle 5: Invest in Nature',
}
phase_map = {
    'define': 'Define',
    'advocate': 'Advocate',
    'implement': 'Implement',
}

# Build lookup for dependency names
action_lookup = {a['id']: a['title'] for a in actions_data}

for principle_id, principle_label in principle_map.items():
    principle_actions = [a for a in actions_data if a['principle'] == principle_id]
    if not principle_actions:
        continue

    doc.add_heading(principle_label, level=2)

    for a in principle_actions:
        doc.add_paragraph('')
        add_grey_marker(doc, f'[ACTION: {a["id"]}]')

        # Action title with phase
        doc.add_heading(f'{a["id"].upper()}: {a["title"]}', level=3)
        doc.add_paragraph(f'Phase: {phase_map.get(a["phase"], a["phase"])}')
        doc.add_paragraph(a['desc'])

        if a['deps']:
            dep_names = [f'{d} ({action_lookup.get(d, "?")})' for d in a['deps']]
            doc.add_paragraph(f'Depends on: {", ".join(dep_names)}')

doc.add_paragraph('─' * 60)

# Save
output_path = '/home/user/nature-roadmap-v3/Nature_Positive_Roadmap_Content.docx'
doc.save(output_path)
print(f"\nDone! Saved to {output_path}")
print(f"Sections from HTML: {section_count}")
print(f"Panels from JS: {len(panel_data)}")
print(f"Actions from JS: {len(actions_data)}")
