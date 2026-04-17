# Overview tab — at-a-glance executive briefing

import datetime as dt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import classify_headline_sentiment
from styles import (
    CARD, LABEL, EXPLAIN, FONT, TEAL, CORAL, SUCCESS, WARNING, DANGER, MUTED, TEXT,
    TEXT_SEC, BORDER, CARD_BG, SIDEBAR_BG,
    progress_bar, signal_row, chart_layout, chart_axes,
)

BOX = CARD + "padding:18px 20px;"


# Trend narrative based on price action
def _smart_comment(price_data):
    current = float(price_data["Close"].iloc[-1])
    dates = price_data["Date"]

    # dict comprehension: look back N trading days (22 per month) to get historical prices
    lookbacks = {"30d": 22, "60d": 44, "90d": 63, "6m": 126}
    prices = {k: float(price_data["Close"].iloc[-n]) for k, n in lookbacks.items() if len(price_data) > n}

    recent = price_data.tail(63)
    high_90, low_90 = float(recent["Close"].max()), float(recent["Close"].min())
    high_idx, low_idx = recent["Close"].idxmax(), recent["Close"].idxmin()
    high_date = dates.iloc[high_idx]
    low_date = dates.iloc[low_idx]
    pct_from_high = ((current - high_90) / high_90) * 100
    pct_from_low = ((current - low_90) / low_90) * 100
    range_pct = ((high_90 - low_90) / low_90) * 100

    price_30d_ago = prices.get("30d", current)
    price_60d_ago = prices.get("60d", current)
    price_90d_ago = prices.get("90d", current)

    def fmt(d):
        # hasattr check because dates could be datetime objects or plain strings
        return d.strftime("%b %Y") if hasattr(d, "strftime") else str(d)[:10]

    if current < price_30d_ago < price_60d_ago and pct_from_high < -5:
        return f"Declining since {fmt(high_date)}, down {abs(pct_from_high):.1f}% from its recent high of ${high_90:.2f}."
    if current > price_30d_ago > price_60d_ago and pct_from_low > 5:
        return f"Trending higher since {fmt(low_date)}, up {pct_from_low:.1f}% from ${low_90:.2f}."
    if range_pct < 15:
        return f"Fluctuating in a range between ${low_90:.0f}\u2013${high_90:.0f} over the past 3 months."
    if current > price_30d_ago and current < price_90d_ago:
        return f"Recovering from recent lows, currently at ${current:.2f}. Still below 90-day levels."
    if current < price_30d_ago and current > price_90d_ago:
        return f"Short-term pullback from ${price_30d_ago:.2f} (30 days ago), but still above 90-day levels."

    chg = ((current - price_90d_ago) / price_90d_ago) * 100
    return f"Price is {'up' if chg > 0 else 'down'} {abs(chg):.1f}% over the past 3 months, currently at ${current:.2f}."


def _calc_period_returns(price_data):
    current = float(price_data["Close"].iloc[-1])
    def _ret(n, lbl):
        if len(price_data) > n:
            past = float(price_data["Close"].iloc[-n - 1])
            return {"label": lbl, "value": ((current - past) / past) * 100}
        return {"label": lbl, "value": None}

    periods = [_ret(1, "1D"), _ret(5, "5D"), _ret(22, "1M"), _ret(126, "6M")]

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

    periods += [_ret(252, "1Y"), _ret(1260, "5Y")]
    return periods


def _fund_snippet(info):
    pe, roe = info.get("trailingPE"), info.get("returnOnEquity")
    parts = []
    if pe is not None: parts.append(f"P/E {pe:.1f}")
    if roe is not None: parts.append(f"ROE {roe * 100:.0f}%")
    metrics = ", ".join(parts) if parts else "Limited data"
    strong = (roe is not None and roe > 0.15) or (pe is not None and pe < 20)
    weak = (roe is not None and roe < 0.08) or (pe is not None and pe > 35)
    if strong: return f"Fundamentals are solid ({metrics})."
    if weak: return f"Fundamental concerns ({metrics})."
    return f"Fundamentals are mixed ({metrics})."


def _build_chart(price_data, n_days=126):
    chart_df = price_data.tail(n_days).copy()
    dates, close = chart_df["Date"].tolist(), chart_df["Close"].tolist()
    y_min, y_max = min(close), max(close)
    pad = (y_max - y_min) * 0.08 if y_max != y_min else y_max * 0.02

    fig = go.Figure()
    # invisible baseline trace at bottom — the next trace uses fill="tonexty" to shade
    # the area between this invisible line and the actual price line
    fig.add_trace(go.Scatter(x=dates, y=[y_min - pad] * len(dates), mode="lines",
                              line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dates, y=close, mode="lines", line=dict(color=TEAL, width=2),
                              fill="tonexty", fillcolor="rgba(0,151,167,0.05)",
                              hovertemplate="$%{y:.2f}<extra></extra>"))
    fig.update_layout(height=220, margin=dict(l=5, r=10, t=5, b=25),
                      plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
                      hovermode="x unified",
                      font=dict(family=FONT, size=11, color=TEXT_SEC))
    fig.update_xaxes(showgrid=False, showline=True, linecolor=BORDER,
                     tickfont=dict(size=10, color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", tickprefix="$",
                     tickfont=dict(size=10, color=MUTED),
                     range=[y_min - pad, y_max + pad])
    return fig


def render(selected, price_data, info, last_row, change_pct,
           volume_score, volume_details,
           market_regime, regime_metrics,
           recommendation_data, rsi_value,
           news_items, cost_basis, rule_details,
           logo_url="", is_sp500=False, chart_period="6M", piotroski_score=None):

    rec = recommendation_data.get("recommendation", "HOLD")
    confidence = recommendation_data.get("confidence", 50)
    rec_colors = {"BUY": TEAL, "SELL": CORAL, "HOLD": WARNING}
    rec_color = rec_colors.get(rec, WARNING)

    company_name = info.get("shortName", selected)
    current_price = float(price_data["Close"].iloc[-1])
    change_sign = "+" if change_pct >= 0 else ""
    change_color = SUCCESS if change_pct >= 0 else DANGER
    rsi_safe = rsi_value if rsi_value is not None and not pd.isna(rsi_value) else 50  # default to neutral RSI if missing so UI doesn't break

    logo_html = ""
    if logo_url:
        logo_html = (
            f'<img src="{logo_url}" alt="" '
            f'style="width:44px;height:44px;border-radius:12px;object-fit:contain;margin-right:14px;'
            f'border:1px solid {BORDER};padding:4px;background:{CARD_BG};" '
            f'onerror="this.style.display=\'none\'">')

    # 1. Header
    st.html(f"""
    <div style="{CARD} padding:18px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;">
                {logo_html}
                <div>
                    <div style="font-size:20px;font-weight:600;color:#0F172A;letter-spacing:-0.02em;
                                line-height:1.2;font-family:{FONT};">{company_name}</div>
                    <span style="font-size:13px;color:{MUTED};letter-spacing:0.05em;font-weight:500;
                                 font-family:{FONT};">{selected}</span>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="text-align:right;">
                    <span style="font-size:28px;font-weight:700;color:#0F172A;letter-spacing:-0.02em;
                                 font-family:'Calibri','Segoe UI',sans-serif;">${current_price:.2f}</span>
                    <span style="font-size:14px;color:{change_color};font-weight:600;margin-left:8px;
                                 font-family:{FONT};">{change_sign}{change_pct:.2f}%</span>
                </div>
                <div style="font-size:13px;font-weight:700;color:white;background:{rec_color};
                            padding:5px 18px;border-radius:20px;letter-spacing:0.04em;">{rec}</div>
            </div>
        </div>
    </div>
    """)
    st.markdown("<div style='height:3px;'></div>", unsafe_allow_html=True)

    # 2. Chart + period returns
    _period_days = {"1D": 1, "5D": 5, "1M": 22, "6M": 126, "1Y": 252, "5Y": 1260, "MAX": len(price_data)}
    if chart_period == "YTD":
        _today = price_data["Date"].iloc[-1]
        _yr = _today.year if hasattr(_today, 'year') else dt.date.today().year
        _ytd_mask = price_data["Date"].dt.year == _yr
        _n_days = max(int(_ytd_mask.sum()), 1)
    else:
        _n_days = min(_period_days.get(chart_period, 126), len(price_data))

    fig = _build_chart(price_data, n_days=_n_days)
    # flatten the returns list into a dict for quick lookup by period label
    ret_map = {p["label"]: p["value"] for p in _calc_period_returns(price_data)}

    period_buttons_html = ""
    for period_label in ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"]:
        return_val = ret_map.get(period_label)
        return_color = (SUCCESS if return_val >= 0 else DANGER) if return_val is not None else MUTED
        return_text = f"{return_val:+.2f}%" if return_val is not None else "\u2014"
        is_active = period_label == chart_period
        background = "#E0F4F5" if is_active else SIDEBAR_BG
        border_style = f"1.5px solid {TEAL}" if is_active else "1.5px solid transparent"
        label_color = TEAL if is_active else MUTED
        label_weight = "600" if is_active else "500"
        period_buttons_html += (
            f'<div style="flex:1;text-align:center;padding:8px 4px;border-radius:10px;'
            f'background:{background};border:{border_style};">'
            f'<div style="font-size:11px;color:{label_color};font-weight:{label_weight};letter-spacing:0.02em;'
            f'font-family:{FONT};">{period_label}</div>'
            f'<div style="font-size:13px;color:{return_color};font-weight:600;font-family:{FONT};">{return_text}</div>'
            f'</div>')

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:14px;
                box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);
                min-height:380px;margin-bottom:-370px;"></div>
    """, unsafe_allow_html=True)
    _, dc, _ = st.columns([0.2, 9.6, 0.2])
    with dc:
        st.plotly_chart(fig, use_container_width=True, key="dash_price_chart", config={"displayModeBar": False})
    st.markdown(f'<div style="padding:4px 16px 12px 16px;display:flex;gap:6px;">{period_buttons_html}</div>',
                unsafe_allow_html=True)

    # 3. Smart comment
    st.markdown(f"""
    <div style="font-family:{FONT};font-size:13px;color:{TEXT_SEC};line-height:1.6;
                padding:6px 4px 6px 20px;">{_smart_comment(price_data)}</div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:45px;'></div>", unsafe_allow_html=True)

    # 4. Company info
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    sp500_label = "S&P 500" if is_sp500 else "Non S&P 500"
    sp500_clr = SUCCESS if is_sp500 else MUTED

    long_summary = info.get("longBusinessSummary")
    desc_text = ""
    if long_summary:
        sentences = long_summary.split(". ")
        desc_text = ". ".join(sentences[:2]).strip()
        if not desc_text.endswith("."): desc_text += "."

    desc_html = (f'<p style="font-size:12.5px;color:{TEXT_SEC};line-height:1.6;margin:0;'
                 f'font-family:{FONT};">{desc_text}</p>') if desc_text else ""

    def _tag(lbl, val, color=""):
        c = f"color:{color};" if color else f"color:{TEXT};"
        return (f'<div style="padding:4px 12px;background:{SIDEBAR_BG};border-radius:8px;display:inline-block;">'
                f'<span style="font-weight:500;font-size:12px;color:{MUTED};font-family:{FONT};">{lbl}</span>'
                f' <span style="font-size:12px;font-weight:600;{c}font-family:{FONT};">{val}</span></div>')

    st.markdown(f"""
    <div style="{CARD} padding:16px 20px;">
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
            {_tag("Sector", sector)} {_tag("Industry", industry)} {_tag("Index", sp500_label, sp500_clr)}
        </div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # 5. Signal boxes
    regime_colors = {"Bull": SUCCESS, "Bear": DANGER, "Sideways": WARNING, "High-Volatility": DANGER}
    regime_clr = regime_colors.get(market_regime, TEXT_SEC)

    regime_explanations = {
        "Bull": "Broader market trending upward — generally supports stock prices.",
        "Bear": "Broader market trending downward — generally pressures stock prices.",
        "Sideways": "No clear market trend — prices may fluctuate without sustained direction.",
        "High-Volatility": "Larger-than-usual price swings — increased uncertainty.",
    }
    regime_explain = regime_explanations.get(market_regime, "Market conditions being assessed.")

    crossover_type = rule_details.get("crossover_type", "none") if rule_details else "none"
    atv_confirmed = rule_details.get("atv_confirmed", False) if rule_details else False
    rl_override = rule_details.get("rl_override", False) if rule_details else False

    if rec == "BUY":
        if crossover_type == "golden_cross" and atv_confirmed:
            signal_explain = "Golden Cross with rising volume confirmed by ATV slope. RSI gate passed."
        elif rl_override:
            signal_explain = "No SMA crossover. RL agent identified a buying opportunity."
        else:
            signal_explain = "SMA crossover with volume and RSI confirmation pointing upward."
    elif rec == "SELL":
        if crossover_type == "death_cross" and atv_confirmed:
            signal_explain = "Death Cross with rising volume confirmed by ATV slope. RSI gate passed."
        elif rl_override:
            signal_explain = "No SMA crossover. RL agent identified downside risk."
        else:
            signal_explain = "SMA crossover with volume and RSI confirmation pointing downward."
    else:
        if crossover_type == "none" and not rl_override:
            signal_explain = "No SMA-20/50 crossover detected. Holding until confirmed crossover with volume support."
        elif crossover_type in ("golden_cross", "death_cross") and not atv_confirmed:
            signal_explain = "Crossover detected but ATV slope did not confirm — signal weakened to HOLD."
        else:
            signal_explain = "RSI gate or conflicting signals resulted in HOLD."

    confidence_color = SUCCESS if confidence >= 70 else WARNING if confidence >= 50 else DANGER
    if confidence >= 70:
        confidence_explain = "All indicators aligned — crossover, volume, and RL agreement."
    elif confidence >= 50:
        confidence_explain = "Some indicators not fully aligned."
    else:
        confidence_explain = "Weak signal — no crossover or volume not confirmed."

    # Key signals data
    if rule_details:
        cross_labels = {"golden_cross": ("Golden Cross", SUCCESS), "death_cross": ("Death Cross", DANGER),
                        "none": ("No Crossover", MUTED)}
        cross_name, cross_color = cross_labels.get(crossover_type, ("No Crossover", MUTED))
        atv = "Confirmed" if rule_details.get("atv_confirmed") else "Not Confirmed"
        atv_color = SUCCESS if rule_details.get("atv_confirmed") else WARNING
        rsi_gate = rule_details.get("rsi_gate", "n/a")
        rsi_map = {"passed": ("Passed", SUCCESS), "blocked_overbought": ("Blocked \u2014 Overbought", DANGER),
                   "blocked_oversold": ("Blocked \u2014 Oversold", DANGER), "n/a": ("N/A", MUTED)}
        rsi_label, rsi_color = rsi_map.get(rsi_gate, ("N/A", MUTED))
        rl_signal = rule_details.get("rl_signal")
        if rl_signal:
            rl_agrees = rule_details.get("rl_agrees", False)
            if rule_details.get("rl_override"):
                rl_status, rl_color_badge = "Override", WARNING
            elif rl_agrees:
                rl_status, rl_color_badge = "Agrees", SUCCESS
            else:
                rl_status, rl_color_badge = "Disagrees", WARNING
            rl_row = signal_row("RL Agent (PPO)", f"{rl_signal} \u2014 {rl_status}", rl_color_badge)
        else:
            rl_row = signal_row("RL Agent (PPO)", "Not Active", MUTED)
    else:
        cross_name, cross_color = "N/A", MUTED
        atv, atv_color = "N/A", MUTED
        rsi_label, rsi_color = "N/A", MUTED
        rl_row = signal_row("RL Agent (PPO)", "Not Active", MUTED)

    sig_cols = st.columns([1, 1, 1, 1.5])
    with sig_cols[0]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Market Regime</div>
            <div style="font-size:20px;font-weight:700;color:{regime_clr};margin-top:4px;
                        letter-spacing:-0.01em;font-family:{FONT};">{market_regime}</div>
            <div style="{EXPLAIN}">{regime_explain}</div>
        </div>""", unsafe_allow_html=True)
    with sig_cols[1]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Signal</div>
            <div style="font-size:28px;font-weight:700;color:{rec_color};margin-top:4px;
                        letter-spacing:-0.02em;font-family:{FONT};">{rec}</div>
            <div style="{EXPLAIN}">{signal_explain}</div>
        </div>""", unsafe_allow_html=True)
    with sig_cols[2]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Confidence</div>
            <div style="font-size:28px;font-weight:700;color:{confidence_color};margin-top:4px;
                        letter-spacing:-0.02em;font-family:{FONT};">{confidence}%</div>
            <div style="{EXPLAIN}">{confidence_explain}</div>
        </div>""", unsafe_allow_html=True)
    with sig_cols[3]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Key Signals</div>
            <div style="line-height:1.6;font-family:{FONT};">
                {signal_row("SMA Crossover", cross_name, cross_color)}
                {signal_row("ATV Volume", atv, atv_color)}
                {signal_row("RSI Gate", rsi_label, rsi_color)}
                {rl_row}
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # 6. Health check + news
    news_col, hc_col = st.columns(2)

    with hc_col:
        rsi_zone = "Overbought" if rsi_safe > 70 else "Oversold" if rsi_safe < 30 else "Neutral"
        rsi_bar_color = CORAL if rsi_safe > 70 or rsi_safe < 30 else TEAL

        sma50_hc = float(price_data["SMA50"].iloc[-1]) if "SMA50" in price_data.columns and pd.notna(price_data["SMA50"].iloc[-1]) else None
        sma50_row = ""
        if sma50_hc is not None:
            pct_vs = (current_price - sma50_hc) / sma50_hc * 100
            pct_color = SUCCESS if pct_vs >= 0 else CORAL
            sma50_row = (
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid {BORDER};">'
                f'<span style="font-size:12px;color:{TEXT_SEC};font-family:{FONT};">Price vs SMA50</span>'
                f'<span style="font-size:12px;font-weight:700;color:{pct_color};font-family:{FONT};">'
                f'{"+" if pct_vs >= 0 else ""}{pct_vs:.1f}% {"above" if pct_vs >= 0 else "below"}</span></div>')

        rel_vol_hc = float(price_data["Rel_Volume"].iloc[-1]) if "Rel_Volume" in price_data.columns and pd.notna(price_data["Rel_Volume"].iloc[-1]) else None
        rel_vol_row = ""
        if rel_vol_hc is not None:
            rv_label, rv_color = ("High Activity", SUCCESS) if rel_vol_hc >= 2.0 else \
                                  ("Normal Activity", TEAL) if rel_vol_hc >= 0.8 else ("Low Activity", WARNING)
            rel_vol_row = (
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid {BORDER};">'
                f'<span style="font-size:12px;color:{TEXT_SEC};font-family:{FONT};">Relative Volume</span>'
                f'<span style="font-size:12px;font-weight:700;color:{rv_color};font-family:{FONT};">'
                f'{rel_vol_hc:.2f}x \u2014 {rv_label}</span></div>')

        fscore_bar = ""
        if piotroski_score is not None:
            fs_val = int(piotroski_score / 9 * 100)
            fs_color = SUCCESS if piotroski_score >= 7 else WARNING if piotroski_score >= 4 else CORAL
            fs_label = "Strong" if piotroski_score >= 7 else "Moderate" if piotroski_score >= 4 else "Weak"
            fscore_bar = progress_bar(f"Piotroski F-Score \u2014 {piotroski_score}/9 ({fs_label})", fs_val, fs_color)

        bars = progress_bar(f"RSI Momentum \u2014 {rsi_zone}", rsi_safe, rsi_bar_color) + fscore_bar

        st.markdown(f"""
        <div style="{CARD} padding:16px 20px;">
            <div style="{LABEL}">Health Check</div>
            {bars} {sma50_row} {rel_vol_row}
            <div style="font-family:{FONT};font-size:13px;color:{TEXT_SEC};line-height:1.5;
                        margin-top:8px;">{_fund_snippet(info)}</div>
        </div>""", unsafe_allow_html=True)

    with news_col:
        sentiment_colors = {"Positive": SUCCESS, "Negative": CORAL, "Neutral": MUTED}
        news_html = ""
        if news_items:
            for item in news_items[:5]:
                headline = item.get("headline", "Untitled")
                url = item.get("url", "#")
                sentiment = classify_headline_sentiment(headline)
                bc = sentiment_colors.get(sentiment, MUTED)
                news_html += (
                    f'<div style="border-left:3px solid {bc};padding:8px 12px;margin-bottom:6px;'
                    f'border-radius:0 8px 8px 0;background:{SIDEBAR_BG};">'
                    f'<a href="{url}" target="_blank" style="font-size:12.5px;font-weight:450;'
                    f'color:{TEXT};text-decoration:none;line-height:1.4;font-family:{FONT};">'
                    f'{headline}</a></div>')
        else:
            news_html = f'<div style="font-size:13px;color:{MUTED};padding:8px 0;font-family:{FONT};">No recent news available.</div>'

        st.markdown(f"""
        <div style="{CARD} padding:16px 20px;">
            <div style="{LABEL}">News & Sentiment</div>
            {news_html}
        </div>""", unsafe_allow_html=True)

    # 7. My Position
    if cost_basis is not None:
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        pnl_pct = (current_price - cost_basis) / cost_basis * 100
        pnl_dollar = current_price - cost_basis
        pnl_color = SUCCESS if pnl_pct >= 0 else DANGER
        pnl_label = "profit" if pnl_pct >= 0 else "loss"
        action_word = "gain" if pnl_pct >= 0 else "lose"

        examples = ""
        for qty in [10, 50, 100]:
            total = pnl_dollar * qty
            examples += (
                f'<span style="display:inline-block;padding:3px 10px;background:{SIDEBAR_BG};'
                f'border-radius:8px;font-size:11px;font-weight:500;color:{pnl_color};'
                f'font-family:{FONT};">{qty} shares = ${abs(total):,.2f} {pnl_label}</span>')

        st.markdown(f"""
        <div style="{CARD} padding:16px 20px;border-left:4px solid {pnl_color};">
            <div style="{LABEL}">My Position</div>
            <div style="margin-top:6px;font-family:{FONT};">
                <span style="font-size:12px;color:{TEXT_SEC};">Avg Cost </span>
                <span style="font-size:14px;font-weight:600;color:{TEXT};">${cost_basis:.2f}</span>
                <span style="font-size:12px;color:{TEXT_SEC};margin:0 6px;">\u2192 Current</span>
                <span style="font-size:14px;font-weight:600;color:{TEXT};">${current_price:.2f}</span>
            </div>
            <div style="margin-top:10px;font-family:{FONT};">
                <span style="font-size:13px;color:{TEXT};">If you sold now, you would {action_word} approx. </span>
                <span style="font-size:13px;font-weight:700;color:{pnl_color};">${abs(pnl_dollar):.2f}/share</span>
                <span style="font-size:13px;font-weight:600;color:{pnl_color};"> ({pnl_pct:+.1f}%)</span>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">{examples}</div>
            <div style="font-size:10px;color:{MUTED};line-height:1.5;font-family:{FONT};
                        margin-top:12px;font-style:italic;">
                Based on your entered average cost. Actual P&amp;L depends on shares held
                and acquisition prices. Does not account for fees, taxes, or dividends.
            </div>
        </div>""", unsafe_allow_html=True)
