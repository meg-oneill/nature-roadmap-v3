#!/usr/bin/env python3
"""Extract all text content from index.html into a structured Word document."""

from bs4 import BeautifulSoup, NavigableString, Comment
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

# Read HTML
with open('/home/user/nature-roadmap-v3/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

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
title = doc.add_heading('Nature Positive Roadmap — Full Content Extract', level=0)
doc.add_paragraph('This document contains all text content from the website, organized by section. '
                   'Edit the text below, and the changes will be mapped back to the HTML.\n'
                   'Note: Section markers like [SECTION: ...] are for reference — do not remove them.')
doc.add_paragraph('─' * 60)

def clean_text(text):
    """Clean whitespace from extracted text."""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_section_id(element):
    """Get the id of the nearest parent section or the element itself."""
    if element.get('id'):
        return element['id']
    for parent in element.parents:
        if parent.get('id'):
            return parent['id']
    return None

def extract_text_recursive(element, depth=0):
    """Extract text preserving some structure."""
    texts = []
    for child in element.children:
        if isinstance(child, (Comment, NavigableString)):
            t = clean_text(str(child))
            if t and not t.startswith('<!--'):
                texts.append(t)
        elif child.name in ['script', 'style', 'svg', 'nav', 'img', 'input', 'select', 'button', 'form']:
            # Skip non-content elements, but include button text
            if child.name == 'button':
                t = clean_text(child.get_text())
                if t:
                    texts.append(f'[Button: {t}]')
        elif child.name:
            texts.extend(extract_text_recursive(child, depth + 1))
    return texts

# Process the body content section by section
body = soup.find('body')
if not body:
    print("No body found!")
    exit(1)

# Find all major sections
sections = body.find_all(['section', 'div', 'footer'], recursive=False)
if not sections:
    # Try finding sections at any depth
    sections = body.find_all('section')

# Also look for direct section-like divs
all_sections = []
for child in body.children:
    if isinstance(child, NavigableString):
        continue
    if child.name in ['nav']:
        continue
    all_sections.append(child)

section_count = 0
for section in all_sections:
    if isinstance(section, NavigableString):
        continue
    if not section.name:
        continue

    # Determine section name
    section_id = section.get('id', '')
    section_classes = ' '.join(section.get('class', []))

    # Find the first heading in this section
    heading = section.find(['h1', 'h2', 'h3'])
    heading_text = clean_text(heading.get_text()) if heading else ''

    # Build section label
    label_parts = []
    if section_id:
        label_parts.append(f'id="{section_id}"')
    if section_classes:
        label_parts.append(f'class="{section_classes}"')
    label = ' | '.join(label_parts) if label_parts else f'<{section.name}>'

    # Skip if no meaningful text
    full_text = clean_text(section.get_text())
    if not full_text or len(full_text) < 5:
        continue

    section_count += 1

    # Add section marker
    doc.add_paragraph('')  # spacer
    marker = doc.add_paragraph()
    marker.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = marker.add_run(f'[SECTION {section_count}: {label}]')
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(150, 150, 150)

    if heading_text:
        doc.add_heading(heading_text, level=1)

    # Now walk through all elements in this section and extract content
    for element in section.descendants:
        if isinstance(element, NavigableString):
            continue
        if not element.name:
            continue

        # Only process leaf-level content elements
        if element.name == 'h1':
            t = clean_text(element.get_text())
            if t and t != heading_text:  # Don't duplicate the section heading
                doc.add_heading(t, level=1)
        elif element.name == 'h2':
            t = clean_text(element.get_text())
            if t and t != heading_text:
                doc.add_heading(t, level=2)
        elif element.name == 'h3':
            t = clean_text(element.get_text())
            if t and t != heading_text:
                doc.add_heading(t, level=3)
        elif element.name == 'h4':
            t = clean_text(element.get_text())
            if t:
                doc.add_heading(t, level=4)
        elif element.name == 'p':
            t = clean_text(element.get_text())
            if t:
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
        elif element.name == 'span':
            # Only get spans that have direct text (not just wrapping other elements)
            direct_text = ''.join(
                str(c).strip() for c in element.children if isinstance(c, NavigableString)
            ).strip()
            # Skip spans that just contain numbers or single characters (icons, etc.)
            if direct_text and len(direct_text) > 3:
                # Check if parent is already handled
                if element.parent and element.parent.name not in ['p', 'h1', 'h2', 'h3', 'h4', 'li', 'blockquote', 'cite', 'a']:
                    pass  # Skip to avoid duplication
        elif element.name == 'figcaption':
            t = clean_text(element.get_text())
            if t:
                p = doc.add_paragraph(f'[Caption: {t}]')
                p.runs[0].font.size = Pt(9)
                p.runs[0].font.color.rgb = RGBColor(100, 100, 100)

    doc.add_paragraph('─' * 60)

# Save
output_path = '/home/user/nature-roadmap-v3/Nature_Positive_Roadmap_Content.docx'
doc.save(output_path)
print(f"Done! Saved to {output_path}")
print(f"Extracted {section_count} sections")
