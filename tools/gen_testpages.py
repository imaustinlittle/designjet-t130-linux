"""Generate PDF test pages for capturing and checking T130 print jobs.

Usage: python3 gen_testpages.py OUTPUT_DIR

Pages use a single Flate filter per stream. Stacked filters (ASCII85 + Flate,
reportlab's default) make newer cups-filters pdftopdf emit blank pages.
"""
import sys, os
import reportlab.rl_config
reportlab.rl_config.useA85 = 0
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
POSTER = (24 * inch, 36 * inch)

def label(c, w, h, text):
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(0.5 * inch, h - 0.5 * inch, text)

def blank(path, size):
    c = canvas.Canvas(path, pagesize=size)
    c.showPage(); c.save()

def square(path, size):
    # One 1in black square, 1in from top-left. Locates origin and margins.
    w, h = size
    c = canvas.Canvas(path, pagesize=size)
    c.setFillColorRGB(0, 0, 0)
    c.rect(1 * inch, h - 2 * inch, 1 * inch, 1 * inch, stroke=0, fill=1)
    c.showPage(); c.save()

def patches(path, size, title):
    w, h = size
    c = canvas.Canvas(path, pagesize=size)
    label(c, w, h, title)
    colors = [
        ("black", (0, 0, 0)), ("gray50", (.5, .5, .5)), ("white", (1, 1, 1)),
        ("cyan", (0, 1, 1)), ("magenta", (1, 0, 1)), ("yellow", (1, 1, 0)),
        ("red", (1, 0, 0)), ("green", (0, 1, 0)), ("blue", (0, 0, 1)),
    ]
    cols, rows = 3, 3
    margin = 0.75 * inch
    pw = (w - 2 * margin) / cols
    ph = (h - 2 * margin - 0.5 * inch) / rows
    for i, (name, rgb) in enumerate(colors):
        cx = margin + (i % cols) * pw
        cy = h - margin - 0.5 * inch - (i // cols + 1) * ph
        c.setFillColorRGB(*rgb)
        c.setStrokeColorRGB(0, 0, 0)
        c.rect(cx + 6, cy + 6, pw - 12, ph - 12, stroke=1, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        c.drawString(cx + 10, cy + 10, name)
    c.showPage(); c.save()

def gradients(path, size):
    w, h = size
    c = canvas.Canvas(path, pagesize=size)
    label(c, w, h, "T130 test: 16-step ramps (gray, R, G, B)")
    margin = 0.75 * inch
    steps = 16
    sw = (w - 2 * margin) / steps
    bh = 1.25 * inch
    ramps = [lambda v: (v, v, v), lambda v: (v, 0, 0), lambda v: (0, v, 0), lambda v: (0, 0, v)]
    for r, f in enumerate(ramps):
        y = h - 1.5 * inch - (r + 1) * (bh + 0.4 * inch)
        for s in range(steps):
            v = s / (steps - 1)
            c.setFillColorRGB(*f(v))
            c.rect(margin + s * sw, y, sw, bh, stroke=0, fill=1)
    c.showPage(); c.save()

def lines(path, size):
    w, h = size
    c = canvas.Canvas(path, pagesize=size)
    label(c, w, h, "T130 test: line weights 0.1/0.25/0.5/1/2 pt, plus text")
    c.setStrokeColorRGB(0, 0, 0)
    margin = 0.75 * inch
    for i, lw in enumerate([0.1, 0.25, 0.5, 1, 2]):
        y = h - 1.5 * inch - i * 0.5 * inch
        c.setLineWidth(lw)
        c.line(margin, y, w - margin, y)
    c.setLineWidth(0.25)
    top = h - 4.5 * inch
    for x in range(0, int(w - 2 * margin) + 1, int(0.25 * inch)):
        c.line(margin + x, margin, margin + x, top)
    for y in range(int(margin), int(top) + 1, int(0.25 * inch)):
        c.line(margin, y, w - margin, y)
    c.setFont("Helvetica", 6)
    c.drawString(margin, top + 10, "The quick brown fox jumps over the lazy dog 0123456789 (6pt)")
    c.showPage(); c.save()

tests = [
    ("01-blank-letter.pdf", lambda p: blank(p, letter)),
    ("02-square-letter.pdf", lambda p: square(p, letter)),
    ("03-patches-letter.pdf", lambda p: patches(p, letter, "T130 test: solid patches, letter")),
    ("04-ramps-letter.pdf", lambda p: gradients(p, letter)),
    ("05-lines-letter.pdf", lambda p: lines(p, letter)),
    ("06-square-24x36.pdf", lambda p: square(p, POSTER)),
    ("07-patches-24x36.pdf", lambda p: patches(p, POSTER, "T130 test: solid patches, 24x36")),
]
for name, fn in tests:
    fn(os.path.join(out, name))
    print(name)
