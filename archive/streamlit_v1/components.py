# =============================================================================
# COMPONENTS.PY - Reusable UI components for the dashboard
# =============================================================================


def get_status_color(status_type):
    """Get the appropriate color for a status type."""
    colors = {
        "success": "#10B981",  # Emerald - Bull/BUY/Low risk
        "warning": "#F59E0B",  # Amber - Sideways/HOLD/Medium risk
        "danger": "#F43F5E",   # Rose - Bear/SELL/High risk
        "info": "#0097A7",     # Teal - Info accents
        "neutral": "#1A3C40",  # Primary text (dark teal-charcoal)
        "muted": "#5A7D82",    # Secondary text
    }
    return colors.get(status_type, colors["neutral"])


def get_status_bg(status_type):
    """Get the appropriate background color for a status type."""
    bgs = {
        "success": "rgba(16, 185, 129, 0.1)",
        "warning": "rgba(245, 158, 11, 0.1)",
        "danger": "#FFE4E6",
        "info": "rgba(0, 151, 167, 0.1)",
        "neutral": "#FFFFFF",
    }
    return bgs.get(status_type, bgs["neutral"])


def render_metric_card(label, value, tooltip="", status="neutral", size="normal"):
    """Render a styled metric card with the new design system."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    if size == "large":
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 28px; font-weight: 400;"
    elif size == "medium":
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 22px; font-weight: 400;"
    else:
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 18px; font-weight: 400;"

    return f"""
    <div style='
        text-align: center;
        padding: 10px 14px;
        background: {bg};
        border: 1px solid #D0E8EA;
        border-radius: 6px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #5A7D82;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        '>{label}</div>
        <div style='{value_style} color: {color};'>{value}</div>
    </div>
    """


def render_badge_card(label, value, icon="", tooltip="", status="neutral"):
    """Render a badge-style card with horizontal layout."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    return f"""
    <div style='
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        background: {bg};
        border: 1px solid #D0E8EA;
        border-radius: 6px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='font-size: 22px; flex-shrink: 0;'>{icon}</div>
        <div>
            <div style='
                font-family: Source Sans Pro, Arial, sans-serif;
                font-size: 12px;
                font-weight: 500;
                color: #5A7D82;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 2px;
            '>{label}</div>
            <div style='
                font-family: "Source Sans Pro", Arial, sans-serif;
                font-size: 18px;
                font-weight: 400;
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
        background: #FFFFFF;
        border: 1px solid #D0E8EA;
        border-radius: 6px;
        margin-bottom: 6px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #5A7D82;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 17px;
            font-weight: 400;
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
        "neutral": "linear-gradient(135deg, #1A3C40 0%, #37616A 100%)",
    }
    gradient = gradients.get(status, gradients["neutral"])

    return f"""
    <div style='
        text-align: center;
        padding: 12px 16px;
        background: {gradient};
        border-radius: 6px;
        cursor: help;
    ' title='{subtitle}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: rgba(255,255,255,0.85);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.1;
        '>{value}</div>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 11px;
            color: rgba(255,255,255,0.7);
            margin-top: 4px;
        '>{subtitle}</div>
    </div>
    """


def render_accent_card(label, value, tooltip="", status="neutral", border_color=None):
    """Render an accent-bordered card for confidence/score metrics."""
    color = get_status_color(status)
    if border_color is None:
        border_color = "#0097A7" if status in ("info", "neutral") else color

    return f"""
    <div style='
        text-align: center;
        padding: 10px 14px;
        background: #FFFFFF;
        border: 1px solid #D0E8EA;
        border-left: 3px solid {border_color};
        border-radius: 6px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #5A7D82;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
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
        color = m.get("color", "#1A3C40")
        tooltip = m.get("tooltip", "")
        divider = '<div style="width:1px;background:#D0E8EA;align-self:stretch;margin:0 12px;"></div>' if i > 0 else ""
        items_html += f"""{divider}
        <div style="flex:1;min-width:0;text-align:center;cursor:help;" title="{tooltip}">
            <div style="font-family:Source Sans Pro,Arial,sans-serif;font-size:11px;font-weight:500;
                        color:#5A7D82;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:2px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{label}</div>
            <div style="font-family:Source Sans Pro,Arial,sans-serif;font-size:15px;font-weight:500;
                        color:{color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{value}</div>
        </div>"""

    return f"""
    <div style="display:flex;align-items:center;background:#FFFFFF;border:1px solid #D0E8EA;
                border-radius:6px;padding:8px 14px;">
        {items_html}
    </div>
    """

