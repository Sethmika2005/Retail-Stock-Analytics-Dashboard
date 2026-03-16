# =============================================================================
# NEWS TAB - News feed and sentiment analysis display
# =============================================================================

import datetime as dt
import streamlit as st
from models import classify_headline_sentiment
from components import render_metrics_strip, get_status_color


def render(news_items):
    """Render the News & Sentiment tab content."""
    st.subheader("Recent News")
    st.caption("Latest headlines from Finnhub. Read articles to form your own opinion on sentiment.")

    if not news_items:
        st.info("No recent news available for this ticker.")
        return

    # Count sentiment
    sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for item in news_items[:15]:
        sentiment = classify_headline_sentiment(item.get("headline", ""))
        sentiments[sentiment] += 1

    # Display sentiment summary as a single strip
    total = sum(sentiments.values())
    if total > 0:
        _strip_html = render_metrics_strip([
            {"label": "Positive", "value": str(sentiments["Positive"]), "color": get_status_color("success"), "tooltip": "Positive sentiment headlines"},
            {"label": "Neutral", "value": str(sentiments["Neutral"]), "color": "#1E293B", "tooltip": "Neutral sentiment headlines"},
            {"label": "Negative", "value": str(sentiments["Negative"]), "color": get_status_color("danger"), "tooltip": "Negative sentiment headlines"},
        ])
        try:
            st.html(_strip_html)
        except Exception:
            st.markdown(_strip_html, unsafe_allow_html=True)

        # One-liner sentiment summary
        dominant = max(sentiments, key=sentiments.get)
        dominant_pct = sentiments[dominant] / total * 100
        if dominant == "Positive":
            st.caption(f"News sentiment is mostly positive — {sentiments['Positive']} of {total} headlines are favorable.")
        elif dominant == "Negative":
            st.caption(f"News sentiment is mostly negative — {sentiments['Negative']} of {total} headlines are unfavorable.")
        else:
            st.caption(f"News sentiment is mixed — no dominant positive or negative tone across {total} headlines.")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Sentiment to border colour mapping
    sentiment_colors = {
        "Positive": "#0097A7",   # teal
        "Negative": "#FF6B6B",   # coral
        "Neutral": "#64748B",    # muted
    }

    # Display news items as styled cards
    for item in news_items[:15]:
        headline = item.get("headline", "Untitled")
        source = item.get("source", "Unknown")
        url = item.get("url", "#")
        timestamp = item.get("datetime")
        summary = item.get("summary", "")

        when = dt.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"
        sentiment = classify_headline_sentiment(headline)
        border_color = sentiment_colors.get(sentiment, "#64748B")

        summary_html = ""
        if summary:
            truncated = summary[:200] + "..." if len(summary) > 200 else summary
            summary_html = f'<div style="font-size: 13px; color: #64748B; margin-top: 6px; line-height: 1.4;">{truncated}</div>'

        st.markdown(f"""
        <div style="
            background: #FFFFFF;
            border-left: 4px solid {border_color};
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 6px;
        ">
            <a href="{url}" target="_blank" style="
                font-family: 'Inter', Arial, sans-serif;
                font-size: 15px;
                font-weight: 600;
                color: #1E293B;
                text-decoration: none;
                line-height: 1.4;
            ">{headline}</a>
            {summary_html}
            <div style="font-size: 12px; color: #64748B; margin-top: 8px;">{source} &middot; {when}</div>
        </div>
        """, unsafe_allow_html=True)
