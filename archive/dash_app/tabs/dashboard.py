# =============================================================================
# DASHBOARD TAB - At-a-Glance Executive Briefing (Dash version)
# =============================================================================

import datetime as dt
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc

from components import (
    COLORS, FONTS, SHADOWS, LABEL_STYLE, SNAPPY_STYLE, CARD_STYLE,
    card, label, snappy, spacer, section_divider,
    progress_bar, signal_row, metric_card,
)
from models import classify_headline_sentiment, generate_bull_bear_case


# =============================================================================
# HELPERS
# =============================================================================

def _smart_comment(price_data):
    """Generate an intelligent trend comment based on price action."""
    current = float(price_data["Close"].iloc[-1])
    dates = price_data["Date"]

    lookbacks = {"30d": 22, "60d": 44, "90d": 63, "6m": 126}
    prices = {}
    for k, n in lookbacks.items():
        if len(price_data) > n:
            prices[k] = float(price_data["Close"].iloc[-n])

    recent = price_data.tail(63)
    high_90 = float(recent["Close"].max())
    low_90 = float(recent["Close"].min())
    high_idx = recent["Close"].idxmax()
    low_idx = recent["Close"].idxmin()

    high_date = dates.iloc[high_idx] if high_idx < len(dates) else dates.iloc[-1]
    low_date = dates.iloc[low_idx] if low_idx < len(dates) else dates.iloc[-1]

    pct_from_high = ((current - high_90) / high_90) * 100
    pct_from_low = ((current - low_90) / low_90) * 100
    range_pct = ((high_90 - low_90) / low_90) * 100

    p30 = prices.get("30d", current)
    p60 = prices.get("60d", current)
    p90 = prices.get("90d", current)

    def fmt_date(d):
        if hasattr(d, "strftime"):
            return d.strftime("%b %Y")
        return str(d)[:10]

    if current < p30 < p60 and pct_from_high < -5:
        return f"Declining since {fmt_date(high_date)}, down {abs(pct_from_high):.1f}% from its recent high of ${high_90:.2f}."
    if current > p30 > p60 and pct_from_low > 5:
        return f"Trending higher since {fmt_date(low_date)}, up {pct_from_low:.1f}% from ${low_90:.2f}."
    if range_pct < 15:
        return f"Fluctuating in a range between ${low_90:.0f}\u2013${high_90:.0f} over the past 3 months."
    if current > p30 and current < p90:
        return f"Recovering from recent lows, currently at ${current:.2f}. Still below 90-day levels."
    if current < p30 and current > p90:
        return f"Short-term pullback from ${p30:.2f} (30 days ago), but still above 90-day levels."

    chg = ((current - p90) / p90) * 100 if p90 else 0
    direction = "up" if chg > 0 else "down"
    return f"Price is {direction} {abs(chg):.1f}% over the past 3 months, currently at ${current:.2f}."


def _calc_period_returns(price_data):
    """Calculate returns for standard periods."""
    current = float(price_data["Close"].iloc[-1])
    periods = []

    def _ret(n, lbl):
        if len(price_data) > n:
            past = float(price_data["Close"].iloc[-n - 1])
            pct = ((current - past) / past) * 100
            return {"label": lbl, "value": pct}
        return {"label": lbl, "value": None}

    periods.append(_ret(1, "1D"))
    periods.append(_ret(5, "5D"))
    periods.append(_ret(22, "1M"))
    periods.append(_ret(126, "6M"))

    # YTD
    if "Date" in price_data.columns:
        dates_col = price_data["Date"]
        if hasattr(dates_col.iloc[-1], "year"):
            year_start = price_data[dates_col.dt.year == dates_col.iloc[-1].year]
        else:
            year_start = pd.DataFrame()
        if len(year_start) > 0:
            ytd_start = float(year_start["Close"].iloc[0])
            periods.append({"label": "YTD", "value": ((current - ytd_start) / ytd_start) * 100})
        else:
            periods.append({"label": "YTD", "value": None})
    else:
        periods.append({"label": "YTD", "value": None})

    periods.append(_ret(252, "1Y"))
    periods.append(_ret(1260, "5Y"))
    return periods


def _fund_snippet(info):
    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    parts = []
    if pe is not None:
        parts.append(f"P/E {pe:.1f}")
    if roe is not None:
        parts.append(f"ROE {roe * 100:.0f}%")
    metrics = ", ".join(parts) if parts else "Limited data"
    strong = (roe is not None and roe > 0.15) or (pe is not None and pe < 20)
    weak = (roe is not None and roe < 0.08) or (pe is not None and pe > 35)
    if strong:
        return f"Fundamentals are solid ({metrics})."
    if weak:
        return f"Fundamental concerns ({metrics})."
    return f"Fundamentals are mixed ({metrics})."


def build_chart(chart_df, date_col="Date", close_col="Close"):
    """Build price chart from any DataFrame with date and close columns."""
    dates = chart_df[date_col].tolist()
    close = chart_df[close_col].tolist()

    # Dynamic y-axis range with padding
    y_min = min(close)
    y_max = max(close)
    y_padding = (y_max - y_min) * 0.08 if y_max != y_min else y_max * 0.02

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=close, mode="lines",
        line=dict(color=COLORS["teal"], width=2),
        fill="tonexty", fillcolor="rgba(0, 151, 167, 0.05)",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ))
    # Invisible baseline trace at y_min for the fill area
    fig.add_trace(go.Scatter(
        x=dates, y=[y_min - y_padding] * len(dates),
        mode="lines", line=dict(width=0), showlegend=False,
        hoverinfo="skip",
    ))
    # Reorder so baseline is first, price line fills down to it
    fig.data = (fig.data[1], fig.data[0])

    fig.update_layout(
        height=220, margin=dict(l=5, r=10, t=5, b=25),
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False, hovermode="x unified",
        font=dict(family=FONTS["primary"], size=11, color=COLORS["text_secondary"]),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=COLORS["border"],
                     tickfont=dict(size=10, color=COLORS["muted"]))
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", tickprefix="$",
                     tickfont=dict(size=10, color=COLORS["muted"]),
                     range=[y_min - y_padding, y_max + y_padding])
    return fig


# Period button config
PERIOD_BUTTONS = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"]


# =============================================================================
# RENDER
# =============================================================================

def render(stock_data, price_data, cost_basis):
    ticker = stock_data["ticker"]
    info = stock_data["info"]
    change_pct = stock_data["change_pct"]
    tech_score = stock_data["tech_score"]
    volume_score = stock_data["volume_score"]
    rsi_value = stock_data["rsi_value"]
    market_regime = stock_data["market_regime"]
    paper1_details = stock_data["paper1_details"]
    recommendation_data = stock_data["recommendation"]
    news_items = stock_data["news_items"]
    logo_url = stock_data.get("logo_url", "")
    is_sp500 = stock_data.get("is_sp500", False)

    rec = recommendation_data.get("recommendation", "HOLD")
    confidence = recommendation_data.get("confidence", 50)
    rec_colors = {"BUY": COLORS["success"], "SELL": COLORS["coral"], "HOLD": COLORS["warning"]}
    rec_color = rec_colors.get(rec, COLORS["warning"])

    company_name = info.get("shortName", ticker)
    current_price = float(price_data["Close"].iloc[-1])
    change_sign = "+" if change_pct >= 0 else ""
    change_color = COLORS["success"] if change_pct >= 0 else COLORS["danger"]
    rsi_safe = rsi_value if (rsi_value is not None and not pd.isna(rsi_value)) else 50

    # =====================================================================
    # 1. HEADER
    # =====================================================================
    logo_children = []
    if logo_url:
        logo_children = [html.Img(
            src=logo_url, alt="",
            style={"width": "44px", "height": "44px", "borderRadius": "12px",
                   "objectFit": "contain", "marginRight": "14px",
                   "border": f"1px solid {COLORS['border']}",
                   "padding": "4px", "background": "#FFFFFF"},
        )]

    # Signal pill
    rec_pill = html.Div(rec, style={
        "fontSize": "13px", "fontWeight": 700, "color": "white",
        "background": rec_color, "padding": "5px 18px",
        "borderRadius": "20px", "display": "inline-block", "marginTop": "6px",
        "letterSpacing": "0.04em",
    })

    header = card([
        html.Div([
            html.Div([
                *logo_children,
                html.Div([
                    html.Div(company_name, style={
                        "fontSize": "20px", "fontWeight": 600, "color": COLORS["heading"],
                        "letterSpacing": "-0.02em", "lineHeight": "1.2",
                    }),
                    html.Span(ticker, style={
                        "fontSize": "13px", "color": COLORS["muted"],
                        "letterSpacing": "0.05em", "fontWeight": 500,
                    }),
                ]),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                html.Div([
                    html.Span(f"${current_price:.2f}", style={
                        "fontSize": "26px", "fontWeight": 600, "color": COLORS["heading"],
                        "letterSpacing": "-0.02em",
                    }),
                    html.Span(f" {change_sign}{change_pct:.2f}%", style={
                        "fontSize": "14px", "color": change_color, "fontWeight": 600,
                        "marginLeft": "6px",
                    }),
                ]),
                rec_pill,
            ], style={"textAlign": "right"}),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
    ], padding="18px 24px")

    # =====================================================================
    # 2. CHART + PERIOD RETURNS
    # =====================================================================
    # Default: 1D view (built by callback on load, placeholder empty chart)
    period_returns = _calc_period_returns(price_data)
    ret_map = {p["label"]: p["value"] for p in period_returns}

    period_btns = []
    for p_label in PERIOD_BUTTONS:
        val = ret_map.get(p_label)
        if val is not None:
            clr = COLORS["success"] if val >= 0 else COLORS["danger"]
            val_text = f"{val:+.2f}%"
        else:
            clr = COLORS["muted"]
            val_text = "—"

        is_active = (p_label == "6M")

        period_btns.append(html.Button([
            html.Div(p_label, style={
                "fontSize": "11px", "color": COLORS["teal"] if is_active else COLORS["muted"],
                "fontWeight": 600 if is_active else 500,
                "letterSpacing": "0.02em",
            }),
            html.Div(val_text, style={
                "fontSize": "13px", "color": clr, "fontWeight": 600,
            }),
        ], id=f"period-btn-{p_label}", n_clicks=0, style={
            "flex": 1, "textAlign": "center", "padding": "8px 4px",
            "borderRadius": "10px",
            "background": "#E0F4F5" if is_active else "#F8FAFB",
            "border": f"1.5px solid {COLORS['teal']}" if is_active else "1.5px solid transparent",
            "cursor": "pointer",
        }))

    chart_section = card([
        dcc.Graph(id="dashboard-price-chart", config={"displayModeBar": False},
                  style={"height": "220px"}),
        html.Div(period_btns, style={
            "display": "flex", "gap": "6px", "marginTop": "10px",
        }),
    ], padding="16px 20px")

    # =====================================================================
    # 3. SMART COMMENT
    # =====================================================================
    comment = _smart_comment(price_data)
    comment_section = html.Div(comment, style={
        "fontFamily": FONTS["primary"], "fontSize": "13px",
        "color": COLORS["text_secondary"], "lineHeight": "1.6",
        "padding": "6px 4px",
    })

    # =====================================================================
    # 4. COMPANY INFO
    # =====================================================================
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    sp500_label = "S&P 500" if is_sp500 else "Non S&P 500"
    sp500_clr = COLORS["success"] if is_sp500 else COLORS["muted"]

    desc_text = ""
    long_summary = info.get("longBusinessSummary")
    if long_summary:
        sentences = long_summary.split(". ")
        desc_text = ". ".join(sentences[:2]).strip()
        if not desc_text.endswith("."):
            desc_text += "."

    def _info_tag(lbl, val, color=None):
        return html.Div([
            html.Span(lbl, style={"fontWeight": 500, "fontSize": "12px", "color": COLORS["muted"]}),
            html.Span(f" {val}", style={
                "fontSize": "12px", "fontWeight": 600,
                "color": color or COLORS["text_primary"],
            }),
        ], style={
            "padding": "4px 12px", "background": "#F8FAFB",
            "borderRadius": "8px", "display": "inline-block",
        })

    company_info = card([
        html.Div([
            _info_tag("Sector", sector),
            _info_tag("Industry", industry),
            _info_tag("Index", sp500_label, sp500_clr),
        ], style={"display": "flex", "gap": "8px", "marginBottom": "10px", "flexWrap": "wrap"}),
        html.P(desc_text, style={
            "fontSize": "12.5px", "color": COLORS["text_secondary"],
            "lineHeight": "1.6", "margin": 0,
        }) if desc_text else html.Span(),
    ], padding="16px 20px")

    # =====================================================================
    # 5. SIGNAL BOXES
    # =====================================================================
    regime_colors = {"Bull": COLORS["success"], "Bear": COLORS["danger_red"],
                     "Sideways": COLORS["warning"], "High-Volatility": COLORS["danger_red"]}
    regime_clr = regime_colors.get(market_regime, COLORS["text_secondary"])

    box_style = {
        "flex": 1, "background": COLORS["card"], "border": f"1px solid {COLORS['border']}",
        "borderRadius": "14px", "padding": "18px 20px",
        "boxShadow": SHADOWS["sm"],
    }

    # Dynamic explanations
    _explain_style = {
        "fontSize": "11px", "color": COLORS["muted"], "lineHeight": "1.4",
        "marginTop": "8px", "fontWeight": 400,
    }

    regime_explanations = {
        "Bull": "Broad market uptrend — conditions favour long positions.",
        "Bear": "Broad market downtrend — caution advised, risk of further declines.",
        "Sideways": "No clear direction — range-bound trading, wait for breakout.",
        "High-Volatility": "Elevated uncertainty — wider price swings expected, tighten risk.",
    }
    regime_explain = regime_explanations.get(market_regime, "Market conditions are being assessed.")

    regime_box = html.Div([
        label("Market Regime"),
        html.Div(market_regime, style={
            "fontSize": "20px", "fontWeight": 700, "color": regime_clr, "marginTop": "4px",
            "letterSpacing": "-0.01em",
        }),
        html.Div(regime_explain, style=_explain_style),
    ], style=box_style)

    signal_explanations = {
        "BUY": "Technical indicators and AI model suggest upside potential.",
        "SELL": "Signals point to downside risk — consider reducing exposure.",
        "HOLD": "Mixed signals — no strong case for buying or selling right now.",
    }
    signal_explain = signal_explanations.get(rec, "Awaiting signal confirmation.")

    signal_box = html.Div([
        label("Signal"),
        html.Div(rec, style={
            "fontSize": "28px", "fontWeight": 700, "color": rec_color, "marginTop": "4px",
            "letterSpacing": "-0.02em",
        }),
        html.Div(signal_explain, style=_explain_style),
    ], style=box_style)

    conf_status_clr = COLORS["success"] if confidence >= 70 else COLORS["warning"] if confidence >= 50 else COLORS["danger"]

    if confidence >= 70:
        conf_explain = "Strong agreement across indicators — higher conviction signal."
    elif confidence >= 50:
        conf_explain = "Moderate agreement — some indicators conflict, proceed with caution."
    else:
        conf_explain = "Weak agreement — indicators are diverging, signal is unreliable."

    confidence_box = html.Div([
        label("Confidence"),
        html.Div(f"{confidence}%", style={
            "fontSize": "28px", "fontWeight": 700, "color": conf_status_clr, "marginTop": "4px",
            "letterSpacing": "-0.02em",
        }),
        html.Div(conf_explain, style=_explain_style),
    ], style=box_style)

    # Key Signals
    if paper1_details:
        ct = paper1_details.get("crossover_type", "none")
        cross_labels = {"golden_cross": ("Golden Cross", COLORS["success"]),
                        "death_cross": ("Death Cross", COLORS["danger_red"]),
                        "none": ("No Crossover", COLORS["muted"])}
        cross_name, cross_clr = cross_labels.get(ct, ("No Crossover", COLORS["muted"]))
        atv = "Confirmed" if paper1_details.get("atv_confirmed") else "Not Confirmed"
        atv_clr = COLORS["success"] if paper1_details.get("atv_confirmed") else COLORS["warning"]
        rsi_g = paper1_details.get("rsi_gate", "n/a")
        rsi_gate_map = {"passed": ("Passed", COLORS["success"]),
                        "blocked_overbought": ("Blocked", COLORS["danger_red"]),
                        "blocked_oversold": ("Blocked", COLORS["danger_red"]),
                        "n/a": ("N/A", COLORS["muted"])}
        rsi_lbl, rsi_clr = rsi_gate_map.get(rsi_g, ("N/A", COLORS["muted"]))
        rl_sig = paper1_details.get("rl_signal")
        if rl_sig:
            ai_agrees = paper1_details.get("rl_agrees", False)
            ai_status = "Agrees" if ai_agrees else "Disagrees"
            ai_clr = COLORS["success"] if ai_agrees else COLORS["warning"]
            ai_row = signal_row("AI Model", f"{rl_sig} \u2014 {ai_status}", ai_clr)
        else:
            ai_row = signal_row("AI Model", "Not Active", COLORS["muted"])
    else:
        cross_name, cross_clr = "N/A", COLORS["muted"]
        atv, atv_clr = "N/A", COLORS["muted"]
        rsi_lbl, rsi_clr = "N/A", COLORS["muted"]
        ai_row = signal_row("AI Model", "Not Active", COLORS["muted"])

    signals_box = html.Div([
        label("Key Signals"),
        html.Div([
            signal_row("Trend", cross_name, cross_clr),
            signal_row("Volume", atv, atv_clr),
            signal_row("RSI Gate", rsi_lbl, rsi_clr),
            ai_row,
        ], style={"lineHeight": "1.6"}),
    ], style={**box_style, "flex": 1.5})

    signal_boxes = html.Div([
        regime_box, signal_box, confidence_box, signals_box,
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"})

    # =====================================================================
    # 6. HEALTH CHECK
    # =====================================================================
    tech_label_text = "Strong" if tech_score >= 60 else "Weak" if tech_score < 40 else "Neutral"
    vol_label_text = "Strong" if volume_score >= 60 else "Weak" if volume_score < 40 else "Neutral"
    rsi_zone = "Overbought" if rsi_safe > 70 else "Oversold" if rsi_safe < 30 else "Neutral"
    rsi_bar_color = COLORS["coral"] if rsi_safe > 70 or rsi_safe < 30 else COLORS["teal"]

    fund_snip = _fund_snippet(info)
    bull_case, bear_case = generate_bull_bear_case(info, tech_score, price_data, market_regime)
    bull_pt = bull_case[0] if bull_case else "Potential for mean reversion"
    bear_pt = bear_case[0] if bear_case else "Standard market risk"

    health_check = card([
        label("Health Check"),
        progress_bar(f"Tech Score \u2014 {tech_label_text}", tech_score, COLORS["teal"]),
        progress_bar(f"Volume \u2014 {vol_label_text}", volume_score, COLORS["teal"]),
        progress_bar(f"Momentum (RSI) \u2014 {rsi_zone}", rsi_safe, rsi_bar_color),
        snappy(fund_snip),
        html.Div([
            html.Div(bull_pt, style={
                "flex": 1, "borderLeft": f"3px solid {COLORS['success']}", "padding": "6px 10px",
                "fontSize": "12px", "color": COLORS["text_primary"], "lineHeight": "1.4",
                "borderRadius": "0 6px 6px 0", "background": "rgba(16, 185, 129, 0.04)",
            }),
            html.Div(bear_pt, style={
                "flex": 1, "borderLeft": f"3px solid {COLORS['coral']}", "padding": "6px 10px",
                "fontSize": "12px", "color": COLORS["text_primary"], "lineHeight": "1.4",
                "borderRadius": "0 6px 6px 0", "background": "rgba(255, 107, 107, 0.04)",
            }),
        ], style={"marginTop": "14px", "display": "flex", "gap": "10px"}),
    ])

    # =====================================================================
    # 7. NEWS & SENTIMENT
    # =====================================================================
    sentiment_colors = {"Positive": COLORS["success"], "Negative": COLORS["coral"], "Neutral": COLORS["muted"]}
    news_children = []
    if news_items:
        for item in news_items[:5]:
            headline = item.get("headline", "Untitled")
            url = item.get("url", "#")
            sentiment = classify_headline_sentiment(headline)
            bc = sentiment_colors.get(sentiment, COLORS["muted"])
            news_children.append(html.Div(
                html.A(headline, href=url, target="_blank", style={
                    "fontSize": "12.5px", "fontWeight": 450,
                    "color": COLORS["text_primary"], "textDecoration": "none",
                    "lineHeight": "1.4",
                }),
                style={
                    "borderLeft": f"3px solid {bc}", "padding": "8px 12px",
                    "marginBottom": "6px", "borderRadius": "0 8px 8px 0",
                    "background": "#F8FAFB",
                },
            ))
    else:
        news_children = [html.Div("No recent news available.",
                                   style={"fontSize": "13px", "color": COLORS["muted"],
                                          "padding": "8px 0"})]

    news_section = card([label("News & Sentiment"), *news_children])

    # =====================================================================
    # ASSEMBLE
    # =====================================================================
    return html.Div([
        header,
        spacer(),
        chart_section,
        comment_section,
        spacer(),
        company_info,
        spacer(),
        signal_boxes,
        spacer(),
        html.Div([
            html.Div(health_check, style={"flex": 1, "minWidth": 0}),
            html.Div(news_section, style={"flex": 1, "minWidth": 0}),
        ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}),
    ])
