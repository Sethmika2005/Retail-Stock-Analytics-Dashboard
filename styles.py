import streamlit as st

# -- Design tokens --
FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
BG = "#F4F7F9"
CARD_BG = "#FFFFFF"
BORDER = "#E8EDF2"
TEAL = "#0097A7"
TEAL_DARK = "#005662"
CORAL = "#FF6B6B"
HEADING = "#0F172A"
TEXT = "#1E293B"
TEXT_SEC = "#64748B"
MUTED = "#94A3B8"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
DANGER_ROSE = "#F43F5E"
GRID = "#F1F5F9"
SHADOW = "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)"
SHADOW_MD = "0 4px 12px rgba(0,0,0,0.05), 0 1px 4px rgba(0,0,0,0.03)"
SIDEBAR_BG = "#F8FAFB"

# -- Reusable CSS fragments --
CARD = (
    f"background:{CARD_BG};border:1px solid {BORDER};border-radius:14px;"
    f"box-shadow:{SHADOW};"
)
CARD_PAD = CARD + "padding:18px 20px;"
LABEL = (
    f"font-family:{FONT};font-size:11px;font-weight:600;"
    f"color:{MUTED};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;"
)
EXPLAIN = (
    f"font-size:11px;color:{MUTED};line-height:1.4;margin-top:8px;font-weight:400;"
    f"font-family:{FONT};"
)


def inject_css():
    """Inject global CSS. Call once from app.py."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700&display=swap');

.stApp {
    background-color: #F4F7F9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
.main .block-container {
    max-width: 1200px !important;
    padding: 2rem 1rem !important;
    background-color: #F4F7F9 !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #F8FAFB !important;
    border-right: 1px solid #E8EDF2 !important;
}
[data-testid="stSidebar"] .stMarkdown {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 600 !important; color: #1E293B !important;
    font-size: 14px !important; text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px; background-color: transparent !important;
    border-bottom: 1px solid #E8EDF2 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important; color: #94A3B8 !important;
    background-color: transparent !important; border: none !important;
    padding: 10px 18px !important; letter-spacing: 0.01em !important;
}
.stTabs [aria-selected="true"] {
    color: #0097A7 !important; font-weight: 600 !important;
    border-bottom: 2px solid #0097A7 !important; background-color: transparent !important;
}

/* Headers */
h1 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 24px !important; font-weight: 700 !important;
    color: #0F172A !important; letter-spacing: -0.03em !important;
}
h2, h3 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 600 !important; color: #0F172A !important;
}
p, span { color: #1E293B; }
.muted { color: #94A3B8 !important; }

/* Metrics */
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E8EDF2; border-radius: 12px;
    padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
}
[data-testid="stMetricLabel"] { color: #64748B !important; }
[data-testid="stMetricValue"] { color: #1E293B !important; }
[data-testid="stMetricDelta"] { color: #1E293B !important; }
[data-testid="stCaptionContainer"] { color: #64748B !important; }
.stCaption, small { color: #64748B !important; }

/* Progress bar */
[data-testid="stProgress"] > div > div { background-color: #F1F5F9 !important; }
[data-testid="stProgress"] > div > div > div { background-color: #0097A7 !important; }

/* Expander */
[data-testid="stExpander"] { color: #1E293B !important; }
[data-testid="stExpander"] summary { color: #1E293B !important; }

/* Toggle */
[data-testid="stToggle"] label { color: #1E293B !important; font-weight: 500 !important; }
[data-testid="stToggle"] {
    background-color: #FFFFFF !important; border: 1.5px solid #CBD5E1 !important;
    border-radius: 12px !important; padding: 10px 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important; transition: border-color 150ms ease !important;
}
[data-testid="stToggle"]:hover { border-color: #0097A7 !important; }
[data-testid="stToggle"] > div { background-color: #FFFFFF !important; }

/* Buttons */
.stButton > button {
    background-color: #FFFFFF !important; color: #1E293B !important;
    border: 1px solid #E8EDF2 !important; border-radius: 12px !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 500 !important; padding: 8px 16px !important;
    transition: all 150ms ease !important;
}
.stButton > button:hover {
    background-color: #F4F7F9 !important; border-color: #0097A7 !important;
}
.stButton > button:active { background-color: #E8EDF2 !important; }
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background-color: #0097A7 !important; color: #FFFFFF !important;
    border: 1px solid #0097A7 !important;
}
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #00838F !important; border-color: #00838F !important;
}
[data-testid="stSidebar"] .stButton > button {
    background-color: #FFFFFF !important; color: #1E293B !important;
    border: 1px solid #E8EDF2 !important; width: 100% !important;
    font-size: 12px !important; padding: 6px 14px !important; min-height: 0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #F4F7F9 !important; border-color: #0097A7 !important;
}

/* Text */
[data-testid="stText"] { color: #1E293B !important; }
[data-testid="stMarkdownContainer"] { color: #1E293B !important; }
[data-testid="stMarkdownContainer"] p { color: #1E293B !important; }
[data-testid="stMarkdownContainer"] li { color: #1E293B !important; }

/* Card classes */
.metric-card {
    background: #FFFFFF; border: 1px solid #E8EDF2; border-radius: 14px;
    padding: 16px 20px; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
}
.card-label {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 11px; font-weight: 600; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;
}
.big-number {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 22px; font-weight: 500; color: #1E293B;
}
.status-success { color: #10B981 !important; }
.status-warning { color: #F59E0B !important; }
.status-danger { color: #F43F5E !important; }
.status-info { color: #0097A7 !important; }
.bg-success { background-color: rgba(16, 185, 129, 0.08) !important; }
.bg-warning { background-color: rgba(245, 158, 11, 0.08) !important; }
.bg-danger { background-color: rgba(244, 63, 94, 0.08) !important; }
.bg-info { background-color: rgba(0, 151, 167, 0.08) !important; }

/* Badge */
.badge {
    display: inline-block; padding: 3px 14px; border-radius: 20px;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
}

/* Spacing / dividers */
.section-gap { margin-top: 20px !important; }
.row-gap { margin-top: 10px !important; }
.section-divider { height: 1px; background: #E8EDF2; border: none; margin: 12px 0; }
.section-header {
    border-left: 3px solid #0097A7; padding-left: 12px; margin: 16px 0 8px 0;
}
.section-header h3 {
    margin: 0 !important; padding: 0 !important;
    font-size: 17px !important; letter-spacing: -0.01em !important;
}

/* Expander details */
.streamlit-expanderHeader {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important; color: #1E293B !important;
    background-color: #FFFFFF !important; border: 1px solid #E8EDF2 !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] {
    background-color: #FFFFFF !important; border: 1px solid #E8EDF2 !important;
    border-radius: 14px !important; padding: 0 !important;
}
[data-testid="stExpander"] details {
    background-color: #FFFFFF !important; border: 1px solid #E8EDF2 !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] summary {
    background-color: #FFFFFF !important; padding: 12px 16px !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: #FFFFFF !important; padding: 16px !important;
    border-top: 1px solid #E8EDF2 !important;
}

/* DataFrame, alerts */
.stDataFrame { border: 1px solid #E8EDF2 !important; border-radius: 14px !important; }
.stAlert {
    background-color: #F8FAFB !important; border: 1px solid #E8EDF2 !important;
    border-radius: 14px !important; color: #1E293B !important;
}

/* Sidebar inputs */
[data-testid="stSidebar"] [data-baseweb="select"] { background-color: #FFFFFF !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #FFFFFF !important; border-color: #E8EDF2 !important;
    border-radius: 10px !important; color: #1E293B !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg { color: #64748B !important; }
[data-testid="stSidebar"] [data-baseweb="input"] {
    background-color: #FFFFFF !important; border-color: #E8EDF2 !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] input {
    color: #1E293B !important; background-color: #FFFFFF !important;
}
[data-testid="stSidebar"] label {
    color: #1E293B !important; font-size: 13px !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] .stCheckbox label span { color: #1E293B !important; }
[data-testid="stSidebar"] hr { border-color: #E8EDF2 !important; margin: 16px 0 !important; }

/* Dropdowns */
[data-baseweb="popover"] { background-color: #FFFFFF !important; }
[data-baseweb="popover"] ul { background-color: #FFFFFF !important; }
[data-baseweb="popover"] li {
    color: #1E293B !important; background-color: #FFFFFF !important;
}
[data-baseweb="popover"] li:hover { background-color: #F4F7F9 !important; }
[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #E0F4F5 !important; color: #0097A7 !important;
}
[data-baseweb="menu"], [data-baseweb="menu"] > div, [data-baseweb="menu"] ul,
[data-baseweb="menu"] li, [role="listbox"], [role="listbox"] > div, [role="listbox"] li,
[role="option"], [data-baseweb="popover"] > div, [data-baseweb="popover"] > div > div,
[data-baseweb="popover"] > div > div > div, [data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [role="listbox"] {
    background-color: #FFFFFF !important; background: #FFFFFF !important;
    color: #1E293B !important;
}
[data-baseweb="menu"] li:hover, [role="listbox"] li:hover,
[role="option"]:hover {
    background-color: #F4F7F9 !important; background: #F4F7F9 !important;
}
[role="option"][aria-selected="true"] {
    background-color: #E0F4F5 !important; background: #E0F4F5 !important;
    color: #0097A7 !important;
}

/* Selectbox text */
[data-baseweb="select"] span { color: #1E293B !important; }
[data-baseweb="select"] div[data-testid="stMarkdownContainer"] p { color: #1E293B !important; }
[data-baseweb="select"] input { color: #1E293B !important; background-color: #FFFFFF !important; }

/* Plotly */
[data-testid="stPlotlyChart"] {
    border: none !important; box-shadow: none !important; background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# -- HTML helpers --

def badge_html(text, color):
    """Pill-shaped badge."""
    return (
        f'<span style="display:inline-block;padding:3px 14px;border-radius:20px;'
        f'background:{color};color:white;font-size:11px;font-weight:700;'
        f'font-family:{FONT};letter-spacing:0.04em;vertical-align:middle;">{text}</span>'
    )


def chart_layout(height=280):
    """Standard Plotly layout dict."""
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="white", paper_bgcolor="white",
        hovermode="x unified",
        font=dict(family=FONT, size=11, color=TEXT_SEC),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(size=11, color=TEXT),
        ),
    )


def chart_axes(fig, y_prefix="", x_category=False):
    """Apply standard axis styling to a Plotly figure."""
    xkw = dict(showgrid=False, showline=True, linecolor=BORDER,
               tickfont=dict(size=10, color=MUTED))
    if x_category:
        xkw["type"] = "category"
    fig.update_xaxes(**xkw)
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID,
        tickfont=dict(size=10, color=MUTED),
        tickprefix=y_prefix,
    )


def chart_card_bg(height=380):
    """White rounded background box that chart content sits on top of."""
    return (
        f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:14px;'
        f'box-shadow:{SHADOW};min-height:{height}px;margin-bottom:-{height - 10}px;"></div>'
    )


def chart_card_header(title, verdict_text, verdict_color):
    """Header row: uppercase label + verdict badge."""
    return (
        f'<div style="padding:8px 16px 4px 16px;">'
        f'<span style="{LABEL} font-size:14px;margin-right:10px;display:inline-block;'
        f'vertical-align:middle;">{title}</span>'
        f'{badge_html(verdict_text, verdict_color)}'
        f'</div>'
    )


def explanation_html(text):
    """Small muted text below a chart card."""
    return (
        f'<div style="font-size:11px;color:{MUTED};line-height:1.4;'
        f'font-family:{FONT};padding:0px 16px 12px 16px;margin-top:-12px;">{text}</div>'
    )


def progress_bar(label_text, score, color=TEAL):
    """Horizontal bar with label and numeric value."""
    pct = max(0, min(100, float(score)))
    return (
        f'<div style="margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-family:{FONT};font-size:12px;color:{TEXT_SEC};margin-bottom:3px;">'
        f'<span>{label_text}</span>'
        f'<span style="font-weight:600;color:{TEXT};">{pct:.0f}</span></div>'
        f'<div style="background:{GRID};border-radius:4px;height:6px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>'
        f'</div></div>'
    )


def signal_row(label_text, value, color):
    """Key-value row for signal cards."""
    return (
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;">'
        f'<span style="font-size:12px;color:{TEXT_SEC};font-family:{FONT};">{label_text}</span>'
        f'<span style="font-size:12px;font-weight:600;color:{color};'
        f'font-family:{FONT};">{value}</span></div>'
    )


def metric_tag(lbl, value, color):
    """Colored inline tag (e.g. "P/E 18.3")."""
    return (
        f'<span style="display:inline-block;padding:4px 12px;background:{SIDEBAR_BG};'
        f'border-radius:8px;margin-right:10px;margin-bottom:6px;">'
        f'<span style="font-size:11px;font-weight:500;color:{MUTED};margin-right:6px;'
        f'font-family:{FONT};">{lbl}</span>'
        f'<span style="font-size:12px;font-weight:600;color:{color};'
        f'font-family:{FONT};">{value}</span></span>'
    )


def get_status_color(status_type):
    """Map status keyword to hex color."""
    return {
        "success": SUCCESS, "warning": WARNING, "danger": DANGER,
        "info": TEAL, "neutral": TEXT, "muted": MUTED,
    }.get(status_type, TEXT)


def render_metrics_strip(metrics):
    """Horizontal label:value strip (TradingView-style)."""
    items = ""
    for i, m in enumerate(metrics):
        label = m.get("label", "")
        value = m.get("value", "")
        color = m.get("color", TEXT)
        tooltip = m.get("tooltip", "")
        divider = (
            f'<div style="width:1px;background:{BORDER};align-self:stretch;margin:0 12px;"></div>'
            if i > 0 else ""
        )
        items += (
            f'{divider}'
            f'<div style="flex:1;min-width:0;text-align:center;cursor:help;" title="{tooltip}">'
            f'<div style="font-family:{FONT};font-size:11px;font-weight:600;'
            f'color:{TEXT_SEC};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{label}</div>'
            f'<div style="font-family:{FONT};font-size:15px;font-weight:500;'
            f'color:{color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{value}</div>'
            f'</div>'
        )
    return (
        f'<div style="display:flex;align-items:center;background:{CARD_BG};'
        f'border:1px solid {BORDER};border-radius:12px;padding:10px 16px;'
        f'box-shadow:{SHADOW};">{items}</div>'
    )


def score_color(score):
    """Green/amber/red based on 0-100 score."""
    if score >= 60:
        return SUCCESS
    if score >= 40:
        return WARNING
    return CORAL


def metric_color(value, good, ok, higher_is_better=True):
    """Green/amber/red based on thresholds."""
    if value is None:
        return MUTED
    if higher_is_better:
        return SUCCESS if value >= good else WARNING if value >= ok else CORAL
    return SUCCESS if value <= good else WARNING if value <= ok else CORAL


def spacer(px=12):
    """Vertical spacer div."""
    return f'<div style="height:{px}px;"></div>'
