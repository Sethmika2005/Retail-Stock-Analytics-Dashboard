# =============================================================================
# COMPONENTS.PY - Reusable UI components for the dashboard
# =============================================================================


def get_status_color(status_type):
    """Get the appropriate color for a status type."""
    colors = {
        "success": "#10B981",  # Emerald - Bull/BUY/Low risk
        "warning": "#F59E0B",  # Amber - Sideways/HOLD/Medium risk
        "danger": "#F43F5E",   # Rose - Bear/SELL/High risk
        "info": "#0EA5E9",     # Sky - Info accents
        "neutral": "#37322F",  # Primary text
        "muted": "#605A57",    # Secondary text
    }
    return colors.get(status_type, colors["neutral"])


def get_status_bg(status_type):
    """Get the appropriate background color for a status type."""
    bgs = {
        "success": "rgba(16, 185, 129, 0.1)",
        "warning": "rgba(245, 158, 11, 0.1)",
        "danger": "#FFE4E6",
        "info": "rgba(14, 165, 233, 0.1)",
        "neutral": "#FFFFFF",
    }
    return bgs.get(status_type, bgs["neutral"])


def render_metric_card(label, value, tooltip="", status="neutral", size="normal"):
    """Render a styled metric card with the new design system."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    if size == "large":
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 42px; font-weight: 400;"
    elif size == "medium":
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 32px; font-weight: 400;"
    else:
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 24px; font-weight: 400;"

    return f"""
    <div style='
        text-align: center;
        padding: 20px;
        background: {bg};
        border: 1px solid #E0DEDB;
        border-radius: 10px;
        box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
        cursor: help;
        transition: all 300ms ease-in-out;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #605A57;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        '>{label}</div>
        <div style='{value_style} color: {color};'>{value}</div>
    </div>
    """


def render_badge_card(label, value, icon="", tooltip="", status="neutral"):
    """Render a large badge-style card (like market regime)."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    return f"""
    <div style='
        text-align: center;
        padding: 24px;
        background: {bg};
        border: 1px solid #E0DEDB;
        border-radius: 12px;
        box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
        cursor: help;
    ' title='{tooltip}'>
        <div style='font-size: 48px; margin-bottom: 8px;'>{icon}</div>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #605A57;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 28px;
            font-weight: 400;
            color: {color};
        '>{value}</div>
    </div>
    """


def render_compact_card(label, value, tooltip="", status="neutral"):
    """Render a compact metric card for dense layouts."""
    color = get_status_color(status)

    return f"""
    <div style='
        text-align: center;
        padding: 16px;
        background: #FFFFFF;
        border: 1px solid #E0DEDB;
        border-radius: 8px;
        box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
        margin-bottom: 8px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #605A57;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 22px;
            font-weight: 400;
            color: {color};
        '>{value}</div>
    </div>
    """


def format_large_number(value):
    """Format large numbers with K, M, B, T suffixes."""
    if value is None:
        return "N/A"
    try:
        value = float(value)
        if abs(value) >= 1e12:
            return f"${value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_mcap(val):
    """Format market cap for display."""
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    elif val >= 1e9:
        return f"${val/1e9:.1f}B"
    elif val >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


def get_chart_layout_defaults():
    """Return common chart layout settings with dark grey fonts."""
    CHART_FONT_COLOR = "#4A4A4A"
    CHART_AXIS_COLOR = "#4A4A4A"
    CHART_GRID_COLOR = "rgba(74, 74, 74, 0.15)"

    return dict(
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
        title_font=dict(color=CHART_FONT_COLOR, size=14),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont=dict(color=CHART_AXIS_COLOR),
            title=dict(font=dict(color=CHART_AXIS_COLOR)),
            gridcolor=CHART_GRID_COLOR,
            linecolor=CHART_GRID_COLOR,
        ),
        yaxis=dict(
            tickfont=dict(color=CHART_AXIS_COLOR),
            title=dict(font=dict(color=CHART_AXIS_COLOR)),
            gridcolor=CHART_GRID_COLOR,
            linecolor=CHART_GRID_COLOR,
        ),
        legend=dict(font=dict(color=CHART_FONT_COLOR)),
    )
