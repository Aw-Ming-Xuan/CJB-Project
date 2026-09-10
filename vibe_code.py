import logging

# --- FIX: SUPPRESS STREAMLIT MISSING SCRIPTRUNCONTEXT LOG WARNINGS ---
logging.getLogger("streamlit.runtime.scriptrunner.script_runner").setLevel(
    logging.ERROR
)
for logger_name in logging.root.manager.loggerDict:
    if "streamlit" in logger_name:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
# ----------------------------------------------------------------------

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
import yfinance as yf

# Configure Seaborn Dark Theme
sns.set_theme(style="darkgrid")
plt.rcParams.update(
    {
        "figure.facecolor": "#0e1117",
        "axes.facecolor": "#0e1117",
        "text.color": "white",
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        "grid.color": "#262730",
    }
)

st.set_page_config(
    page_title="SMU LatAm Market & Presentation Platform",
    layout="wide",
    page_icon="🌎",
)

st.title("🌎 LatAm Market Presentation & Pitch Platform")
st.caption(
    "Developed for SMU Emerging Markets Club | Powered by Streamlit, Seaborn & yfinance"
)


# Helper function to format metrics safely
def format_num(num, is_percent=False, is_curr=True):
    if num is None or not isinstance(num, (int, float)) or pd.isna(num):
        return "N/A"
    if is_percent:
        return f"{num * 100:.2f}%"
    prefix = "$" if is_curr else ""
    if abs(num) >= 1e12:
        return f"{prefix}{num/1e12:.2f}T"
    elif abs(num) >= 1e9:
        return f"{prefix}{num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"{prefix}{num/1e6:.2f}M"
    return f"{prefix}{num:,.2f}"


# --- LATAM DIRECTORY ---
LATAM_DIRECTORY = {
    "🇧🇷 MercadoLibre (MELI - LatAm E-Commerce/Fintech)": {
        "symbol": "MELI",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Nu Holdings (NU - Digital Banking)": {
        "symbol": "NU",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Petrobras (PBR - State Energy)": {
        "symbol": "PBR",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Vale S.A. (VALE - Mining & Materials)": {
        "symbol": "VALE",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Itaú Unibanco (ITUB - Commercial Bank)": {
        "symbol": "ITUB",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Banco Bradesco (BBD - Commercial Bank)": {
        "symbol": "BBD",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Ambev (ABEV - Beverage Leader)": {
        "symbol": "ABEV",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇧🇷 Embraer (ERJ - Aerospace & Defense)": {
        "symbol": "ERJ",
        "country": "Brazil",
        "fx": "BRLUSD=X",
        "etf": "EWZ",
    },
    "🇲🇽 Fomento Económico Mexicano (FMX - Retail)": {
        "symbol": "FMX",
        "country": "Mexico",
        "fx": "MXNUSD=X",
        "etf": "EWW",
    },
    "🇲🇽 América Móvil (AMX - Telecom)": {
        "symbol": "AMX",
        "country": "Mexico",
        "fx": "MXNUSD=X",
        "etf": "EWW",
    },
    "🇲🇽 Cemex (CX - Building Materials)": {
        "symbol": "CX",
        "country": "Mexico",
        "fx": "MXNUSD=X",
        "etf": "EWW",
    },
    "🇲🇽 Coca-Cola FEMSA (KOF - Bottling)": {
        "symbol": "KOF",
        "country": "Mexico",
        "fx": "MXNUSD=X",
        "etf": "EWW",
    },
    "🇨🇱 Sociedad Química y Minera (SQM - Lithium)": {
        "symbol": "SQM",
        "country": "Chile",
        "fx": "CLPUSD=X",
        "etf": "ECH",
    },
    "🇨🇱 Banco de Chile (BCH - Banking)": {
        "symbol": "BCH",
        "country": "Chile",
        "fx": "CLPUSD=X",
        "etf": "ECH",
    },
    "🇦🇷 YPF S.A. (YPF - Energy & Oil)": {
        "symbol": "YPF",
        "country": "Argentina",
        "fx": "ARSUSD=X",
        "etf": "ARGT",
    },
    "🇦🇷 Grupo Financiero Galicia (GGAL - Financials)": {
        "symbol": "GGAL",
        "country": "Argentina",
        "fx": "ARSUSD=X",
        "etf": "ARGT",
    },
    "🇦🇷 Banco Macro (BMA - Banking)": {
        "symbol": "BMA",
        "country": "Argentina",
        "fx": "ARSUSD=X",
        "etf": "ARGT",
    },
    "🇨🇴 Ecopetrol (EC - Oil & Infrastructure)": {
        "symbol": "EC",
        "country": "Colombia",
        "fx": "COPUSD=X",
        "etf": "GXG",
    },
    "🇨🇴 Bancolombia (CIB - Banking)": {
        "symbol": "CIB",
        "country": "Colombia",
        "fx": "COPUSD=X",
        "etf": "GXG",
    },
    "🇵🇪 Credicorp (BAP - Financials)": {
        "symbol": "BAP",
        "country": "Peru",
        "fx": "PENUSD=X",
        "etf": "EPU",
    },
    "🇵🇪 Cia de Minas Buenaventura (BVN - Mining)": {
        "symbol": "BVN",
        "country": "Peru",
        "fx": "PENUSD=X",
        "etf": "EPU",
    },
    "🇺🇾 dLocal (DLO - Payments)": {
        "symbol": "DLO",
        "country": "Uruguay",
        "fx": "UYUUSD=X",
        "etf": "EWZ",
    },
}

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🔍 LatAm Search & Selection")
preset_selection = st.sidebar.selectbox(
    "Select Target Stock:",
    ["-- Select From Directory --"] + list(LATAM_DIRECTORY.keys()),
)
custom_ticker = (
    st.sidebar.text_input("Or Enter Any Ticker (e.g. ITUB, CX, BMA, AAPL):", "")
    .strip()
    .upper()
)

if custom_ticker:
    ticker_symbol = custom_ticker
    country_hint = "Custom Search"
    fx_symbol = "BRLUSD=X"
    country_etf = "EWZ"
elif preset_selection != "-- Select From Directory --":
    ticker_symbol = LATAM_DIRECTORY[preset_selection]["symbol"]
    country_hint = LATAM_DIRECTORY[preset_selection]["country"]
    fx_symbol = LATAM_DIRECTORY[preset_selection]["fx"]
    country_etf = LATAM_DIRECTORY[preset_selection]["etf"]
else:
    ticker_symbol = "MELI"
    country_hint = "Brazil"
    fx_symbol = "BRLUSD=X"
    country_etf = "EWZ"

timeframe = st.sidebar.selectbox(
    "Chart Timeframe", ["1mo", "3mo", "6mo", "1y", "5y"], index=3
)

# Fetch Stock Info
ticker = yf.Ticker(ticker_symbol)
try:
    info = ticker.info
except Exception:
    info = {}

# Sidebar Company Card
st.sidebar.markdown("---")
st.sidebar.header("🏢 Company Profile")
company_name = info.get("longName") or info.get("shortName") or ticker_symbol
st.sidebar.subheader(company_name)

if info and info.get("quoteType"):
    st.sidebar.write(f"**Country:** {info.get('country', country_hint)}")
    st.sidebar.write(f"**Sector:** {info.get('sector', 'N/A')}")
    st.sidebar.write(f"**Industry:** {info.get('industry', 'N/A')}")
    st.sidebar.write(f"**Market Cap:** {format_num(info.get('marketCap'))}")
    st.sidebar.write(
        f"**Enterprise Value:** {format_num(info.get('enterpriseValue'))}"
    )
    st.sidebar.write(f"**Exchange:** {info.get('exchange', 'N/A')}")
    with st.sidebar.expander("📄 Business Summary"):
        st.write(
            info.get("longBusinessSummary", "No overview summary available.")
        )
else:
    st.sidebar.warning("Limited metadata found for this ticker.")

# --- NAVIGATION TABS ---
(
    tab_ratios,
    tab_options,
    tab_peers,
    tab_macro,
    tab_chart,
    tab_sentiment,
    tab_summary,
    tab_script,
    tab_guide,
) = st.tabs([
    "📊 Financial Ratios",
    "🎯 Options & Sentiment",
    "⚔️ Peer Comparison",
    "🏛️ Sovereign & FX Macro",
    "📈 Price & Technicals",
    "📰 News Catalysts",
    "📑 Executive Slide Highlights",
    "🎙️ Dynamic Pitch Script",
    "🎓 Presentation Playbook",
])

# --- TAB 1: FINANCIAL RATIOS ---
with tab_ratios:
    st.subheader(
        f"📊 Comprehensive Valuation & Ratios Matrix ({ticker_symbol})"
    )
    col_val, col_prof, col_health, col_yield = st.columns(4)

    with col_val:
        st.markdown("### 🏷️ Valuation Multiples")
        st.write(
            f"**Forward P/E:** {format_num(info.get('forwardPE'), is_curr=False)}"
        )
        st.write(
            f"**Trailing P/E:** {format_num(info.get('trailingPE'), is_curr=False)}"
        )
        st.write(
            f"**EV / EBITDA:** {format_num(info.get('enterpriseToEbitda'), is_curr=False)}"
        )
        st.write(
            f"**EV / Revenue:** {format_num(info.get('enterpriseToRevenue'), is_curr=False)}"
        )
        st.write(
            f"**Price / Book (P/B):** {format_num(info.get('priceToBook'), is_curr=False)}"
        )
        st.write(
            f"**Price / Sales:** {format_num(info.get('priceToSalesTrailing12Months'), is_curr=False)}"
        )

    with col_prof:
        st.markdown("### 💰 Margins & Returns")
        st.write(
            f"**Gross Margin:** {format_num(info.get('grossMargins'), is_percent=True)}"
        )
        st.write(
            f"**Operating Margin:** {format_num(info.get('operatingMargins'), is_percent=True)}"
        )
        st.write(
            f"**Profit Margin:** {format_num(info.get('profitMargins'), is_percent=True)}"
        )
        st.write(
            f"**Return on Equity (ROE):** {format_num(info.get('returnOnEquity'), is_percent=True)}"
        )
        st.write(
            f"**Return on Assets (ROA):** {format_num(info.get('returnOnAssets'), is_percent=True)}"
        )
        st.write(
            f"**Revenue Growth:** {format_num(info.get('revenueGrowth'), is_percent=True)}"
        )

    with col_health:
        st.markdown("### 🛡️ Solvency & Debt")
        st.write(
            f"**Debt to Equity:** {format_num(info.get('debtToEquity'), is_curr=False)}"
        )
        st.write(
            f"**Current Ratio:** {format_num(info.get('currentRatio'), is_curr=False)}"
        )
        st.write(
            f"**Quick Ratio:** {format_num(info.get('quickRatio'), is_curr=False)}"
        )
        st.write(f"**Total Cash:** {format_num(info.get('totalCash'))}")
        st.write(f"**Total Debt:** {format_num(info.get('totalDebt'))}")
        st.write(
            f"**Operating Cash Flow:** {format_num(info.get('operatingCashflow'))}"
        )

    with col_yield:
        st.markdown("### 📈 Shareholder Yield")
        st.write(f"**Trailing EPS:** {format_num(info.get('trailingEps'))}")
        st.write(f"**Forward EPS:** {format_num(info.get('forwardEps'))}")
        st.write(
            f"**Dividend Yield:** {format_num(info.get('dividendYield'), is_percent=True)}"
        )
        st.write(
            f"**Payout Ratio:** {format_num(info.get('payoutRatio'), is_percent=True)}"
        )
        st.write(f"**Book Value / Share:** {format_num(info.get('bookValue'))}")
        st.write(f"**Free Cash Flow:** {format_num(info.get('freeCashflow'))}")

# --- TAB 2: OPTIONS CHAIN & MARKET SENTIMENT ---
expirations = ()
try:
    expirations = ticker.options
except Exception:
    expirations = ()

with tab_options:
    st.subheader(
        f"🎯 Options Market Flow & Hold/Release Sentiment ({ticker_symbol})"
    )

    if expirations:
        selected_exp = st.selectbox(
            "Select Options Expiration Date:", expirations, index=0
        )

        try:
            opt_chain = ticker.option_chain(selected_exp)
            calls = opt_chain.calls.fillna(0)
            puts = opt_chain.puts.fillna(0)

            total_call_vol = int(calls["volume"].sum())
            total_put_vol = int(puts["volume"].sum())
            total_call_oi = int(calls["openInterest"].sum())
            total_put_oi = int(puts["openInterest"].sum())

            pcr_vol = (
                (total_put_vol / total_call_vol) if total_call_vol > 0 else 0
            )
            pcr_oi = (total_put_oi / total_call_oi) if total_call_oi > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "Call Vol / Open Interest",
                f"{total_call_vol:,} / {total_call_oi:,}",
            )
            m2.metric(
                "Put Vol / Open Interest",
                f"{total_put_vol:,} / {total_put_oi:,}",
            )
            m3.metric(
                "Put/Call Ratio (Volume)",
                f"{pcr_vol:.2f}",
                delta="Bearish" if pcr_vol > 1.0 else "Bullish",
                delta_color="inverse",
            )
            m4.metric(
                "Put/Call Ratio (Open Interest)",
                f"{pcr_oi:.2f}",
                delta="Heavy Hedging" if pcr_oi > 1.2 else "Growth Outlook",
                delta_color="inverse",
            )

            st.markdown("---")

            if pcr_oi > 1.2 or pcr_vol > 1.2:
                st.warning(
                    f"⚠️ **Bearish / Hedging Outlook (Release Signal):** Put/Call Open Interest Ratio is {pcr_oi:.2f}. Institutional traders are holding Put options to hedge against downside risks or sovereign volatility."
                )
            elif pcr_oi < 0.7 and pcr_vol < 0.7:
                st.success(
                    f"🟢 **Bullish Momentum Outlook (Hold / Accumulate Signal):** Put/Call Open Interest Ratio is {pcr_oi:.2f}. Strong Call option volume suggests traders expect stock appreciation."
                )
            else:
                st.info(
                    f"🔵 **Neutral / Balanced Outlook:** Put/Call ratio is {pcr_oi:.2f}. Institutions are maintaining balanced hedging postures."
                )

            col_calls, col_puts = st.columns(2)
            with col_calls:
                st.markdown("**🟢 Top Call Options Contracts**")
                st.dataframe(
                    calls[[
                        "strike",
                        "lastPrice",
                        "bid",
                        "ask",
                        "volume",
                        "openInterest",
                        "impliedVolatility",
                    ]]
                    .sort_values("openInterest", ascending=False)
                    .head(8),
                    use_container_width=True,
                )

            with col_puts:
                st.markdown("**🔴 Top Put Options Contracts**")
                st.dataframe(
                    puts[[
                        "strike",
                        "lastPrice",
                        "bid",
                        "ask",
                        "volume",
                        "openInterest",
                        "impliedVolatility",
                    ]]
                    .sort_values("openInterest", ascending=False)
                    .head(8),
                    use_container_width=True,
                )

        except Exception as e:
            st.error(
                f"Could not load option chain for expiration date {selected_exp}: {e}"
            )
    else:
        st.info(
            f"No active options contracts traded on US exchanges for '{ticker_symbol}'. Options metrics are available for US-listed ADRs (e.g., MELI, NU, PBR, VALE, YPF, CX)."
        )

# --- TAB 3: PEER COMPARISON MATRIX ---
with tab_peers:
    st.subheader("⚔️ Side-by-Side Peer Valuation Comparison")
    st.caption(
        "Compare key metrics between your target company and a regional competitor for presentation slides."
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.write(f"**Target Stock:** `{ticker_symbol}`")
    with col_p2:
        peer_ticker_symbol = (
            st.text_input(
                "Enter Peer Ticker Symbol (e.g. NU, ITUB, PBR, CX):",
                "NU" if ticker_symbol != "NU" else "MELI",
            )
            .strip()
            .upper()
        )

    peer_ticker = yf.Ticker(peer_ticker_symbol)
    try:
        peer_info = peer_ticker.info
    except Exception:
        peer_info = {}

    metrics_comparison = {
        "Metric": [
            "Market Cap",
            "Forward P/E",
            "EV / EBITDA",
            "Operating Margin",
            "Profit Margin",
            "ROE",
            "YoY Rev Growth",
            "Debt / Equity",
        ],
        f"{ticker_symbol} (Target)": [
            format_num(info.get("marketCap")),
            format_num(info.get("forwardPE"), is_curr=False),
            format_num(info.get("enterpriseToEbitda"), is_curr=False),
            format_num(info.get("operatingMargins"), is_percent=True),
            format_num(info.get("profitMargins"), is_percent=True),
            format_num(info.get("returnOnEquity"), is_percent=True),
            format_num(info.get("revenueGrowth"), is_percent=True),
            format_num(info.get("debtToEquity"), is_curr=False),
        ],
        f"{peer_ticker_symbol} (Peer)": [
            format_num(peer_info.get("marketCap")),
            format_num(peer_info.get("forwardPE"), is_curr=False),
            format_num(peer_info.get("enterpriseToEbitda"), is_curr=False),
            format_num(peer_info.get("operatingMargins"), is_percent=True),
            format_num(peer_info.get("profitMargins"), is_percent=True),
            format_num(peer_info.get("returnOnEquity"), is_percent=True),
            format_num(peer_info.get("revenueGrowth"), is_percent=True),
            format_num(peer_info.get("debtToEquity"), is_curr=False),
        ],
    }

    df_peers = pd.DataFrame(metrics_comparison)
    st.table(df_peers)

# --- TAB 4: SOVEREIGN MACRO & FX SCORECARD ---
with tab_macro:
    st.subheader(f"🏛️ Sovereign Risk Scorecard ({country_hint})")
    st.caption(
        "Evaluate overall country risk by tracking the primary Country ETF alongside foreign exchange trends."
    )

    c_etf, c_fx = st.columns(2)

    with c_etf:
        st.markdown(f"**Country Equity Index ETF (`{country_etf}`)**")
        etf_ticker = yf.Ticker(country_etf)
        etf_hist = etf_ticker.history(period=timeframe)
        if not etf_hist.empty:
            etf_hist = etf_hist.reset_index()
            if pd.api.types.is_datetime64tz_dtype(etf_hist["Date"]):
                etf_hist["Date"] = etf_hist["Date"].dt.tz_localize(None)
            fig_etf, ax_e = plt.subplots(figsize=(6, 3.5))
            sns.lineplot(
                data=etf_hist,
                x="Date",
                y="Close",
                ax=ax_e,
                color="#29B6F6",
                linewidth=2,
            )
            ax_e.set_title(
                f"{country_etf} Trajectory ({timeframe})",
                color="white",
                fontsize=11,
            )
            ax_e.set_ylabel("Price (USD)", color="white")
            fig_etf.autofmt_xdate()
            plt.tight_layout()
            st.pyplot(fig_etf)

    with c_fx:
        st.markdown(f"**Foreign Exchange Rate (`{fx_symbol}`)**")
        fx_ticker = yf.Ticker(fx_symbol)
        fx_hist = fx_ticker.history(period=timeframe)
        if not fx_hist.empty:
            fx_hist = fx_hist.reset_index()
            if pd.api.types.is_datetime64tz_dtype(fx_hist["Date"]):
                fx_hist["Date"] = fx_hist["Date"].dt.tz_localize(None)
            fig_fx, ax_f = plt.subplots(figsize=(6, 3.5))
            sns.lineplot(
                data=fx_hist,
                x="Date",
                y="Close",
                ax=ax_f,
                color="#FFD54F",
                linewidth=2,
            )
            ax_f.set_title(
                f"{fx_symbol} Currency Trajectory ({timeframe})",
                color="white",
                fontsize=11,
            )
            ax_f.set_ylabel("FX Rate", color="white")
            fig_fx.autofmt_xdate()
            plt.tight_layout()
            st.pyplot(fig_fx)

# --- TAB 5: TECHNICAL PRICE & VOLUME ---
with tab_chart:
    st.subheader(f"📈 Technical Price Trajectory ({ticker_symbol})")
    hist = ticker.history(period=timeframe)
    if not hist.empty:
        hist = hist.reset_index()
        if pd.api.types.is_datetime64tz_dtype(hist["Date"]):
            hist["Date"] = hist["Date"].dt.tz_localize(None)

        hist["20_MA"] = hist["Close"].rolling(20).mean()
        hist["50_MA"] = hist["Close"].rolling(50).mean()

        fig, (ax1, ax2) = plt.subplots(
            2,
            1,
            figsize=(12, 6),
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
        )
        sns.lineplot(
            data=hist,
            x="Date",
            y="Close",
            ax=ax1,
            color="#00E676",
            label="Close Price",
            linewidth=2,
        )
        sns.lineplot(
            data=hist,
            x="Date",
            y="20_MA",
            ax=ax1,
            color="#FF9100",
            label="20-Day MA",
            linestyle="--",
        )
        sns.lineplot(
            data=hist,
            x="Date",
            y="50_MA",
            ax=ax1,
            color="#29B6F6",
            label="50-Day MA",
            linestyle=":",
        )
        ax1.set_ylabel("Price (USD)", color="white")
        ax1.legend(facecolor="#1E222D", edgecolor="none", labelcolor="white")

        ax2.bar(hist["Date"], hist["Volume"], color="#37474F", alpha=0.7, width=1)
        ax2.set_ylabel("Volume", color="white")
        fig.autofmt_xdate()
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.error(f"No price data available for ticker '{ticker_symbol}'.")

# --- TAB 6: NEWS CATALYSTS ---
with tab_sentiment:
    st.subheader(f"📰 News Catalysts & Headline Sentiment ({ticker_symbol})")

    @st.cache_data(ttl=1800)
    def fetch_google_news(query):
        encoded = urllib.parse.quote(f"{query} stock news")
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        articles = []
        try:
            with urllib.request.urlopen(req) as response:
                root = ET.fromstring(response.read())
                for item in root.findall("./channel/item")[:8]:
                    articles.append({
                        "title": item.find("title").text,
                        "link": item.find("link").text,
                        "pubDate": item.find("pubDate").text[:16],
                    })
        except Exception:
            pass
        return articles

    articles = fetch_google_news(ticker_symbol)
    if articles:
        for art in articles:
            st.markdown(
                f"- [{art['title']}]({art['link']}) — *{art['pubDate']}*"
            )
    else:
        st.info("No recent headlines retrieved for this ticker.")

# --- TAB 7: EXECUTIVE SLIDE HIGHLIGHTS GENERATOR ---
with tab_summary:
    st.subheader(
        f"📑 Executive Presentation Highlights Generator ({ticker_symbol})"
    )
    st.caption(
        "Copy and paste these auto-generated bullet points directly into your presentation slides."
    )

    fwd_pe = format_num(info.get("forwardPE"), is_curr=False)
    ev_ebitda = format_num(info.get("enterpriseToEbitda"), is_curr=False)
    rev_g = format_num(info.get("revenueGrowth"), is_percent=True)
    mkt_cap = format_num(info.get("marketCap"))
    op_m = format_num(info.get("operatingMargins"), is_percent=True)

    summary_text = f"""
    ### 🎯 Slide 1: Company Profile & Core Valuation
    * **Target Entity:** {company_name} (`{ticker_symbol}`) | **Country:** {info.get('country', country_hint)}
    * **Market Capitalization:** {mkt_cap} | **Sector:** {info.get('sector', 'N/A')}
    * **Valuation Multiples:** Trading at a Forward P/E of **{fwd_pe}** and EV/EBITDA of **{ev_ebitda}**.
    
    ---
    
    ### 📊 Slide 2: Growth Engine & Operational Health
    * **Top-line Expansion:** YoY Revenue Growth currently stands at **{rev_g}**.
    * **Operating Profitability:** Operating Margins running at **{op_m}**.
    * **Balance Sheet Stability:** Debt-to-Equity ratio at **{format_num(info.get('debtToEquity'), is_curr=False)}**.
    
    ---
    
    ### 🏛️ Slide 3: Sovereign Exposure & Sentiment Thesis
    * **Macro Factor:** Exposed to `{fx_symbol}` exchange fluctuations and sovereign index benchmark `{country_etf}`.
    * **Institutional Stance:** Review Put/Call Open Interest ratios in Tab 2 before issuing a final Hold or Release rating.
    """

    st.markdown(summary_text)

# --- TAB 8: DYNAMIC PITCH SCRIPT GENERATOR ---
with tab_script:
    st.subheader(f"🎙️ Adaptive Oral Stock Pitch Script ({ticker_symbol})")
    st.caption(
        "Auto-generated 90-second pitch transcript tailored to current live market data."
    )

    fwd_pe_val = format_num(info.get("forwardPE"), is_curr=False)
    ev_ebitda_val = format_num(info.get("enterpriseToEbitda"), is_curr=False)
    rev_growth_val = format_num(info.get("revenueGrowth"), is_percent=True)
    margin_val = format_num(info.get("operatingMargins"), is_percent=True)
    country_val = info.get("country", country_hint)
    sector_val = info.get("sector", "Emerging Markets Equities")

    pcr_signal = "neutral"
    pcr_explanation = "balanced option open interest, reflecting standard institutional portfolio hedging."

    try:
        if expirations:
            opt_c = ticker.option_chain(expirations[0])
            c_vol = opt_c.calls["volume"].sum()
            p_vol = opt_c.puts["volume"].sum()
            pcr_calc = (p_vol / c_vol) if c_vol > 0 else 1.0
            if pcr_calc > 1.1:
                pcr_signal = "defensive / cautious"
                pcr_explanation = f"a high Put/Call ratio of {pcr_calc:.2f}, signaling that institutional desk flows are heavily hedging downside risk."
            elif pcr_calc < 0.8:
                pcr_signal = "strongly bullish"
                pcr_explanation = f"a low Put/Call ratio of {pcr_calc:.2f}, indicating aggressive institutional call buying for upside exposure."
    except Exception:
        pass

    oral_script = f"""
    **[0:00 - 0:20] Section 1: The Hook & Executive Summary**
    > "Good afternoon. Today I am presenting **{company_name}** (Ticker: **{ticker_symbol}**), a market leader in the **{sector_val}** sector out of **{country_val}**. 
    > Our thesis centers on capitalized market dominance, strong operational margins of **{margin_val}**, and robust top-line revenue expansion currently tracking at **{rev_growth_val}** YoY."

    **[0:20 - 0:45] Section 2: Valuation & Competitor Benchmarking**
    > "Looking at core valuation multiples, **{ticker_symbol}** is currently trading at a Forward P/E of **{fwd_pe_val}** and an EV/EBITDA of **{ev_ebitda_val}**. 
    > When benchmarked against regional peers, this multiple reflects an attractive risk-reward entry point, particularly given the company's superior balance sheet liquidity and return metrics."

    **[0:45 - 1:10] Section 3: Sovereign FX & Derivatives Flow**
    > "Because this is an emerging market asset, we must account for sovereign currency risk tied to `{fx_symbol}` and broader index movement in `{country_etf}`. 
    > Turning to institutional positioning in the US options chain, current derivatives flow is **{pcr_signal}**—with {pcr_explanation}"

    **[1:10 - 1:30] Section 4: Recommendation & Final Takeaway**
    > "In summary, given **{company_name}'s** growth velocity, sector positioning, and current valuation discount relative to historical averages, we recommend a **HOLD / ACCUMULATE** rating for equity portfolios seeking LatAm growth exposure. Thank you, and I am open to any questions."
    """

    st.markdown(oral_script)

    st.markdown("---")
    st.markdown("**⚙️ Pitch Customization Controls**")
    custom_target = st.text_input(
        "Custom Target Price or Upside Target (e.g., '$120 / +25% upside'):",
        "$150 / 20% upside",
    )
    c_speaker, c_tone = st.columns(2)
    with c_speaker:
        st.selectbox(
            "Pitch Duration:",
            [
                "90 Seconds (Quick Pitch)",
                "3 Minutes (Committee Style)",
                "5 Minutes (Deep Dive)",
            ],
        )
    with c_tone:
        st.selectbox(
            "Presentation Stance:",
            ["Bullish / Accumulate", "Neutral / Hold", "Bearish / Release"],
        )

    st.info(
        f"💡 **Pitching Tip:** Stated Price Target: **{custom_target}**. Emphasize the Forward P/E ({fwd_pe_val}) and Put/Call positioning when answering Q&A from judges."
    )

# --- TAB 9: PRESENTATION PLAYBOOK ---
with tab_guide:
    st.subheader("🎓 Presentation Playbook: Pitching LatAm Equities")
    st.markdown("""
    ### Structure of an Emerging Markets Stock Pitch
    
    1. **The Macro Narrative:** Establish the country thesis (e.g., Brazilian rate cuts, Mexican nearshoring trends, or Chilean lithium demand).
    2. **Company Moat:** Explain why the company dominates its domestic sector (e.g., MercadoLibre's logistics infrastructure).
    3. **Valuation & Margins:** Present EV/EBITDA and Forward P/E relative to regional peers (Tab 3).
    4. **Institutional Derivatives Flow:** Use Put/Call Ratios (Tab 2) to demonstrate whether institutional market makers are hedging against political risk or accumulating Call leverage.
    
    ---

    ### Options Metrics Quick-Reference
    * **Put/Call Volume Ratio ($PCR_{Vol}$):** Below 0.70 is bullish; above 1.20 indicates immediate institutional downside hedging.
    * **Put/Call Open Interest Ratio ($PCR_{OI}$):** Below 0.80 suggests structural institutional holding; above 1.30 reflects heavy macro hedging or earnings risk preparation.
    """)