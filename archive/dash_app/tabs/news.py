# =============================================================================
# NEWS TAB - News feed and sentiment analysis (Dash version)
# =============================================================================

import datetime as dt
from dash import html

from components import COLORS, FONTS, metrics_strip, section_divider, get_status_color
from models import classify_headline_sentiment


def render(stock_data):
    news_items = stock_data.get("news_items", [])

    children = [
        html.H3("Recent News", style={
            "fontFamily": FONTS["primary"], "fontWeight": 600,
            "color": COLORS["teal_dark"], "marginBottom": "4px",
        }),
        html.P("Latest headlines from Finnhub. Read articles to form your own opinion on sentiment.",
               style={"fontSize": "12px", "color": COLORS["text_secondary"], "marginBottom": "12px"}),
    ]

    if not news_items:
        children.append(html.Div("No recent news available for this ticker.",
                                  style={"padding": "20px", "color": COLORS["text_secondary"]}))
        return html.Div(children)

    # Sentiment counts
    sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for item in news_items[:15]:
        s = classify_headline_sentiment(item.get("headline", ""))
        sentiments[s] += 1

    total = sum(sentiments.values())
    if total > 0:
        children.append(metrics_strip([
            {"label": "Positive", "value": str(sentiments["Positive"]),
             "color": get_status_color("success")},
            {"label": "Neutral", "value": str(sentiments["Neutral"]),
             "color": COLORS["text_primary"]},
            {"label": "Negative", "value": str(sentiments["Negative"]),
             "color": get_status_color("danger")},
        ]))

        dominant = max(sentiments, key=sentiments.get)
        if dominant == "Positive":
            summary = f"News sentiment is mostly positive \u2014 {sentiments['Positive']} of {total} headlines are favorable."
        elif dominant == "Negative":
            summary = f"News sentiment is mostly negative \u2014 {sentiments['Negative']} of {total} headlines are unfavorable."
        else:
            summary = f"News sentiment is mixed \u2014 no dominant positive or negative tone across {total} headlines."

        children.append(html.P(summary, style={
            "fontSize": "12px", "color": COLORS["text_secondary"], "marginTop": "8px",
        }))
        children.append(section_divider())

    # News cards
    sentiment_border = {"Positive": COLORS["teal"], "Negative": COLORS["coral"], "Neutral": COLORS["text_secondary"]}

    for item in news_items[:15]:
        headline = item.get("headline", "Untitled")
        source = item.get("source", "Unknown")
        url = item.get("url", "#")
        timestamp = item.get("datetime")
        summary = item.get("summary", "")

        when = dt.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"
        sentiment = classify_headline_sentiment(headline)
        border_color = sentiment_border.get(sentiment, COLORS["text_secondary"])

        summary_el = []
        if summary:
            truncated = summary[:200] + "..." if len(summary) > 200 else summary
            summary_el = [html.Div(truncated, style={
                "fontSize": "13px", "color": COLORS["text_secondary"],
                "marginTop": "6px", "lineHeight": "1.4",
            })]

        children.append(html.Div(
            [
                html.A(headline, href=url, target="_blank", style={
                    "fontFamily": FONTS["primary"], "fontSize": "15px",
                    "fontWeight": 600, "color": COLORS["text_primary"],
                    "textDecoration": "none", "lineHeight": "1.4",
                }),
                *summary_el,
                html.Div(f"{source} \u00b7 {when}", style={
                    "fontSize": "12px", "color": COLORS["text_secondary"], "marginTop": "8px",
                }),
            ],
            style={
                "background": COLORS["card"],
                "borderLeft": f"4px solid {border_color}",
                "borderRadius": "6px",
                "padding": "10px 14px",
                "marginBottom": "6px",
            },
        ))

    return html.Div(children)
