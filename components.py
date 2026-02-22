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
        border: 1px solid #D0E8EA;
        border-radius: 10px;
        box-shadow: 0px 2px 4px rgba(0, 151, 167, 0.08);
        cursor: help;
        transition: all 300ms ease-in-out;
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
    """Render a large badge-style card (like market regime)."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    return f"""
    <div style='
        text-align: center;
        padding: 24px;
        background: {bg};
        border: 1px solid #D0E8EA;
        border-radius: 12px;
        box-shadow: 0px 2px 4px rgba(0, 151, 167, 0.08);
        cursor: help;
    ' title='{tooltip}'>
        <div style='font-size: 48px; margin-bottom: 8px;'>{icon}</div>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #5A7D82;
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
        border: 1px solid #D0E8EA;
        border-radius: 8px;
        box-shadow: 0px 2px 4px rgba(0, 151, 167, 0.08);
        margin-bottom: 8px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #5A7D82;
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
    """Return common chart layout settings with teal-themed fonts."""
    CHART_FONT_COLOR = "#1A3C40"
    CHART_AXIS_COLOR = "#37616A"
    CHART_GRID_COLOR = "#D0E8EA"

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
        legend=dict(
            font=dict(color=CHART_FONT_COLOR),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        hovermode="x unified",
    )


def render_hero_card(label, value, subtitle="", status="neutral"):
    """Render a large gradient hero card for BUY/HOLD/SELL recommendations."""
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
        padding: 28px 20px;
        background: {gradient};
        border-radius: 14px;
        box-shadow: 0px 4px 16px rgba(0, 151, 167, 0.2);
        cursor: help;
    ' title='{subtitle}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: rgba(255,255,255,0.85);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 48px;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.1;
        '>{value}</div>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 11px;
            color: rgba(255,255,255,0.7);
            margin-top: 6px;
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
        padding: 20px;
        background: #FFFFFF;
        border: 2px solid {border_color};
        border-radius: 12px;
        box-shadow: 0px 2px 8px rgba(0, 151, 167, 0.1);
        cursor: help;
        transition: all 300ms ease-in-out;
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
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 36px;
            font-weight: 600;
            color: {color};
        '>{value}</div>
    </div>
    """

