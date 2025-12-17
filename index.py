# index.py - Main Streamlit application
# Run: streamlit run index.py

import streamlit as st
from data import load_data
from utils import format_commas

st.set_page_config(page_title="Price & Financials", layout="wide")

st.title("Price & Financials (Ticker-driven)")

ticker = st.text_input("Ticker (use exchange suffix if needed, e.g., LSEG.L)", value="LSEG.L").strip()

if ticker:
    with st.spinner("Loading…"):
        data = load_data(ticker)

    # Header: ticker + name
    left, right = st.columns([2, 3])
    with left:
        st.subheader(f"Ticker: **{ticker.upper()}**")
        st.caption(f"Instrument name: {data['name'] or 'N/A'}")

    # Price chart (5y)
    hist = data["hist"]
    if hist is None or hist.empty:
        st.error("No price history returned. Check the ticker or exchange suffix.")
    else:
        with right:
            last_dt = hist.index[-1]
            last_px = hist["Close"].iloc[-1]
            st.metric(label="Last Close (most recent obs.)", value=f"{last_px:,.2f}", help=str(last_dt.date()))

        st.subheader("5-Year Daily Close")
        st.line_chart(hist["Close"])

        # download CSV
        st.download_button(
            "Download 5y CSV",
            data=hist.to_csv(index=True).encode("utf-8"),
            file_name=f"{ticker.upper()}_5y_daily_close.csv",
            mime="text/csv",
        )

    # Financial statements (latest annual period)
    st.markdown("---")
    st.subheader("Latest Annual Financial Statements")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"**Income Statement**  \n_Period end: {data['inc_period']}_")
        if data["inc"] is None or data["inc"].empty:
            st.info("Not available.")
        else:
            st.dataframe(format_commas(data["inc"]), use_container_width=True)
            st.download_button(
                "Download Income Statement (latest year)",
                data=data["inc"].to_csv(index=False).encode("utf-8"),
                file_name=f"{ticker.upper()}_income_statement_latest_year.csv",
                mime="text/csv",
            )

    with c2:
        st.markdown(f"**Statement of Financial Position (Balance Sheet)**  \n_Period end: {data['bal_period']}_")
        if data["bal"] is None or data["bal"].empty:
            st.info("Not available.")
        else:
            st.dataframe(format_commas(data["bal"]), use_container_width=True)
            st.download_button(
                "Download Balance Sheet (latest year)",
                data=data["bal"].to_csv(index=False).encode("utf-8"),
                file_name=f"{ticker.upper()}_balance_sheet_latest_year.csv",
                mime="text/csv",
            )

    with c3:
        st.markdown(f"**Cash Flow Statement**  \n_Period end: {data['cf_period']}_")
        if data["cf"] is None or data["cf"].empty:
            st.info("Not available.")
        else:
            st.dataframe(format_commas(data["cf"]), use_container_width=True)
            st.download_button(
                "Download Cash Flow (latest year)",
                data=data["cf"].to_csv(index=False).encode("utf-8"),
                file_name=f"{ticker.upper()}_cashflow_latest_year.csv",
                mime="text/csv",
            )
else:
    st.info("Enter a ticker to load the chart and statements.")
