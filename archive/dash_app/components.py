# =============================================================================
# COMPONENTS.PY - Reusable Dash HTML components
# =============================================================================

from dash import html

# =============================================================================
# DESIGN TOKENS
# =============================================================================

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

FONTS = {
    "primary": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
}

SHADOWS = {
    "sm": "0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)",
    "md": "0 4px 12px rgba(0, 0, 0, 0.05), 0 1px 4px rgba(0, 0, 0, 0.03)",
    "lg": "0 8px 24px rgba(0, 0, 0, 0.06), 0 2px 8px rgba(0, 0, 0, 0.03)",
}

STATUS_COLORS = {
    "success": COLORS["success"],
    "warning": COLORS["warning"],
    "danger": COLORS["danger"],
    "info": COLORS["info"],
    "neutral": COLORS["neutral"],
    "muted": COLORS["muted"],
}

STATUS_BGS = {
    "success": "rgba(16, 185, 129, 0.08)",
    "warning": "rgba(245, 158, 11, 0.08)",
    "danger": "rgba(244, 63, 94, 0.08)",
    "info": "rgba(0, 151, 167, 0.08)",
    "neutral": "#FFFFFF",
}


def get_status_color(status):
    return STATUS_COLORS.get(status, COLORS["neutral"])


def get_status_bg(status):
    return STATUS_BGS.get(status, "#FFFFFF")


# =============================================================================
# CARD COMPONENTS
# =============================================================================

CARD_STYLE = {
    "background": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "14px",
    "padding": "16px 20px",
    "boxShadow": SHADOWS["sm"],
}

LABEL_STYLE = {
    "fontFamily": FONTS["primary"],
    "fontSize": "11px",
    "fontWeight": 600,
    "color": COLORS["text_secondary"],
    "textTransform": "uppercase",
    "letterSpacing": "0.06em",
    "marginBottom": "8px",
}

SNAPPY_STYLE = {
    "fontFamily": FONTS["primary"],
    "fontSize": "13px",
    "color": COLORS["text_secondary"],
    "lineHeight": "1.6",
    "marginTop": "4px",
}


def card(children, **style_overrides):
    """Base card wrapper."""
    style = {**CARD_STYLE, **style_overrides}
    return html.Div(children, style=style)


def label(text):
    """Section label (uppercase, muted)."""
    return html.Div(text, style=LABEL_STYLE)


def snappy(text):
    """One-liner insight text."""
    return html.Div(text, style=SNAPPY_STYLE)


def section_divider():
    """Horizontal thin line separator."""
    return html.Div(style={
        "height": "1px",
        "background": COLORS["border"],
        "margin": "16px 0",
    })


def section_header(text):
    """Section heading with teal left border."""
    return html.Div(
        html.H3(text, style={
            "margin": "0",
            "padding": "0",
            "fontFamily": FONTS["primary"],
            "fontWeight": 600,
            "color": COLORS["heading"],
            "fontSize": "17px",
            "letterSpacing": "-0.01em",
        }),
        style={
            "borderLeft": f"3px solid {COLORS['teal']}",
            "paddingLeft": "12px",
            "margin": "16px 0 8px 0",
        },
    )


def spacer(height=10):
    """Vertical spacer."""
    return html.Div(style={"height": f"{height}px"})


# =============================================================================
# METRIC CARDS
# =============================================================================

def metric_card(label_text, value, status="neutral", size="normal", tooltip=""):
    """Centered metric card with colored value."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else COLORS["card"]

    font_sizes = {"large": "28px", "medium": "22px", "normal": "18px"}
    font_size = font_sizes.get(size, "18px")

    return html.Div(
        [
            html.Div(label_text, style=LABEL_STYLE),
            html.Div(value, style={
                "fontFamily": FONTS["primary"],
                "fontSize": font_size,
                "fontWeight": 500,
                "color": color,
                "letterSpacing": "-0.01em",
            }),
        ],
        style={
            "textAlign": "center",
            "padding": "14px 16px",
            "background": bg,
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "boxShadow": SHADOWS["sm"],
        },
        title=tooltip,
    )


def hero_card(label_text, value, subtitle="", status="neutral"):
    """Gradient hero card for BUY/HOLD/SELL."""
    gradients = {
        "success": "linear-gradient(135deg, #0097A7 0%, #00BCD4 100%)",
        "warning": "linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)",
        "danger": "linear-gradient(135deg, #FF6B6B 0%, #F43F5E 100%)",
        "neutral": "linear-gradient(135deg, #334155 0%, #475569 100%)",
    }
    gradient = gradients.get(status, gradients["neutral"])

    return html.Div(
        [
            html.Div(label_text, style={
                "fontFamily": FONTS["primary"], "fontSize": "11px", "fontWeight": 600,
                "color": "rgba(255,255,255,0.8)", "textTransform": "uppercase",
                "letterSpacing": "0.08em", "marginBottom": "6px",
            }),
            html.Div(value, style={
                "fontFamily": FONTS["primary"], "fontSize": "32px", "fontWeight": 700,
                "color": "#FFFFFF", "lineHeight": "1.1", "letterSpacing": "-0.02em",
            }),
            html.Div(subtitle, style={
                "fontFamily": FONTS["primary"], "fontSize": "11px",
                "color": "rgba(255,255,255,0.65)", "marginTop": "4px",
            }),
        ],
        style={
            "textAlign": "center",
            "padding": "16px 20px",
            "background": gradient,
            "borderRadius": "14px",
            "boxShadow": SHADOWS["md"],
        },
        title=subtitle,
    )


def accent_card(label_text, value, status="neutral", border_color=None, tooltip=""):
    """Card with teal left-accent border."""
    color = get_status_color(status)
    if border_color is None:
        border_color = COLORS["teal"] if status in ("info", "neutral") else color

    return html.Div(
        [
            html.Div(label_text, style={**LABEL_STYLE, "marginBottom": "6px"}),
            html.Div(value, style={
                "fontFamily": FONTS["primary"], "fontSize": "22px",
                "fontWeight": 600, "color": color,
            }),
        ],
        style={
            "textAlign": "center",
            "padding": "14px 16px",
            "background": COLORS["card"],
            "border": f"1px solid {COLORS['border']}",
            "borderLeft": f"3px solid {border_color}",
            "borderRadius": "12px",
            "boxShadow": SHADOWS["sm"],
        },
        title=tooltip,
    )


def badge_card(label_text, value, icon="", status="neutral", tooltip=""):
    """Horizontal badge card with icon."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else COLORS["card"]

    return html.Div(
        [
            html.Span(icon, style={"fontSize": "22px", "flexShrink": 0}) if icon else None,
            html.Div([
                html.Div(label_text, style={**LABEL_STYLE, "marginBottom": "2px"}),
                html.Div(value, style={
                    "fontFamily": FONTS["primary"], "fontSize": "18px",
                    "fontWeight": 500, "color": color,
                }),
            ]),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "10px",
            "padding": "14px 16px",
            "background": bg,
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px",
            "boxShadow": SHADOWS["sm"],
        },
        title=tooltip,
    )


# =============================================================================
# METRICS STRIP
# =============================================================================

def metrics_strip(metrics):
    """Horizontal strip of label:value pairs.

    Args:
        metrics: list of dicts with keys: label, value, color (optional), tooltip (optional)
    """
    items = []
    for i, m in enumerate(metrics):
        if i > 0:
            items.append(html.Div(style={
                "width": "1px", "background": COLORS["border"],
                "alignSelf": "stretch", "margin": "0 12px",
            }))
        color = m.get("color", COLORS["text_primary"])
        items.append(html.Div(
            [
                html.Div(m["label"], style={
                    "fontFamily": FONTS["primary"], "fontSize": "11px", "fontWeight": 500,
                    "color": COLORS["text_secondary"], "textTransform": "uppercase",
                    "letterSpacing": "0.04em", "marginBottom": "2px",
                    "whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis",
                }),
                html.Div(m["value"], style={
                    "fontFamily": FONTS["primary"], "fontSize": "15px", "fontWeight": 500,
                    "color": color, "whiteSpace": "nowrap", "overflow": "hidden",
                    "textOverflow": "ellipsis",
                }),
            ],
            style={"flex": 1, "minWidth": 0, "textAlign": "center"},
            title=m.get("tooltip", ""),
        ))

    return html.Div(items, style={
        "display": "flex",
        "alignItems": "center",
        "background": COLORS["card"],
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "12px",
        "padding": "10px 16px",
        "boxShadow": SHADOWS["sm"],
    })


# =============================================================================
# PROGRESS BAR
# =============================================================================

def progress_bar(label_text, score, color=None):
    """Horizontal progress bar with label and score."""
    if color is None:
        color = COLORS["teal"]
    pct = max(0, min(100, score))

    return html.Div(
        [
            html.Div(
                [
                    html.Span(label_text, style={
                        "fontFamily": FONTS["primary"], "fontSize": "12px",
                        "color": COLORS["text_secondary"], "fontWeight": 450,
                    }),
                    html.Span(f"{pct:.0f}", style={
                        "fontWeight": 600, "color": COLORS["text_primary"],
                        "fontFamily": FONTS["primary"], "fontSize": "12px",
                    }),
                ],
                style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"},
            ),
            html.Div(
                html.Div(style={
                    "width": f"{pct}%", "height": "100%",
                    "background": color, "borderRadius": "6px",
                    "transition": "width 0.4s ease",
                }),
                style={
                    "background": "#F1F5F9", "borderRadius": "6px",
                    "height": "6px", "overflow": "hidden",
                },
            ),
        ],
        style={"marginBottom": "12px"},
    )


# =============================================================================
# HELPERS
# =============================================================================

def format_mcap(val):
    if val >= 1e12:
        return f"${val / 1e12:.2f}T"
    elif val >= 1e9:
        return f"${val / 1e9:.1f}B"
    elif val >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"


def signal_row(label_text, value, color):
    """Key-value row for signal cards."""
    return html.Div(
        [
            html.Span(label_text, style={"color": COLORS["text_secondary"], "fontWeight": 450}),
            html.Span(value, style={"color": color, "fontWeight": 600}),
        ],
        style={"display": "flex", "justifyContent": "space-between", "marginTop": "8px",
               "fontSize": "12.5px"},
    )
