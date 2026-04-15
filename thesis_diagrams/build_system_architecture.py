"""Editable PowerPoint system architecture diagram.

Four-tier view: User -> Presentation (Streamlit) -> Business Logic -> Data & Caching -> External APIs.
Every shape is a native pptx shape — edit text, colour, and position in PowerPoint.
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# palette (muted academic)
NAVY = RGBColor(0x1F, 0x3A, 0x5F)
BLUE = RGBColor(0x1F, 0x4E, 0x79); BLUE_FILL = RGBColor(0xDE, 0xEB, 0xF7)
GREEN = RGBColor(0x38, 0x76, 0x1D); GREEN_FILL = RGBColor(0xE2, 0xEF, 0xDA)
PURPLE = RGBColor(0x5B, 0x3F, 0x8A); PURPLE_FILL = RGBColor(0xE7, 0xDD, 0xF2)
AMBER = RGBColor(0xBF, 0x7A, 0x00); AMBER_FILL = RGBColor(0xFD, 0xEA, 0xD0)
GREY = RGBColor(0x59, 0x59, 0x59)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)


def add_shape(slide, shape_type, x, y, w, h, text, fill=WHITE, line=BLACK,
              font_size=10, bold=False, font_color=BLACK, line_width=1.0, align=PP_ALIGN.CENTER):
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line; shp.line.width = Pt(line_width)
    tf = shp.text_frame; tf.word_wrap = True
    tf.margin_left = Emu(36000); tf.margin_right = Emu(36000)
    tf.margin_top = Emu(18000); tf.margin_bottom = Emu(18000)
    for i, line_text in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = line_text
        r.font.name = "Calibri"; r.font.size = Pt(font_size)
        r.font.bold = bold; r.font.color.rgb = font_color
    return shp


def add_text(slide, x, y, w, h, text, font_size=10, bold=False, italic=False,
             color=BLACK, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.name = "Calibri"; r.font.size = Pt(font_size)
    r.font.bold = bold; r.font.italic = italic; r.font.color.rgb = color
    return tb


def arrow(slide, x1, y1, x2, y2, color=GREY, width=1.5):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                      Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color; conn.line.width = Pt(width)
    # add arrow head
    from pptx.oxml.ns import qn
    ln = conn.line._get_or_add_ln()
    tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
    ln.append(tail)
    return conn


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Title
    add_text(slide, 0.3, 0.15, 13, 0.4,
             "System Architecture — Retail Stock Analytics Dashboard",
             font_size=16, bold=True, color=NAVY)

    # === Layer 1: User ===
    add_shape(slide, MSO_SHAPE.OVAL, 5.9, 0.75, 1.5, 0.55, "Retail Investor",
              fill=WHITE, line=GREY, bold=True, font_size=10)

    # === Layer 2: Presentation (Streamlit) ===
    pres_x, pres_y, pres_w, pres_h = 0.5, 1.75, 12.3, 1.25
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, pres_x, pres_y, pres_w, pres_h,
              "", fill=BLUE_FILL, line=BLUE, line_width=1.5)
    add_text(slide, pres_x + 0.15, pres_y + 0.05, 6, 0.3,
             "Presentation Layer — Streamlit (app.py, styles.py)",
             font_size=11, bold=True, color=BLUE)

    tabs = ["Dashboard", "Technical", "Fundamentals", "News"]
    tab_w = 2.2; gap = 0.25
    start_x = pres_x + (pres_w - (len(tabs) * tab_w + (len(tabs) - 1) * gap)) / 2
    for i, name in enumerate(tabs):
        add_shape(slide, MSO_SHAPE.RECTANGLE,
                  start_x + i * (tab_w + gap), pres_y + 0.45, tab_w, 0.65,
                  name, fill=WHITE, line=BLUE, bold=True, font_size=10)

    # === Layer 3: Business Logic ===
    logic_x, logic_y, logic_w, logic_h = 0.5, 3.25, 12.3, 1.55
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, logic_x, logic_y, logic_w, logic_h,
              "", fill=GREEN_FILL, line=GREEN, line_width=1.5)
    add_text(slide, logic_x + 0.15, logic_y + 0.05, 6, 0.3,
             "Business Logic Layer",
             font_size=11, bold=True, color=GREEN)

    # models.py
    add_shape(slide, MSO_SHAPE.RECTANGLE, 0.75, 3.6, 5.0, 1.15,
              "models.py\n"
              "• compute_indicators (SMA, RSI, ATV, rel. volume)\n"
              "• generate_paper1_signal  (crossover + ATV + RSI gate)\n"
              "• generate_recommendation_paper1  (+ confidence)\n"
              "• detect_market_regime  • calculate_piotroski_fscore",
              fill=WHITE, line=GREEN, bold=False, font_size=9, align=PP_ALIGN.LEFT)
    # rl_agent.py
    add_shape(slide, MSO_SHAPE.RECTANGLE, 6.0, 3.6, 3.5, 1.15,
              "rl_agent.py\n"
              "• StockTradingEnv (Gymnasium)\n"
              "• train_ppo_agent (PPO, 50K steps)\n"
              "• predict_action  (6-D state → BUY/SELL/HOLD)",
              fill=WHITE, line=GREEN, bold=False, font_size=9, align=PP_ALIGN.LEFT)
    # support
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.75, 3.6, 3.0, 1.15,
              "Support\n"
              "• styles.py (UI theming)\n"
              "• backtest utilities\n"
              "• position tracking",
              fill=WHITE, line=GREEN, bold=False, font_size=9, align=PP_ALIGN.LEFT)

    # === Layer 4: Data & Caching ===
    data_x, data_y, data_w, data_h = 0.5, 5.05, 12.3, 1.1
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, data_x, data_y, data_w, data_h,
              "", fill=PURPLE_FILL, line=PURPLE, line_width=1.5)
    add_text(slide, data_x + 0.15, data_y + 0.05, 6, 0.3,
             "Data & Caching Layer",
             font_size=11, bold=True, color=PURPLE)

    add_shape(slide, MSO_SHAPE.RECTANGLE, 0.75, 5.4, 3.8, 0.65,
              "Streamlit cache\n30-min / 1-hour / 24-hour TTLs",
              fill=WHITE, line=PURPLE, bold=False, font_size=9)
    add_shape(slide, MSO_SHAPE.RECTANGLE, 4.7, 5.4, 3.8, 0.65,
              "In-memory DataFrames\n(OHLCV, indicators, signals)",
              fill=WHITE, line=PURPLE, bold=False, font_size=9)
    add_shape(slide, MSO_SHAPE.RECTANGLE, 8.65, 5.4, 4.1, 0.65,
              "Trained PPO model artefact\n(stable-baselines3 zip)",
              fill=WHITE, line=PURPLE, bold=False, font_size=9)

    # === Layer 5: External APIs ===
    api_x, api_y, api_w, api_h = 0.5, 6.35, 12.3, 0.95
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, api_x, api_y, api_w, api_h,
              "", fill=AMBER_FILL, line=AMBER, line_width=1.5)
    add_text(slide, api_x + 0.15, api_y + 0.05, 6, 0.3,
             "External Data Sources",
             font_size=11, bold=True, color=AMBER)

    add_shape(slide, MSO_SHAPE.RECTANGLE, 0.75, 6.7, 3.8, 0.5,
              "yfinance  —  OHLCV, fundamentals, VIX, S&P 500",
              fill=WHITE, line=AMBER, bold=False, font_size=9)
    add_shape(slide, MSO_SHAPE.RECTANGLE, 4.7, 6.7, 3.8, 0.5,
              "Finnhub  —  company news & sentiment",
              fill=WHITE, line=AMBER, bold=False, font_size=9)
    add_shape(slide, MSO_SHAPE.RECTANGLE, 8.65, 6.7, 4.1, 0.5,
              "Wikipedia / StockAnalysis.com  —  ticker lists",
              fill=WHITE, line=AMBER, bold=False, font_size=9)

    # Flow arrows between layers (dual direction on the side)
    # User ↔ Presentation
    arrow(slide, 6.65, 1.3, 6.65, 1.75, color=GREY)
    arrow(slide, 6.65, 1.75, 6.65, 1.3, color=GREY)
    # Presentation → Business Logic
    arrow(slide, 6.65, 3.0, 6.65, 3.25, color=GREY)
    # Business Logic → Data
    arrow(slide, 6.65, 4.8, 6.65, 5.05, color=GREY)
    # Data → External APIs
    arrow(slide, 6.65, 6.15, 6.65, 6.35, color=GREY)
    arrow(slide, 6.65, 6.35, 6.65, 6.15, color=GREY)

    # Bottom source note
    add_text(slide, 0.3, 7.25, 12, 0.25,
             "Source: app.py, models.py, rl_agent.py, tabs/*.py, styles.py.",
             font_size=8, italic=True, color=GREY)

    out = Path(__file__).parent / "system_architecture.pptx"
    prs.save(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    build()
