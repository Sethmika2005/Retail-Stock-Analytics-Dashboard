# News tab — feed with sentiment classification

import datetime as dt
import streamlit as st
from models import classify_headline_sentiment
from styles import render_metrics_strip, get_status_color, TEAL, CORAL, MUTED, CARD_BG


SENTIMENT_COLORS = {"Positive": TEAL, "Negative": CORAL, "Neutral": MUTED}


def render(news_items):
    st.subheader("Recent News")
    st.caption("Latest headlines from Finnhub. Read articles to form your own opinion on sentiment.")

    if not news_items:
        st.info("No recent news available for this ticker.")
        return

    # Sentiment counts
    sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for item in news_items[:15]:
        sentiments[classify_headline_sentiment(item.get("headline", ""))] += 1

    total = sum(sentiments.values())
    if total > 0:
        strip = render_metrics_strip([
            {"label": "Positive", "value": str(sentiments["Positive"]),
             "color": get_status_color("success"), "tooltip": "Positive sentiment headlines"},
            {"label": "Neutral", "value": str(sentiments["Neutral"]),
             "color": "#1E293B", "tooltip": "Neutral sentiment headlines"},
            {"label": "Negative", "value": str(sentiments["Negative"]),
             "color": get_status_color("danger"), "tooltip": "Negative sentiment headlines"},
        ])
        st.html(strip)

        dominant = max(sentiments, key=sentiments.get)
        if dominant == "Positive":
            st.caption(f"News sentiment is mostly positive — {sentiments['Positive']} of {total} headlines are favorable.")
        elif dominant == "Negative":
            st.caption(f"News sentiment is mostly negative — {sentiments['Negative']} of {total} headlines are unfavorable.")
        else:
            st.caption(f"News sentiment is mixed — no dominant positive or negative tone across {total} headlines.")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # News cards
    for item in news_items[:15]:
        headline = item.get("headline", "Untitled")
        source = item.get("source", "Unknown")
        url = item.get("url", "#")
        ts = item.get("datetime")
        when = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "N/A"

        sentiment = classify_headline_sentiment(headline)
        border = SENTIMENT_COLORS.get(sentiment, MUTED)

        summary = item.get("summary", "")
        truncated = (summary[:200] + "...") if len(summary) > 200 else (summary or "No description available.")
        is_italic = "italic" if not summary else "normal"

        st.markdown(f"""
        <div style="background:{CARD_BG};border-left:4px solid {border};border-radius:6px;
                    padding:10px 14px;margin-bottom:6px;">
            <a href="{url}" target="_blank" style="font-family:'Inter',Arial,sans-serif;
                font-size:15px;font-weight:600;color:#1E293B;text-decoration:none;
                line-height:1.4;">{headline}</a>
            <div style="font-size:13px;color:#64748B;margin-top:6px;line-height:1.4;
                        font-style:{is_italic};">{truncated}</div>
            <div style="font-size:12px;color:#64748B;margin-top:8px;">{source} &middot; {when}</div>
        </div>
        """, unsafe_allow_html=True)
