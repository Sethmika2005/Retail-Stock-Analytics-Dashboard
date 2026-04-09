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
