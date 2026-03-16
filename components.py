# =============================================================================
# COMPONENTS.PY - Reusable UI components for the dashboard
# =============================================================================

# =============================================================================
# DESIGN TOKENS (mirrored from Dash app)
# =============================================================================

FONTS = {
    "primary": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
}

COLORS = {
    "background": "#F4F7F9",
    "card": "#FFFFFF",
    "border": "#E8EDF2",
    "sidebar": "#F8FAFB",
    "teal": "#0097A7",
    "teal_dark": "#005662",
    "coral": "#FF6B6B",
    "heading": "#0F172A",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#F43F5E",
    "danger_red": "#EF4444",
    "info": "#0097A7",
    "neutral": "#1E293B",
    "muted": "#94A3B8",
}

SHADOWS = {
    "sm": "0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)",
    "md": "0 4px 12px rgba(0, 0, 0, 0.05), 0 1px 4px rgba(0, 0, 0, 0.03)",
}

FONT = FONTS["primary"]


def get_status_color(status_type):
    """Get the appropriate color for a status type."""
    colors = {
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger": COLORS["danger"],
        "info": COLORS["info"],
        "neutral": COLORS["neutral"],
        "muted": COLORS["muted"],
    }
    return colors.get(status_type, colors["neutral"])


def get_status_bg(status_type):
    """Get the appropriate background color for a status type."""
    bgs = {
        "success": "rgba(16, 185, 129, 0.08)",
        "warning": "rgba(245, 158, 11, 0.08)",
        "danger": "rgba(244, 63, 94, 0.08)",
        "info": "rgba(0, 151, 167, 0.08)",
        "neutral": "#FFFFFF",
    }
    return bgs.get(status_type, bgs["neutral"])


def render_metric_card(label, value, tooltip="", status="neutral", size="normal"):
    """Render a styled metric card with the new design system."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else COLORS["card"]

    if size == "large":
        value_style = f"font-family: {FONT}; font-size: 28px; font-weight: 500;"
    elif size == "medium":
        value_style = f"font-family: {FONT}; font-size: 22px; font-weight: 500;"
    else:
        value_style = f"font-family: {FONT}; font-size: 18px; font-weight: 500;"

    return f"""
    <div style='
        text-align: center;
        padding: 14px 16px;
        background: {bg};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        box-shadow: {SHADOWS["sm"]};
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: {FONT};
            font-size: 11px;
            font-weight: 600;
            color: {COLORS["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        '>{label}</div>
        <div style='{value_style} color: {color}; letter-spacing: -0.01em;'>{value}</div>
    </div>
    """


def render_badge_card(label, value, icon="", tooltip="", status="neutral"):
    """Render a badge-style card with horizontal layout."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else COLORS["card"]

    return f"""
    <div style='
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 16px;
        background: {bg};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        box-shadow: {SHADOWS["sm"]};
        cursor: help;
    ' title='{tooltip}'>
        <div style='font-size: 22px; flex-shrink: 0;'>{icon}</div>
        <div>
            <div style='
                font-family: {FONT};
                font-size: 11px;
                font-weight: 600;
                color: {COLORS["text_secondary"]};
                text-transform: uppercase;
                letter-spacing: 0.06em;
                margin-bottom: 2px;
            '>{label}</div>
            <div style='
                font-family: {FONT};
                font-size: 18px;
                font-weight: 500;
                color: {color};
            '>{value}</div>
        </div>
    </div>
    """


def render_compact_card(label, value, tooltip="", status="neutral"):
    """Render a compact metric card for dense layouts."""
    color = get_status_color(status)

    return f"""
    <div style='
        text-align: center;
        padding: 8px 12px;
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        box-shadow: {SHADOWS["sm"]};
        margin-bottom: 6px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: {FONT};
            font-size: 11px;
            font-weight: 600;
            color: {COLORS["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 4px;
        '>{label}</div>
        <div style='
            font-family: {FONT};
            font-size: 17px;
            font-weight: 500;
            color: {color};
        '>{value}</div>
    </div>
    """


def format_mcap(val):
    """Format market cap for display."""
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    elif val >= 1e9:
        return f"${val/1e9:.1f}B"
    elif val >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


def render_hero_card(label, value, subtitle="", status="neutral"):
    """Render a gradient hero card for BUY/HOLD/SELL recommendations."""
    gradients = {
        "success": "linear-gradient(135deg, #0097A7 0%, #00BCD4 100%)",
        "warning": "linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)",
        "danger": "linear-gradient(135deg, #FF6B6B 0%, #F43F5E 100%)",
        "neutral": "linear-gradient(135deg, #334155 0%, #475569 100%)",
    }
    gradient = gradients.get(status, gradients["neutral"])

    return f"""
    <div style='
        text-align: center;
        padding: 16px 20px;
        background: {gradient};
        border-radius: 14px;
        box-shadow: {SHADOWS["md"]};
        cursor: help;
    ' title='{subtitle}'>
        <div style='
            font-family: {FONT};
            font-size: 11px;
            font-weight: 600;
            color: rgba(255,255,255,0.8);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        '>{label}</div>
        <div style='
            font-family: {FONT};
            font-size: 32px;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.1;
            letter-spacing: -0.02em;
        '>{value}</div>
        <div style='
            font-family: {FONT};
            font-size: 11px;
            color: rgba(255,255,255,0.65);
            margin-top: 4px;
        '>{subtitle}</div>
    </div>
    """


def render_accent_card(label, value, tooltip="", status="neutral", border_color=None):
    """Render an accent-bordered card for confidence/score metrics."""
    color = get_status_color(status)
    if border_color is None:
        border_color = COLORS["teal"] if status in ("info", "neutral") else color

    return f"""
    <div style='
        text-align: center;
        padding: 14px 16px;
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-left: 3px solid {border_color};
        border-radius: 12px;
        box-shadow: {SHADOWS["sm"]};
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: {FONT};
            font-size: 11px;
            font-weight: 600;
            color: {COLORS["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        '>{label}</div>
        <div style='
            font-family: {FONT};
            font-size: 22px;
            font-weight: 600;
            color: {color};
        '>{value}</div>
    </div>
    """


def render_metrics_strip(metrics):
    """Render a flat horizontal strip of label:value pairs (TradingView-style).

    Parameters:
        metrics: list of dicts with keys: label, value, color (optional), tooltip (optional)
    """
    items_html = ""
    for i, m in enumerate(metrics):
        label = m.get("label", "")
        value = m.get("value", "")
        color = m.get("color", COLORS["text_primary"])
        tooltip = m.get("tooltip", "")
        divider = f'<div style="width:1px;background:{COLORS["border"]};align-self:stretch;margin:0 12px;"></div>' if i > 0 else ""
        items_html += f"""{divider}
        <div style="flex:1;min-width:0;text-align:center;cursor:help;" title="{tooltip}">
            <div style="font-family:{FONT};font-size:11px;font-weight:600;
                        color:{COLORS["text_secondary"]};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{label}</div>
            <div style="font-family:{FONT};font-size:15px;font-weight:500;
                        color:{color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{value}</div>
        </div>"""

    return f"""
    <div style="display:flex;align-items:center;background:{COLORS["card"]};border:1px solid {COLORS["border"]};
                border-radius:12px;padding:10px 16px;box-shadow:{SHADOWS["sm"]};">
        {items_html}
    </div>
    """
