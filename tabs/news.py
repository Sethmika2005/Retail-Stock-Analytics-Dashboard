# =============================================================================
# NEWS TAB - News feed and sentiment analysis display
# =============================================================================

import datetime as dt
import streamlit as st
from models import classify_headline_sentiment
from components import render_metric_card


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

    # Display sentiment summary with styled cards
    total = sum(sentiments.values())
    if total > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(render_metric_card("Positive", str(sentiments["Positive"]), "Positive sentiment headlines", "success"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_metric_card("Neutral", str(sentiments["Neutral"]), "Neutral sentiment headlines", "neutral"), unsafe_allow_html=True)
        with col3:
            st.markdown(render_metric_card("Negative", str(sentiments["Negative"]), "Negative sentiment headlines", "danger"), unsafe_allow_html=True)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Sentiment to border colour mapping
    sentiment_colors = {
        "Positive": "#0097A7",   # teal
        "Negative": "#FF6B6B",   # coral
        "Neutral": "#5A7D82",    # muted
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
        border_color = sentiment_colors.get(sentiment, "#5A7D82")

        summary_html = ""
        if summary:
            truncated = summary[:200] + "..." if len(summary) > 200 else summary
            summary_html = f'<div style="font-size: 13px; color: #5A7D82; margin-top: 6px; line-height: 1.4;">{truncated}</div>'

        st.markdown(f"""
        <div style="
            background: #FFFFFF;
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            box-shadow: 0px 1px 4px rgba(0, 151, 167, 0.06);
        ">
            <a href="{url}" target="_blank" style="
                font-family: 'Source Sans Pro', Arial, sans-serif;
                font-size: 15px;
                font-weight: 600;
                color: #1A3C40;
                text-decoration: none;
                line-height: 1.4;
            ">{headline}</a>
            {summary_html}
            <div style="font-size: 12px; color: #5A7D82; margin-top: 8px;">{source} &middot; {when}</div>
        </div>
        """, unsafe_allow_html=True)
