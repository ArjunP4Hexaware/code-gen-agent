"""Build the ACFC overview deck for this agent (PPTX).

    pip install python-pptx
    python scripts/build_acfc_deck.py [output.pptx]

Self-contained: shared slide helpers (deck_lib) + this agent's content in one file so the
deck can be regenerated without cross-repo dependencies. Layout is absolute-positioned;
text length drives fit — shorten copy rather than growing boxes.
"""
# ---------------------------------------------------------------------------
# deck_lib — shared slide-building helpers (python-pptx, absolute layout, 16:9)
# Every deck in the AI-in-Engineering program uses this same visual system so
# the five agent decks read as one family. Copy is short by design: layout is
# absolute-positioned, so text length drives fit. Shorten copy, don't grow boxes.
# ---------------------------------------------------------------------------
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ------------------------------------------------------------------ palette
NAVY = RGBColor(0x0E, 0x22, 0x33)
NAVY_L = RGBColor(0x1B, 0x3A, 0x52)
INK = RGBColor(0x1A, 0x24, 0x33)
BODY = RGBColor(0x3A, 0x4A, 0x5C)
MUTED = RGBColor(0x6B, 0x7A, 0x8C)
TEAL = RGBColor(0x00, 0xA1, 0x9A)
TEAL_D = RGBColor(0x00, 0x7C, 0x76)
BLUE = RGBColor(0x2E, 0x6E, 0xD1)
AMBER = RGBColor(0xD9, 0x8A, 0x1F)
RED = RGBColor(0xC2, 0x3B, 0x3B)
GREEN = RGBColor(0x1E, 0x7A, 0x46)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAPER = RGBColor(0xF4, 0xF7, 0xF9)
LINE = RGBColor(0xD8, 0xE0, 0xE7)
PALE = RGBColor(0xC3, 0xD2, 0xDE)
TEAL_BG = RGBColor(0xE3, 0xF5, 0xF4)
BLUE_BG = RGBColor(0xE6, 0xEF, 0xFB)
AMBER_BG = RGBColor(0xFB, 0xF1, 0xE1)
GREY_BG = RGBColor(0xEE, 0xF1, 0xF4)

KIND_COLOR = {  # pipeline step kinds
    "llm": (BLUE, BLUE_BG, "LLM step (Claude)"),
    "code": (TEAL_D, TEAL_BG, "Deterministic code"),
    "human": (AMBER, AMBER_BG, "Human decision"),
    "data": (MUTED, GREY_BG, "Artifact / data"),
}

FONT = "Calibri"
FONT_H = "Calibri Light"

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.7)
CONTENT_W = W - 2 * MARGIN
TOP = Inches(1.45)  # content starts below title band
BOTTOM = Inches(6.75)  # content must stay above footer band


class Deck:
    def __init__(self, agent_label, program_label="Hexaware × ACFC · AI-in-Engineering"):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.agent_label = agent_label
        self.program_label = program_label
        self.n = 0

    # ------------------------------------------------------------ primitives
    def slide(self, dark=False):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        if dark:
            rect(s, 0, 0, W, H, fill=NAVY)
        return s

    def save(self, path):
        self.prs.save(path)

    def footer(self, s, dark=False):
        col = PALE if dark else MUTED
        line_col = NAVY_L if dark else LINE
        rect(s, MARGIN, Inches(6.98), CONTENT_W, Pt(0.75), fill=line_col)
        text(s, MARGIN, Inches(7.02), Inches(8), Inches(0.35),
             f"{self.program_label}  ·  {self.agent_label}", size=10, color=col)
        text(s, W - MARGIN - Inches(1.5), Inches(7.02), Inches(1.5), Inches(0.35),
             str(self.n), size=10, color=col, align=PP_ALIGN.RIGHT)

    def title(self, s, title_txt, kicker=None, dark=False):
        col = WHITE if dark else INK
        kcol = TEAL if dark else TEAL_D
        y = Inches(0.42)
        if kicker:
            text(s, MARGIN, y, CONTENT_W, Inches(0.3), kicker.upper(), size=11,
                 color=kcol, bold=True, font=FONT, spacing=True)
            y = Inches(0.68)
        text(s, MARGIN, y, CONTENT_W, Inches(0.7), title_txt, size=28,
             color=col, bold=True, font=FONT_H)
        rect(s, MARGIN, Inches(1.32), Inches(1.1), Pt(3), fill=TEAL)

    def notes(self, s, txt):
        s.notes_slide.notes_text_frame.text = txt

    # ------------------------------------------------------------ slide types
    def cover(self, title_txt, subtitle, meta_lines, notes=None):
        s = self.slide(dark=True)
        rect(s, 0, 0, Inches(0.35), H, fill=TEAL)
        text(s, Inches(1.0), Inches(0.9), Inches(10), Inches(0.4),
             self.program_label.upper(), size=12, color=TEAL, bold=True, spacing=True)
        text(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(1.9), title_txt, size=44,
             color=WHITE, bold=True, font=FONT_H)
        text(s, Inches(1.0), Inches(4.0), Inches(11), Inches(1.0), subtitle, size=20,
             color=PALE, font=FONT_H)
        y = Inches(5.5)
        for ln in meta_lines:
            text(s, Inches(1.0), y, Inches(11), Inches(0.35), ln, size=13, color=PALE)
            y += Inches(0.36)
        if notes:
            self.notes(s, notes)
        return s

    def statement(self, kicker, big, small=None, notes=None):
        """One big idea per slide."""
        s = self.slide()
        self.title(s, kicker)
        text(s, MARGIN, Inches(1.7), CONTENT_W, Inches(2.8), big, size=26, color=NAVY,
             bold=True, font=FONT_H, anchor=MSO_ANCHOR.MIDDLE)
        if small:
            text(s, MARGIN, Inches(4.75), CONTENT_W, Inches(1.9), small, size=15, color=BODY)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def bullets_slide(self, title_txt, items, kicker=None, notes=None, takeaway=None,
                      size=17):
        s = self.slide()
        self.title(s, title_txt, kicker)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        bullets(s, MARGIN, TOP, CONTENT_W, bottom - TOP, items, size=size)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def two_col(self, title_txt, left_head, left_items, right_head, right_items,
                kicker=None, notes=None, takeaway=None, left_tone="grey",
                right_tone="teal", size=15):
        s = self.slide()
        self.title(s, title_txt, kicker)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        gap = Inches(0.35)
        cw = (CONTENT_W - gap) / 2
        for i, (head, items, tone) in enumerate(
                [(left_head, left_items, left_tone), (right_head, right_items, right_tone)]):
            x = MARGIN + i * (cw + gap)
            panel(s, x, TOP, cw, bottom - TOP, head, items, tone=tone, size=size)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def cards(self, title_txt, items, kicker=None, cols=3, notes=None, takeaway=None,
              body_size=13):
        """items: list of (heading, body[, tone])."""
        s = self.slide()
        self.title(s, title_txt, kicker)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        rows = (len(items) + cols - 1) // cols
        gap = Inches(0.28)
        cw = (CONTENT_W - gap * (cols - 1)) / cols
        ch = (bottom - TOP - gap * (rows - 1)) / rows
        for i, it in enumerate(items):
            head, body = it[0], it[1]
            tone = it[2] if len(it) > 2 else "grey"
            r, c = divmod(i, cols)
            x = MARGIN + c * (cw + gap)
            y = TOP + r * (ch + gap)
            card(s, x, y, cw, ch, head, body, tone=tone, body_size=body_size)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def kpis(self, title_txt, tiles, kicker=None, notes=None, source=None, below=None,
             cols=None, takeaway=None):
        """tiles: list of (big, label, sub). Optional `below` bullets under tiles."""
        s = self.slide()
        self.title(s, title_txt, kicker)
        cols = cols or min(len(tiles), 4)
        rows = (len(tiles) + cols - 1) // cols
        gap = Inches(0.25)
        cw = (CONTENT_W - gap * (cols - 1)) / cols
        th = Inches(1.9)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        for i, (big, label, sub) in enumerate(tiles):
            r, c = divmod(i, cols)
            x = MARGIN + c * (cw + gap)
            y = TOP + r * (th + gap)
            kpi_tile(s, x, y, cw, th, big, label, sub)
        y_after = TOP + rows * (th + gap)
        if below:
            bullets(s, MARGIN, y_after + Inches(0.1), CONTENT_W,
                    bottom - y_after - Inches(0.5), below, size=15)
        if source:
            text(s, MARGIN, bottom - Inches(0.4), CONTENT_W, Inches(0.4),
                 "Source: " + source, size=10, color=MUTED, italic=True)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def flow_slide(self, title_txt, steps, kicker=None, notes=None, below=None,
                   takeaway=None, legend=True, y=None, step_h=None):
        """steps: list of (label, sub, kind). Rendered as a left-to-right flow."""
        s = self.slide()
        self.title(s, title_txt, kicker)
        y = y or (TOP + Inches(0.25))
        step_h = step_h or (Inches(1.8) if len(steps) <= 5 else Inches(2.2))
        flow(s, MARGIN, y, CONTENT_W, step_h, steps)
        yy = y + step_h + Inches(0.15)
        if legend:
            legend_row(s, MARGIN, yy, [k for k in ("llm", "code", "human", "data")
                                       if any(st[2] == k for st in steps)])
            yy += Inches(0.45)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        if below:
            bullets(s, MARGIN, yy + Inches(0.1), CONTENT_W, bottom - yy - Inches(0.1),
                    below, size=14)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def table_slide(self, title_txt, headers, rows, kicker=None, notes=None,
                    col_widths=None, takeaway=None, source=None, size=12,
                    highlight_last=False):
        s = self.slide()
        self.title(s, title_txt, kicker)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        if source:
            bottom -= Inches(0.6)
        table(s, MARGIN, TOP, CONTENT_W, bottom - TOP, headers, rows,
              col_widths=col_widths, size=size, highlight_last=highlight_last)
        if source:
            text(s, MARGIN, bottom + Inches(0.05), CONTENT_W, Inches(0.55),
                 "Source / assumptions: " + source, size=9.5, color=MUTED, italic=True)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def program_map(self, title_txt, highlight, kicker=None, notes=None, below=None,
                    takeaway=None):
        """The five-agent program map with one agent highlighted."""
        s = self.slide()
        self.title(s, title_txt, kicker)
        agents = [
            ("BRD → FRD", "Business requirements →\nfunctional requirements", "brd"),
            ("FRD → STTM", "Functional requirements →\nsource-to-target mapping", "sttm"),
            ("CodeGen", "Mapping contract →\npipeline code + tests", "codegen"),
            ("Code Review", "PR / diff →\nreview findings + gate", "review"),
        ]
        y = TOP + Inches(0.3)
        bh = Inches(1.5)
        gap = Inches(0.55)
        bw = (CONTENT_W - gap * 3) / 4
        for i, (name, sub, key) in enumerate(agents):
            x = MARGIN + i * (bw + gap)
            hi = key == highlight
            box = rect(s, x, y, bw, bh, fill=(TEAL if hi else WHITE),
                       line=(TEAL if hi else PALE), lw=1.5,
                       shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.12)
            text(s, x, y + Inches(0.15), bw, Inches(0.45), name, size=16, bold=True,
                 color=(WHITE if hi else NAVY), align=PP_ALIGN.CENTER)
            text(s, x + Inches(0.1), y + Inches(0.6), bw - Inches(0.2), Inches(0.85), sub,
                 size=11, color=(WHITE if hi else BODY), align=PP_ALIGN.CENTER)
            if i < 3:
                arrow(s, x + bw + Inches(0.08), y + bh / 2, gap - Inches(0.16))
        # sidecar
        sy = y + bh + Inches(0.4)
        hi = highlight == "sql"
        sw = Inches(5.2)
        sx = MARGIN + (CONTENT_W - sw) / 2
        rect(s, sx, sy, sw, Inches(0.95), fill=(TEAL if hi else WHITE),
             line=(TEAL if hi else PALE), lw=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             adj=0.2, dash=(not hi))
        text(s, sx, sy + Inches(0.08), sw, Inches(0.4), "SQL Optimization (standalone)",
             size=15, bold=True, color=(WHITE if hi else NAVY), align=PP_ALIGN.CENTER)
        text(s, sx, sy + Inches(0.48), sw, Inches(0.4),
             "Reads warehouse query telemetry, returns a ranked optimization backlog",
             size=11, color=(WHITE if hi else BODY), align=PP_ALIGN.CENTER)
        text(s, MARGIN, sy + Inches(1.05), CONTENT_W, Inches(0.35),
             "Human approval gate between every stage · shared hub + append-only ledger "
             "(agent-pipeline-orchestrator)", size=11, color=MUTED, align=PP_ALIGN.CENTER,
             italic=True)
        yy = sy + Inches(1.5)
        bottom = BOTTOM - (Inches(0.85) if takeaway else 0)
        if below:
            bullets(s, MARGIN, yy, CONTENT_W, bottom - yy, below, size=14)
        if takeaway:
            takeaway_bar(s, takeaway)
        self.footer(s)
        if notes:
            self.notes(s, notes)
        return s

    def closing(self, title_txt, lines, notes=None):
        s = self.slide(dark=True)
        rect(s, 0, 0, Inches(0.35), H, fill=TEAL)
        text(s, Inches(1.0), Inches(1.2), Inches(11), Inches(1.0), title_txt, size=36,
             color=WHITE, bold=True, font=FONT_H)
        bullets(s, Inches(1.0), Inches(2.5), Inches(11.3), Inches(4.0), lines, size=18,
                color=PALE, bullet_color=TEAL)
        self.footer(s, dark=True)
        if notes:
            self.notes(s, notes)
        return s


# ------------------------------------------------------------------ helpers
def rect(s, x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE,
         adj=None, dash=False):
    sh = s.shapes.add_shape(shape, int(x), int(y), int(w), int(h))
    if adj is not None and sh.adjustments:
        sh.adjustments[0] = adj
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
        if dash:
            from pptx.enum.dml import MSO_LINE
            sh.line.dash_style = MSO_LINE.DASH
    sh.shadow.inherit = False
    return sh


def text(s, x, y, w, h, txt, size=14, color=INK, bold=False, italic=False, font=FONT,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=False, wrap=True):
    tb = s.shapes.add_textbox(int(x), int(y), int(w), int(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    lines = txt.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        f = r.font
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        f.name = font
        f.color.rgb = color
        if spacing:
            rPr = r._r.get_or_add_rPr()
            rPr.set("spc", "150")
    return tb


def bullets(s, x, y, w, h, items, size=15, color=INK, bullet_color=TEAL, sub_color=BODY):
    """items: str | (str, level) | (str, level, {'bold':..,'color':..}). level 0/1."""
    tb = s.shapes.add_textbox(int(x), int(y), int(w), int(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    first = True
    for it in items:
        if isinstance(it, str):
            it = (it, 0)
        txt, level = it[0], it[1]
        opts = it[2] if len(it) > 2 else {}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(8 if level == 0 else 4)
        p.level = 0
        indent = "        " if level else ""
        r0 = p.add_run()
        r0.text = indent + ("▪  " if level == 0 else "–  ")
        r0.font.size = Pt(size if level == 0 else size - 2)
        r0.font.color.rgb = bullet_color if level == 0 else MUTED
        r0.font.name = FONT
        r0.font.bold = True
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(opts.get("size", size if level == 0 else size - 2))
        r.font.bold = opts.get("bold", False)
        r.font.italic = opts.get("italic", False)
        r.font.name = FONT
        r.font.color.rgb = opts.get("color", color if level == 0 else sub_color)
    return tb


TONES = {
    "grey": (GREY_BG, MUTED, NAVY),
    "teal": (TEAL_BG, TEAL, TEAL_D),
    "blue": (BLUE_BG, BLUE, BLUE),
    "amber": (AMBER_BG, AMBER, AMBER),
    "navy": (NAVY, TEAL, WHITE),
    "white": (WHITE, LINE, NAVY),
}


def card(s, x, y, w, h, head, body, tone="grey", body_size=13):
    bg, accent, headcol = TONES[tone]
    rect(s, x, y, w, h, fill=bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.06)
    rect(s, x, y, Pt(4), h, fill=accent)
    pad = Inches(0.22)
    text(s, x + pad, y + Inches(0.15), w - 2 * pad, Inches(0.55), head, size=15,
         bold=True, color=headcol)
    body_col = PALE if tone == "navy" else BODY
    if isinstance(body, (list, tuple)):
        bullets(s, x + pad, y + Inches(0.7), w - 2 * pad, h - Inches(0.8), body,
                size=body_size, color=body_col, sub_color=body_col,
                bullet_color=accent)
    else:
        text(s, x + pad, y + Inches(0.7), w - 2 * pad, h - Inches(0.8), body,
             size=body_size, color=body_col)


def panel(s, x, y, w, h, head, items, tone="grey", size=15):
    bg, accent, headcol = TONES[tone]
    rect(s, x, y, w, h, fill=bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.04)
    rect(s, x, y, w, Inches(0.6), fill=accent, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         adj=0.25)
    rect(s, x, y + Inches(0.3), w, Inches(0.3), fill=accent)  # square off bottom
    text(s, x + Inches(0.25), y + Inches(0.12), w - Inches(0.5), Inches(0.4), head,
         size=15, bold=True, color=WHITE)
    bullets(s, x + Inches(0.25), y + Inches(0.8), w - Inches(0.5), h - Inches(0.95),
            items, size=size, bullet_color=accent)


def kpi_tile(s, x, y, w, h, big, label, sub):
    rect(s, x, y, w, h, fill=WHITE, line=LINE, lw=1, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         adj=0.08)
    rect(s, x, y + h - Pt(4), w, Pt(4), fill=TEAL)
    big_size = 32 if len(big) <= 8 else (26 if len(big) <= 11 else 21)
    text(s, x + Inches(0.2), y + Inches(0.15), w - Inches(0.4), Inches(0.75), big, size=big_size,
         bold=True, color=NAVY, font=FONT_H, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.2), y + Inches(0.9), w - Inches(0.4), Inches(0.35), label, size=13,
         bold=True, color=TEAL_D)
    text(s, x + Inches(0.2), y + Inches(1.22), w - Inches(0.4), Inches(0.5), sub, size=10.5,
         color=MUTED)


def arrow(s, x, y_center, length):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, int(x), int(y_center - Inches(0.11)),
                           int(length), int(Inches(0.22)))
    a.fill.solid()
    a.fill.fore_color.rgb = PALE
    a.line.fill.background()
    a.shadow.inherit = False
    return a


def flow(s, x, y, w, h, steps):
    n = len(steps)
    gap = Inches(0.32) if n <= 5 else Inches(0.26)
    bw = (w - gap * (n - 1)) / n
    sub_size = 10.5 if n <= 5 else 10
    for i, (label, sub, kind) in enumerate(steps):
        accent, bg, _ = KIND_COLOR[kind]
        bx = x + i * (bw + gap)
        rect(s, bx, y, bw, h, fill=bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.1)
        rect(s, bx, y, bw, Pt(5), fill=accent)
        text(s, bx, y + Inches(0.15), bw, Inches(0.3), f"{i + 1}", size=11, bold=True,
             color=accent, align=PP_ALIGN.CENTER)
        text(s, bx + Inches(0.08), y + Inches(0.42), bw - Inches(0.16), Inches(0.5), label,
             size=13, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        text(s, bx + Inches(0.1), y + Inches(0.9), bw - Inches(0.2), h - Inches(0.95), sub,
             size=sub_size, color=BODY, align=PP_ALIGN.CENTER)
        if i < n - 1:
            arrow(s, bx + bw + Inches(0.04), y + h / 2, gap - Inches(0.08))


def legend_row(s, x, y, kinds):
    cx = x
    for k in kinds:
        accent, bg, label = KIND_COLOR[k]
        rect(s, cx, y + Inches(0.08), Inches(0.22), Inches(0.22), fill=accent,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)
        text(s, cx + Inches(0.3), y + Inches(0.03), Inches(2.4), Inches(0.35), label,
             size=11, color=BODY)
        cx += Inches(2.6)


def takeaway_bar(s, txt):
    y = BOTTOM - Inches(0.7)
    rect(s, MARGIN, y, CONTENT_W, Inches(0.7), fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         adj=0.2)
    rect(s, MARGIN + Inches(0.25), y + Inches(0.2), Pt(4), Inches(0.3), fill=TEAL)
    text(s, MARGIN + Inches(0.45), y, CONTENT_W - Inches(0.7), Inches(0.7), txt, size=14,
         color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def table(s, x, y, w, h, headers, rows, col_widths=None, size=12, highlight_last=False):
    nrows, ncols = len(rows) + 1, len(headers)
    shp = s.shapes.add_table(nrows, ncols, int(x), int(y), int(w),
                             int(min(h, Inches(0.62) * nrows)))
    tbl = shp.table
    if col_widths:
        tot = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = int(w * cw / tot)
    row_h = int(min(h / nrows, Inches(0.62)))
    for r in range(nrows):
        tbl.rows[r].height = row_h

    def _cell(c, txt, bold=False, color=INK, fill=None, sz=size, align=PP_ALIGN.LEFT):
        c.text = ""
        tf = c.text_frame
        tf.word_wrap = True
        c.margin_left = c.margin_right = Inches(0.08)
        c.margin_top = c.margin_bottom = Inches(0.04)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        lines = str(txt).split("\n")
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            rr = p.add_run()
            rr.text = ln
            rr.font.size = Pt(sz)
            rr.font.bold = bold
            rr.font.name = FONT
            rr.font.color.rgb = color
        if fill is not None:
            c.fill.solid()
            c.fill.fore_color.rgb = fill

    for ci, hd in enumerate(headers):
        _cell(tbl.cell(0, ci), hd, bold=True, color=WHITE, fill=NAVY, sz=size)
    for ri, row in enumerate(rows, start=1):
        last = highlight_last and ri == nrows - 1
        for ci, val in enumerate(row):
            fill = TEAL_BG if last else (WHITE if ri % 2 else PAPER)
            _cell(tbl.cell(ri, ci), val, bold=(ci == 0 or last),
                  color=(TEAL_D if last else INK), fill=fill)
    # kill the default table style banding look
    tblPr = shp._element.graphic.graphicData.tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "0")
    return shp


# ---------------------------------------------------------------------------
# Content: CodeGen (Data Engineer) Agent — ACFC overview deck
# Facts sourced from README.md, CLAUDE.md, docs/DESIGN.md, docs/WORKFLOW.md, docs/DEMO_RUNBOOK.md,
# docs/LIVE_RUN_RECORD.md, docs/LIVE_PATH_RECON.md, docs/SEGMENTED_MODE_DESIGN.md,
# fixtures/replay/live_e2e_20260807 (repo state 2026-08-10).
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

OUT = (Path(sys.argv[1]) if len(sys.argv) > 1
       else Path(__file__).resolve().parent.parent / "docs" / "code-gen-agent_overview_deck.pptx")

d = Deck("CodeGen Agent")

# 1 ── cover
d.cover(
    "CodeGen — the Data Engineer Agent",
    "From approved FRD + STTM contracts to a production-shaped Databricks ingestion pipeline — "
    "PySpark, Delta DDL, tests, job and notebook — with the AI kept out of production code.",
    ["Prepared for AmeriHealth Caritas Family of Companies (ACFC)",
     "Hexaware · AI-in-Engineering program · Agent 3 of 5 · August 2026",
     "Status: live end-to-end runs on anonymised MIDS / CV fixtures; first real-workspace deployment pending"],
    notes="Opening. What CodeGen does, why ACFC would want it, what has been measured, and an explicitly "
          "labelled illustrative savings model. Fixture feeds are anonymised (Civic Vantage universe) or "
          "synthetic (CAQH STTM) — never present them as ACFC data.")

# 2 ── one sentence
d.statement(
    "What it does — in one sentence",
    "It compiles two approved, machine-readable contracts — the FRD feed contract and the STTM mapping "
    "contract — into a complete bronze-to-silver ingestion pipeline for Databricks, and grades its own "
    "output with a gate before an engineer ever opens a pull request.",
    "Input: <feed>.contract.json (from FRD→STTM) + STTM mapping contract (extracted deterministically from the client's STTM workbook).\n"
    "Output per feed: PySpark + Delta Lake modules, Unity Catalog DDL, a pytest suite, a Databricks Workflows job JSON, "
    "one runnable notebook, a generation report and a PASS / PASS WITH FLAGS / FAIL verdict.\n"
    "Templates write the code. Claude only reviews the leftovers — and never writes production code.",
    notes="'Two-layer trust rule': everything derivable from the contracts is written by Jinja2 templates "
          "(Layer 1). Only free-text validation rules the deterministic classifier cannot map go to Claude "
          "(Layer 2), and its output is a review artifact (candidates.json), never merged into modules.")

# 3 ── problem
d.two_col(
    "Why ACFC needs it",
    "Feed onboarding today",
    ["Every new data feed (MIDS, CAQH, …) needs its own ingestion pipeline: readers, drift checks, mappings, audit columns, rejects, MERGE writer, DQ, tests, job",
     "The work is translation — BRD/FRD + STTM spreadsheet hand-typed into PySpark, Delta DDL and tests",
     "Repetitive and error-prone; each engineer's pipeline looks a little different",
     "Reviewers must reverse-engineer the spreadsheet to check the code",
     "House rules (PHI masking, audit columns, recycle logic) depend on the individual remembering them"],
    "With the CodeGen agent",
    ["Same contracts in, same bytes out — 34–39 files per feed generated in seconds",
     "House style baked into 41 templates: stage-as-String, typed audit columns, drift → fail/quarantine, idempotent MERGE, PHI masked last-4 at every egress",
     "Every emitted file carries a provenance banner with contract names + SHA-256",
     "Reviewers get a report: rule table with grounding, files emitted, gate results, flags",
     "Only genuinely unmapped rules go to Claude — as candidates for an engineer to approve, never as merged code"],
    kicker="The business problem",
    takeaway="Pipeline scaffolding in seconds instead of engineer-days per feed, in one consistent house style — with the engineer still owning every PR.",
    notes="Fixture contexts are real project shapes: MIDS social-determinants feeds (3 flat files, recycle "
          "against Facets subscriber lookup, 7-day window) and CAQH TPL inbound (Header/Detail/Trailer, "
          "15-day recycle). ACFC's engineer-hours per feed are not in the repo — the previous deck's "
          "'engineer-weeks' is unmeasured.")

# 4 ── how it works
d.flow_slide(
    "How it works — templates write the code, the AI reviews the leftovers",
    [("EXTRACT STTM", "Client STTM workbook + FRD contract → mapping contract JSON. Deterministic, no LLM, no network", "code"),
     ("RESOLVE", "FRD ⋈ STTM per feed; any disagreement (delimiter, targets, recycle window) raises — never reconciled silently", "code"),
     ("COMPILE RULES", "Regex classifier: mappable / orchestration / notification / out-of-scope / flagged / unmapped — with grounding substring", "code"),
     ("LAYER-2 REASON", "Only unmapped rules → Claude, with a context pack; citations must be verbatim; output = candidates.json", "llm"),
     ("EMIT + GATE", "41 Jinja2 templates → modules, DDL, tests, job, notebook; ruff + debug + secrets + test-per-module + generated tests → verdict", "code"),
     ("REVIEW", "Engineer approves / rejects candidates, owns the PR → Code Review Agent", "human")],
    kicker="Two-layer trust architecture",
    below=["PASS = every rule compiled deterministically, checks green, tests pass · PASS WITH FLAGS = green but a human is needed (candidates pending, flagged/notification rules, tests skipped) · FAIL = any gate check failed",
           "Candidates alone can never cause FAIL; a live provider outage degrades to flags, never a crashed generation",
           "Never hand-edit generated code — fix contracts or templates and regenerate; the diff shows exactly which contract version produced which code"],
    takeaway="The AI never writes production code. If a template cannot derive it from the contract, a person decides — and the gate says so.",
    notes="Model: claude-opus-4-8, max 2 attempts, no sampling params. Grounding failures reject any "
          "citation that is not a verbatim substring of the rule text or contract excerpt. Segmented "
          "(Header/Detail/Trailer) feeds are supported in generation via a STTM dialect extension.")

# 5 ── trust
d.cards(
    "Built for a regulated environment",
    [("AI fenced off from production code",
      ["Layer 1 templates own every module, DDL, test and job", "Layer 2 output is a review artifact, never merged", "Approval is a recorded decision, not a merge (v2 by design)"], "teal"),
     ("Byte-stable & provenanced",
      ["No timestamps or randomness in output — same contracts, same bytes", "Provenance banner: contract names + SHA-256 in every file", "Report repeats it, with the rule table and grounding"], "blue"),
     ("Gate mirrors Code Review",
      ["ruff, debug-pattern scan, secrets scan, test-file-per-module", "Optional: run the generated Spark tests locally", "Verdict computed by code, shared PASS / PASS WITH FLAGS / FAIL vocabulary"], "amber"),
     ("PHI-aware by template",
      ["PHI masked to last-4 at every log, report and error egress", "Audit columns LOB, SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME on every table", "Not-null rejects → errors table; drift → fail file / quarantine"], "grey"),
     ("Costs known before spend",
      ["UI shows calls & cost before a live run (~3 calls, ~$0.10, ~20 s)", "Mock provider by default; replay sets for zero-cost demos", "Live outage → flags, not failure"], "grey"),
     ("Tested, no client data",
      ["80 offline tests incl. golden-pair byte comparison for the extractor", "Anonymised MIDS / CV fixtures; CAQH STTM explicitly synthetic", "Real CAQH workbook never enters the repo"], "grey")],
    kicker="Governance by construction",
    cols=3, body_size=12,
    notes="Contract disagreements raise ContractMismatchError rather than being reconciled silently — "
          "the agent refuses to guess between the FRD and the STTM.")

# 6 ── where it fits
d.program_map(
    "Where it fits in the AI-in-Engineering pipeline", "codegen",
    kicker="Third of five agents",
    below=["Consumes the FRD→STTM agent's <feed>.contract.json plus the STTM mapping contract; the built-in extract-sttm command reads the client's workbook directly (flat dialect)",
           "Its generated modules and report are what the Code Review Agent reviews once the engineer opens the PR; the gate pre-flights the same checks",
           "Hand-off today: copy out/<feed>/ into the target pipeline repo with the report in the PR; ledger integration via the orchestrator's execute mode"],
    notes="Segmented (H/D/T) workbooks are generated but not yet extracted — the CAQH STTM contract in "
          "fixtures is synthetic.")

# 7 ── measured
d.kpis(
    "What we have measured so far",
    [("34–39", "files generated per feed", "PySpark modules, DDL, tests, job JSON, notebook, README, report"),
     ("~15 s · ≈$0.09", "live 3-feed generation", "3 Claude calls, 0 retries, ~15k in / ~0.7k out tokens (claude-opus-4-8)"),
     ("3 / 3", "feeds PASS WITH FLAGS", "All candidates grounded; every citation a verbatim substring"),
     ("80", "automated tests", "Offline, no Spark; extractor golden pair byte-compared; 41 templates")],
    kicker="Live end-to-end runs, 2026-08-07 (anonymised CV / MIDS fixtures)",
    below=["Contract scale handled: feeds with 86, 267 and 46 STTM fields; CAQH synthetic H/D/T feed with 10 validation rules",
           "MIDS feeds need zero LLM calls (every rule compiled deterministically); the whole fixture set needs at most 5 calls — worst case with retries 10",
           "Lifetime live LLM spend across both billed runs: ≈ $0.19",
           "Not yet measured: engineer-hours per feed baseline, defect rates, first run on a real Databricks workspace"],
    source="docs/LIVE_RUN_RECORD.md, docs/LIVE_PATH_RECON.md, fixtures/replay/live_e2e_20260807/*/report.md, CLAUDE.md. Costs are Anthropic list-price estimates from recorded token usage.",
    takeaway="Generation is fast, cheap and grounded; PASS WITH FLAGS is the correct verdict for demo feeds — it means 'a human is needed', not 'something broke'.",
    notes="Be explicit that PASS_WITH_FLAGS is expected: notification rules have no recipients yet and "
          "candidates await approval. Live outputs vary in phrasing between runs; grounding is what is stable.")

# 8 ── benefits
d.cards(
    "Expected benefits for ACFC",
    [("Speed", "Pipeline scaffolding in seconds instead of engineer-days per feed; new feeds stop waiting in the queue.", "teal"),
     ("Consistency", "One house style across every feed and engineer — byte-stable output, provenance in every file.", "teal"),
     ("Compliance by default", "PHI masking, audit columns, reject handling and recycle logic are template guarantees, not reminders.", "blue"),
     ("Safer, faster reviews", "Reviewers read a report and a diff against a known template — no reverse-engineering the spreadsheet.", "blue"),
     ("Fits the existing stack", "Plain PySpark + Delta + Workflows + Unity Catalog; structured for a mechanical DLT port later.", "amber"),
     ("Tiny, fenced AI spend", "≈ $0.10 per multi-feed run; Anthropic is the sole model vendor; live cost is shown before it is spent.", "amber")],
    kicker="Why it is worth doing",
    cols=3, body_size=13,
    notes="Benefits are expectations; the measured facts are on the previous slide.")

# 9 ── savings model
d.table_slide(
    "Time & cost savings — illustrative model",
    ["Per feed (flat file, ~100–250 columns)", "Manual today (assumed)", "With agent (assumed)", "Saving"],
    [["Write reader, drift, mapping, audit, rejects, writer, DQ, run-report modules", "24 h", "0 h (generated)", "24 h"],
     ["Author stage / standard / errors / recycle DDL", "3 h", "0 h (generated)", "3 h"],
     ["Write unit tests per module", "8 h", "0 h (generated)", "8 h"],
     ["Job definition + notebook entry point", "3 h", "0.5 h (fill cluster / schedule)", "2.5 h"],
     ["Review Layer-2 candidates, adjust, open PR", "—", "4 h", "—"],
     ["LLM cost", "—", "≈ $0.03 per feed (measured)", "—"],
     ["Total per feed", "38 h", "4.5 h + $0.03", "≈ 33.5 h (~88%)"]],
    kicker="Assumptions are placeholders — replace with ACFC's engineer effort and feed volume",
    col_widths=[3.4, 1.5, 2.2, 1.4], size=12, highlight_last=True,
    source="Effort figures are illustrative assumptions, not measurements (the repo states no engineer-hours baseline). Only generation time, LLM cost and file counts are measured (docs/LIVE_RUN_RECORD.md). "
           "Example scale-up: 2 new feeds/month × 33.5 h ≈ 800 h/yr; at an illustrative $100/h ≈ $80k/yr vs < $1/yr of LLM spend.",
    takeaway="The engineer's time moves from typing boilerplate to reviewing a report and a diff. One real feed in a pilot would replace every assumption here.",
    notes="Invite the client to replace each figure. Review time is deliberately generous — the engineer "
          "still owns the PR and the Code Review Agent reviews it.")

# 10 ── deployment
d.two_col(
    "Deployment & integration",
    "What exists today",
    ["CLI: codegen generate / generate-all / extract-sttm — dry-run, live, capture, replay",
     "Demo UI (FastAPI + React): dashboard, per-feed rules / Layer-2 review / notebook / generated-code / report tabs; Mock, Replay and confirm-gated Live modes",
     "Databricks Apps manifest (app.yaml) with API key from an app secret; single-port launcher run_demo.sh",
     "Generated job JSON targets Databricks Workflows; DDL targets Unity Catalog; notebook runs as-is",
     "Config-driven: model, cluster shape, notification recipients, segment discriminator in config/config.yaml"],
    "Pending ACFC decisions / work",
    ["First run on a real Databricks workspace / Apps deployment (never deployed yet)",
     "Client pipeline stack confirmation (plain PySpark + Workflows today; DLT port deferred)",
     "Real CAQH STTM workbook + source dictionary → segmented (H/D/T) extraction; confirm the segment discriminator",
     "Job cluster / schedule values (config guess today); notification recipients (empty → flags)",
     "Approve → merge automation (v2), once ACFC is comfortable with the review flow"],
    left_tone="teal", right_tone="grey", size=14,
    notes="Generation never opens a Databricks connection today; DATABRICKS_HOST/TOKEN are reserved for "
          "future deploy. The UI never runs the generated Spark tests (needs a JVM).")

# 11 ── limitations
d.two_col(
    "Known gaps & roadmap",
    "Honest limitations today",
    ["No run on a real Databricks workspace yet; pipeline runs in-process on the demo machine",
     "CAQH segmented workbook not extractable; its STTM contract is synthetic; discriminator is an assumption",
     "Approve → merge is manual by design; decisions do not gate",
     "Rule classifier is regex over observed phrasings — new phrasings widen Layer-2 usage",
     "Live Layer-2 output varies in wording between runs (grounding is stable)"],
    "Proposed next steps",
    ["Obtain the real CAQH STTM → build segmented-mode extraction",
     "Deploy to the client workspace; run generated tests on a real cluster",
     "Confirm stack (Workflows vs DLT) and cluster/schedule values",
     "Approval-merge v2 after pilot feedback",
     "Close the loop with the Code Review Agent on generated PRs"],
    left_tone="amber", right_tone="teal", size=14,
    notes="Say these out loud; they are the asks.")

# 12 ── closing
d.closing(
    "What we need from ACFC",
    ["One real feed (FRD + STTM workbook, anonymised) to generate end-to-end and review with your engineers",
     "The real CAQH STTM workbook and source dictionary for segmented-mode extraction",
     "A workspace to deploy into, plus cluster and scheduling conventions",
     "Baseline numbers: feeds onboarded per quarter, engineer hours per feed — to replace the illustrative savings model",
     "Confirmation of the target pipeline stack (Workflows today, DLT later?)"],
    notes="Three things to remember: templates write the code; the AI only reviews leftovers and must quote "
          "verbatim; engineers make every final call.")

d.save(OUT)
print(f"wrote {OUT} ({d.n} slides)")
