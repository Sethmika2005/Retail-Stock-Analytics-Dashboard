# index.py - Main Streamlit application
# Run: streamlit run index.py

import streamlit as st
from data import load_data
from utils import (
    format_commas,
    format_large_number,
    format_percent,
    format_price,
    format_ratio,
)

st.set_page_config(page_title="Price & Financials", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.title("Settings")
    ticker = st.text_input(
        "Ticker",
        value="LSEG.L",
        help="Use exchange suffix if needed (e.g., LSEG.L for London)",
    ).strip()
    st.markdown("---")
    st.caption("Examples: AAPL, MSFT, GOOGL, LSEG.L, BP.L")

# --- Main content ---
st.title("Price & Financials")

if ticker:
    with st.spinner("Loading data..."):
        data = load_data(ticker)

    metrics = data.get("metrics", {})
    currency = metrics.get("currency", "USD")
    hist = data["hist"]

    # --- Header section ---
    st.subheader(f"{ticker.upper()}")
    if data["name"]:
        st.caption(f"{data['name']}")
    if metrics.get("sector") or metrics.get("industry"):
        st.caption(f"{metrics.get('sector', '')} | {metrics.get('industry', '')}")

    # --- Price & Change ---
    if hist is not None and not hist.empty:
        last_px = hist["Close"].iloc[-1]
        prev_close = metrics.get("prev_close")

        # Calculate daily change
        if prev_close:
            daily_change = last_px - prev_close
            daily_pct = (daily_change / prev_close) * 100
            delta_str = f"{daily_change:+,.2f} ({daily_pct:+.2f}%)"
        else:
            delta_str = None

        # Calculate YTD change
        ytd_start = hist[hist.index.year == hist.index[-1].year]
        if not ytd_start.empty:
            ytd_first = ytd_start["Close"].iloc[0]
            ytd_change = ((last_px - ytd_first) / ytd_first) * 100
            ytd_str = f"{ytd_change:+.2f}%"
        else:
            ytd_str = "N/A"

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric(
                label=f"Last Close ({currency})",
                value=f"{last_px:,.2f}",
                delta=delta_str,
            )
        with col2:
            st.metric(label="YTD Return", value=ytd_str)
        with col3:
            st.metric(
                label="52-Week Range",
                value=f"{format_price(metrics.get('52w_low'))} - {format_price(metrics.get('52w_high'))}",
            )

    st.markdown("---")

    # --- Key Metrics Dashboard ---
    st.subheader("Key Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("Market Cap", format_large_number(metrics.get("market_cap"), currency))
    with m2:
        st.metric("P/E (TTM)", format_ratio(metrics.get("pe_ratio")))
    with m3:
        st.metric("EPS (TTM)", format_price(metrics.get("eps"), currency))
    with m4:
        st.metric("Dividend Yield", format_percent(metrics.get("dividend_yield")))
    with m5:
        st.metric("Avg Volume", format_large_number(metrics.get("volume")))

    m6, m7, m8, m9, m10 = st.columns(5)
    with m6:
        st.metric("Forward P/E", format_ratio(metrics.get("forward_pe")))
    with m7:
        st.metric("50-Day Avg", format_price(metrics.get("50d_avg"), currency))
    with m8:
        st.metric("200-Day Avg", format_price(metrics.get("200d_avg"), currency))
    with m9:
        st.metric("Open", format_price(metrics.get("open"), currency))
    with m10:
        st.metric("Prev Close", format_price(metrics.get("prev_close"), currency))

    st.markdown("---")

    # --- Price Chart ---
    if hist is None or hist.empty:
        st.error("No price history returned. Check the ticker or exchange suffix.")
    else:
        st.subheader("5-Year Daily Close")
        st.line_chart(hist["Close"])

        st.download_button(
            "Download 5Y Price CSV",
            data=hist.to_csv(index=True).encode("utf-8"),
            file_name=f"{ticker.upper()}_5y_daily_close.csv",
            mime="text/csv",
        )

    # --- Financial Statements ---
    st.markdown("---")
    st.subheader("Latest Annual Financial Statements")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"**Income Statement**  \n_Period: {data['inc_period']}_")
        if data["inc"] is None or data["inc"].empty:
            st.info("Not available.")
        else:
            st.dataframe(format_commas(data["inc"]), use_container_width=True)
            st.download_button(
                "Download Income Statement",
                data=data["inc"].to_csv(index=False).encode("utf-8"),
                file_name=f"{ticker.upper()}_income_statement.csv",
                mime="text/csv",
            )

    with c2:
        st.markdown(f"**Balance Sheet**  \n_Period: {data['bal_period']}_")
        if data["bal"] is None or data["bal"].empty:
            st.info("Not available.")
        else:
            st.dataframe(format_commas(data["bal"]), use_container_width=True)
            st.download_button(
                "Download Balance Sheet",
                data=data["bal"].to_csv(index=False).encode("utf-8"),
                file_name=f"{ticker.upper()}_balance_sheet.csv",
                mime="text/csv",
            )

    with c3:
        st.markdown(f"**Cash Flow Statement**  \n_Period: {data['cf_period']}_")
        if data["cf"] is None or data["cf"].empty:
            st.info("Not available.")
        else:
            st.dataframe(format_commas(data["cf"]), use_container_width=True)
            st.download_button(
                "Download Cash Flow",
                data=data["cf"].to_csv(index=False).encode("utf-8"),
                file_name=f"{ticker.upper()}_cashflow.csv",
                mime="text/csv",
            )
else:
    st.info("Enter a ticker in the sidebar to load data.")
