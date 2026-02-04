# =============================================================================
# NEWS TAB - News feed and sentiment analysis display
# =============================================================================

import datetime as dt
import streamlit as st
from models import classify_headline_sentiment


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

    # Display sentiment summary
    total = sum(sentiments.values())
    if total > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Positive", sentiments["Positive"], delta=None)
        with col2:
            st.metric("Neutral", sentiments["Neutral"], delta=None)
        with col3:
            st.metric("Negative", sentiments["Negative"], delta=None)
        st.markdown("---")

    # Display news items
    for item in news_items[:15]:
        headline = item.get("headline", "Untitled")
        source = item.get("source", "Unknown")
        url = item.get("url", "#")
        timestamp = item.get("datetime")
        summary = item.get("summary", "")

        when = dt.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"
        sentiment = classify_headline_sentiment(headline)
        sentiment_icon = {"Positive": "🟢", "Negative": "🔴", "Neutral": "⚪"}.get(sentiment, "⚪")

        st.markdown(f"{sentiment_icon} **[{headline}]({url})**")
        if summary:
            st.caption(summary[:200] + "..." if len(summary) > 200 else summary)
        st.caption(f"{source} · {when}")
        st.markdown("---")
