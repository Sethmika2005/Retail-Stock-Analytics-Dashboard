"""Build an editable PowerPoint flowchart of the buy/sell/hold decision logic.

Every element is a native python-pptx shape + connector — all editable in PowerPoint.
Re-run this script after changes to models.py / rl_agent.py logic to regenerate.
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# --- palette ---
BLUE = RGBColor(0x1F, 0x4E, 0x79)       # rule layer
BLUE_FILL = RGBColor(0xDE, 0xEB, 0xF7)
GREEN = RGBColor(0x2E, 0x75, 0x4B)      # RL layer
GREEN_FILL = RGBColor(0xE2, 0xEF, 0xDA)
GOLD = RGBColor(0xBF, 0x90, 0x00)       # final output
GOLD_FILL = RGBColor(0xFF, 0xF2, 0xCC)
RED = RGBColor(0xC0, 0x00, 0x00)        # blocked paths
GREY = RGBColor(0x59, 0x59, 0x59)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)


def add_shape(slide, shape_type, x, y, w, h, text, fill=WHITE, line=BLACK,
              font_size=9, bold=False, font_color=BLACK, line_width=1.0):
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line
    shp.line.width = Pt(line_width)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(36000)
    tf.margin_right = Emu(36000)
    tf.margin_top = Emu(18000)
    tf.margin_bottom = Emu(18000)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.name = "Calibri"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = font_color
    return shp


def add_label(slide, x, y, w, h, text, font_size=8, italic=True, color=GREY):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.name = "Calibri"
    run.font.size = Pt(font_size)
    run.font.italic = italic
    run.font.color.rgb = color
    return tb


def add_title(slide, x, y, w, h, text, font_size=12, color=BLACK):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.name = "Calibri"
    run.font.size = Pt(font_size)
    run.font.bold = True
    run.font.color.rgb = color
    return tb


def connect(slide, src, dst, color=BLACK, width=1.25, dashed=False):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.ELBOW, 0, 0, 0, 0)
    conn.begin_connect(src, 2)  # 2 = bottom connection point typically
    conn.end_connect(dst, 0)    # 0 = top
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    if dashed:
        from pptx.oxml.ns import qn
        ln = conn.line._get_or_add_ln()
        prstDash = ln.makeelement(qn("a:prstDash"), {"val": "dash"})
        ln.append(prstDash)
    return conn


def connect_sides(slide, src, src_idx, dst, dst_idx, color=BLACK, width=1.25):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.ELBOW, 0, 0, 0, 0)
    conn.begin_connect(src, src_idx)
    conn.end_connect(dst, dst_idx)
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    return conn


def build():
    prs = Presentation()
    # Portrait A4-ish: 8.27" x 11.69". Use 8.5 x 11.
    prs.slide_width = Inches(8.5)
    prs.slide_height = Inches(13.5)
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)

    # ---- Title ----
    add_title(slide, 0.4, 0.2, 7.7, 0.4,
              "Buy / Sell / Hold Decision Logic — SMA Crossover + ATV + RSI + RL Overlay",
              font_size=14)

    # ==================== INPUT SECTION ====================
    add_title(slide, 0.4, 0.7, 3, 0.3, "1. Inputs & Indicators", font_size=11, color=BLUE)

    n_data = add_shape(slide, MSO_SHAPE.PARALLELOGRAM, 3.0, 1.05, 2.5, 0.55,
                       "Daily OHLCV data (yfinance)", fill=BLUE_FILL, line=BLUE, bold=True)

    n_indic = add_shape(slide, MSO_SHAPE.RECTANGLE, 3.0, 1.85, 2.5, 0.55,
                        "Compute SMA20, SMA50,\nATV slope, RSI", fill=BLUE_FILL, line=BLUE)

    n_cross = add_shape(slide, MSO_SHAPE.RECTANGLE, 3.0, 2.65, 2.5, 0.55,
                        "Derive SMA_Cross_Signal\n(+1 golden / 0 none / −1 death)",
                        fill=BLUE_FILL, line=BLUE)

    connect(slide, n_data, n_indic, color=BLUE)
    connect(slide, n_indic, n_cross, color=BLUE)

    # ==================== RULE LAYER ====================
    add_title(slide, 0.4, 3.45, 5, 0.3, "2. Rule Layer (Paper 1)", font_size=11, color=BLUE)

    # central decision
    n_cross_dec = add_shape(slide, MSO_SHAPE.DIAMOND, 3.25, 3.8, 2.0, 1.0,
                            "SMA_Cross_Signal?", fill=BLUE_FILL, line=BLUE, bold=True)
    connect(slide, n_cross, n_cross_dec, color=BLUE)

    # --- Golden cross branch (left) ---
    n_atv_g = add_shape(slide, MSO_SHAPE.DIAMOND, 0.4, 5.1, 1.8, 0.9,
                        "ATV slope > 0 ?", fill=BLUE_FILL, line=BLUE)
    n_rsi_g = add_shape(slide, MSO_SHAPE.DIAMOND, 0.4, 6.3, 1.8, 0.9,
                        "RSI > 70 ?", fill=BLUE_FILL, line=BLUE)
    n_buy_blocked = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.4, 7.55, 1.8, 0.6,
                              "Rule: HOLD\n(blocked — overbought)",
                              fill=WHITE, line=RED, font_color=RED, line_width=1.5, font_size=8)
    n_buy = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.4, 8.35, 1.8, 0.6,
                      "Rule: BUY", fill=GOLD_FILL, line=GOLD, bold=True, font_size=11)
    n_hold_g = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 2.35, 5.25, 0.8, 0.55,
                         "HOLD", fill=WHITE, line=GREY, font_size=9)

    # --- None branch (centre) ---
    n_hold_none = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 3.7, 5.25, 1.1, 0.55,
                            "Rule: HOLD\n(no crossover)", fill=WHITE, line=GREY, font_size=8)

    # --- Death cross branch (right) ---
    n_atv_d = add_shape(slide, MSO_SHAPE.DIAMOND, 6.3, 5.1, 1.8, 0.9,
                        "ATV slope > 0 ?", fill=BLUE_FILL, line=BLUE)
    n_rsi_d = add_shape(slide, MSO_SHAPE.DIAMOND, 6.3, 6.3, 1.8, 0.9,
                        "RSI < 30 ?", fill=BLUE_FILL, line=BLUE)
    n_sell_blocked = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 6.3, 7.55, 1.8, 0.6,
                               "Rule: HOLD\n(blocked — oversold)",
                               fill=WHITE, line=RED, font_color=RED, line_width=1.5, font_size=8)
    n_sell = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 6.3, 8.35, 1.8, 0.6,
                       "Rule: SELL", fill=GOLD_FILL, line=GOLD, bold=True, font_size=11)
    n_hold_d = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 5.35, 5.25, 0.8, 0.55,
                         "HOLD", fill=WHITE, line=GREY, font_size=9)

    # Connect crossover decision to branches
    connect_sides(slide, n_cross_dec, 1, n_atv_g, 1, color=BLUE)       # left
    connect(slide, n_cross_dec, n_hold_none, color=BLUE)                # bottom (none)
    connect_sides(slide, n_cross_dec, 3, n_atv_d, 3, color=BLUE)        # right

    # Golden branch internal
    connect(slide, n_atv_g, n_rsi_g, color=BLUE)
    connect_sides(slide, n_atv_g, 3, n_hold_g, 1, color=GREY)  # No → HOLD
    connect(slide, n_rsi_g, n_buy_blocked, color=RED)           # Yes (overbought) → blocked
    connect(slide, n_buy_blocked, n_buy, color=GREY)            # visual continuation (label says No leads to BUY via alternative)
    # cleaner: connect RSI NO side directly to BUY
    connect_sides(slide, n_rsi_g, 3, n_buy, 1, color=BLUE)

    # Death branch internal
    connect(slide, n_atv_d, n_rsi_d, color=BLUE)
    connect_sides(slide, n_atv_d, 1, n_hold_d, 3, color=GREY)
    connect(slide, n_rsi_d, n_sell_blocked, color=RED)
    connect_sides(slide, n_rsi_d, 1, n_sell, 3, color=BLUE)

    # Edge labels
    add_label(slide, 2.15, 4.25, 1.0, 0.25, "+1 Golden")
    add_label(slide, 3.6, 4.85, 1.3, 0.25, "0 None")
    add_label(slide, 5.3, 4.25, 1.0, 0.25, "−1 Death")

    add_label(slide, 0.0, 5.95, 0.6, 0.25, "No")
    add_label(slide, 2.1, 5.5, 0.4, 0.25, "No")
    add_label(slide, 8.0, 5.95, 0.5, 0.25, "No")
    add_label(slide, 5.9, 5.5, 0.4, 0.25, "No")

    add_label(slide, 1.0, 6.05, 0.6, 0.25, "Yes")
    add_label(slide, 6.9, 6.05, 0.6, 0.25, "Yes")
    add_label(slide, 1.0, 7.25, 0.6, 0.25, "Yes → blocked", color=RED, italic=False)
    add_label(slide, 6.9, 7.25, 0.6, 0.25, "Yes → blocked", color=RED, italic=False)
    add_label(slide, 1.0, 7.95, 0.6, 0.25, "No")
    add_label(slide, 6.9, 7.95, 0.6, 0.25, "No")

    # ==================== RL OVERLAY ====================
    add_title(slide, 0.4, 9.2, 5, 0.3, "3. RL Overlay (PPO Agent)", font_size=11, color=GREEN)

    n_ppo = add_shape(slide, MSO_SHAPE.RECTANGLE, 0.4, 9.6, 3.5, 0.75,
                      "PPO agent predicts action from 6-D state\n[SMA cross, ATV norm, 1d ret, 5d ret, RSI norm, rel vol]",
                      fill=GREEN_FILL, line=GREEN, font_size=8)

    n_rule_out = add_shape(slide, MSO_SHAPE.RECTANGLE, 4.6, 9.6, 3.5, 0.75,
                           "Rule signal\n(BUY / SELL / HOLD)",
                           fill=BLUE_FILL, line=BLUE, bold=True, font_size=10)

    n_agree = add_shape(slide, MSO_SHAPE.DIAMOND, 3.0, 10.6, 2.5, 1.0,
                        "RL action\n== Rule signal ?", fill=GREEN_FILL, line=GREEN, bold=True)

    connect(slide, n_ppo, n_agree, color=GREEN)
    connect(slide, n_rule_out, n_agree, color=BLUE)

    # Yes → agreement path
    n_final_rule = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 5.9, 11.85, 2.2, 0.7,
                             "Final = Rule signal\n(confidence boosted)",
                             fill=GOLD_FILL, line=GOLD, bold=True, font_size=9)
    connect_sides(slide, n_agree, 3, n_final_rule, 1, color=GREEN)
    add_label(slide, 5.5, 11.5, 0.5, 0.25, "Yes")

    # No → check override condition
    n_override_check = add_shape(slide, MSO_SHAPE.DIAMOND, 0.4, 11.7, 2.3, 1.0,
                                 "Rule was HOLD\ndue to no crossover ?",
                                 fill=GREEN_FILL, line=GREEN, font_size=8)
    connect_sides(slide, n_agree, 1, n_override_check, 3, color=GREEN)
    add_label(slide, 2.55, 11.5, 0.4, 0.25, "No")

    n_override = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.4, 12.9, 2.3, 0.5,
                           "RL OVERRIDES\nFinal = RL signal",
                           fill=GOLD_FILL, line=GOLD, bold=True, font_size=9)
    n_rule_wins = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 3.15, 12.9, 2.3, 0.5,
                            "Rule wins\nFinal = Rule (conf. reduced)",
                            fill=GOLD_FILL, line=GOLD, bold=True, font_size=9)
    connect(slide, n_override_check, n_override, color=GREEN)
    connect_sides(slide, n_override_check, 3, n_rule_wins, 1, color=BLUE)
    add_label(slide, 0.8, 12.7, 0.5, 0.2, "Yes")
    add_label(slide, 2.8, 12.7, 0.4, 0.2, "No")

    # Legend
    add_title(slide, 6.0, 0.7, 2.3, 0.25, "Legend", font_size=10, color=GREY)
    lx = 6.0
    ly = 1.05
    add_shape(slide, MSO_SHAPE.PARALLELOGRAM, lx, ly, 0.3, 0.18, "", fill=BLUE_FILL, line=BLUE)
    add_label(slide, lx + 0.35, ly - 0.02, 1.9, 0.25, "Input / data", italic=False)
    add_shape(slide, MSO_SHAPE.RECTANGLE, lx, ly + 0.25, 0.3, 0.18, "", fill=BLUE_FILL, line=BLUE)
    add_label(slide, lx + 0.35, ly + 0.23, 1.9, 0.25, "Process (rule)", italic=False)
    add_shape(slide, MSO_SHAPE.RECTANGLE, lx, ly + 0.50, 0.3, 0.18, "", fill=GREEN_FILL, line=GREEN)
    add_label(slide, lx + 0.35, ly + 0.48, 1.9, 0.25, "Process (RL)", italic=False)
    add_shape(slide, MSO_SHAPE.DIAMOND, lx, ly + 0.75, 0.3, 0.2, "", fill=BLUE_FILL, line=BLUE)
    add_label(slide, lx + 0.35, ly + 0.75, 1.9, 0.25, "Decision", italic=False)
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, lx, ly + 1.05, 0.3, 0.18, "", fill=GOLD_FILL, line=GOLD)
    add_label(slide, lx + 0.35, ly + 1.03, 1.9, 0.25, "Final / terminal", italic=False)
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, lx, ly + 1.30, 0.3, 0.18, "", fill=WHITE, line=RED)
    add_label(slide, lx + 0.35, ly + 1.28, 1.9, 0.25, "Blocked path (RSI)", italic=False, color=RED)

    # Source note (bottom-right, small)
    add_label(slide, 4.5, 13.2, 3.9, 0.25,
              "Source: models.py : generate_paper1_signal + generate_recommendation_paper1",
              font_size=7)

    out = Path(__file__).parent / "buy_sell_decision_flowchart.pptx"
    prs.save(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    build()
