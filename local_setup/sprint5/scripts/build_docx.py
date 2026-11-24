import re
import sys
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = sys.argv[1]
DST = sys.argv[2]

TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*]+?\*)")


def add_inline(paragraph, text):
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        else:
            paragraph.add_run(part)


def is_table_sep(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


with open(SRC, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    if not stripped:
        i += 1
        continue

    if stripped == "---":
        i += 1
        continue

    if stripped.startswith("|") and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
        header = split_row(stripped)
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append(split_row(lines[i]))
            i += 1
        table = doc.add_table(rows=1, cols=len(header))
        table.style = "Light Grid Accent 1"
        for j, h in enumerate(header):
            cell = table.rows[0].cells[j]
            cell.text = ""
            add_inline(cell.paragraphs[0], h)
            for run in cell.paragraphs[0].runs:
                run.bold = True
        for row in rows:
            cells = table.add_row().cells
            for j, val in enumerate(row[: len(header)]):
                cells[j].text = ""
                add_inline(cells[j].paragraphs[0], val)
        doc.add_paragraph()
        continue

    if stripped.startswith("### "):
        p = doc.add_heading(level=2)
        add_inline(p, stripped[4:])
        i += 1
        continue

    if stripped.startswith("## "):
        p = doc.add_heading(level=1)
        add_inline(p, stripped[3:])
        i += 1
        continue

    if stripped.startswith("# "):
        p = doc.add_heading(level=0)
        add_inline(p, stripped[2:])
        i += 1
        continue

    if stripped.startswith("> "):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(18)
        run = p.add_run(stripped[2:])
        run.italic = True
        run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
        i += 1
        continue

    m = re.match(r"^(\s*)([-*])\s+(.*)$", line)
    if m:
        indent, _, text = m.groups()
        style = "List Bullet 2" if len(indent) >= 2 else "List Bullet"
        p = doc.add_paragraph(style=style)
        add_inline(p, text)
        i += 1
        continue

    m = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
    if m:
        indent, _, text = m.groups()
        style = "List Number 2" if len(indent) >= 2 else "List Number"
        p = doc.add_paragraph(style=style)
        add_inline(p, text)
        i += 1
        continue

    p = doc.add_paragraph()
    add_inline(p, stripped)
    i += 1

doc.save(DST)
print("saved", DST)
