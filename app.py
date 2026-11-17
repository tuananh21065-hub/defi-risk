"""
app.py â€” Streamlit Dashboard: DeFi Liquidation Risk Simulator

Cháº¡y: python -m streamlit run app.py
"""
import streamlit as st
import pandas as pd
from simulation import run_scenario
from scenarios import generate_borrowers, INITIAL_ETH_PRICE, LIQUIDATOR_CAPITAL

st.set_page_config(page_title="DeFi Liquidation Risk Simulator", layout="wide")
st.title("đŸ¦ DeFi Liquidation Risk Simulator")
st.caption("MĂ´ phá»ng vĂ  Ä‘Ă¡nh giĂ¡ rá»§i ro thanh lĂ½ trong giao thá»©c cho vay phi táº­p trung (Lending Protocol)")

# --- Sidebar controls ---
st.sidebar.header("â™ï¸ Thiáº¿t láº­p ká»‹ch báº£n")
n_borrowers = st.sidebar.slider("Sá»‘ lÆ°á»£ng ngÆ°á»i vay (Borrowers)", 10, 200, 50, step=10)
eth_price = st.sidebar.number_input("GiĂ¡ ETH ban Ä‘áº§u ($)", value=2000.0, min_value=500.0, max_value=10000.0, step=100.0)
price_shock = st.sidebar.slider("Sá»‘c giĂ¡ ETH ngoáº¡i sinh (%)", -60, 10, -20, step=5)
gas_cost = st.sidebar.number_input("Chi phĂ­ gas má»—i giao dá»‹ch ($)", value=5.0, min_value=0.1, max_value=200.0, step=1.0)
capital = st.sidebar.number_input("Vá»‘n Liquidator ban Ä‘áº§u (USDC)", value=500_000.0, min_value=1000.0, max_value=10_000_000.0, step=10000.0)

st.sidebar.markdown("---")
st.sidebar.subheader("đŸŒ Pháº£n há»“i thá»‹ trÆ°á»ng (Cascade)")
enable_feedback = st.sidebar.checkbox("Báº­t Price Feedback (Liquidation Spiral)", value=False)
market_depth = st.sidebar.select_slider(
    "Äá»™ sĂ¢u thá»‹ trÆ°á»ng (Market Depth)",
    options=[500_000, 2_000_000, 10_000_000, 50_000_000],
    value=10_000_000,
    format_func=lambda x: f"${x:,.0f} USD",
    disabled=not enable_feedback
)

run_btn = st.sidebar.button("â–¶ Cháº¡y mĂ´ phá»ng", type="primary")

if run_btn:
    borrowers = generate_borrowers(n=n_borrowers, eth_price=float(eth_price))
    result = run_scenario(
        borrowers=borrowers,
        initial_eth_price=float(eth_price),
        price_shock_pct=price_shock / 100.0,
        liquidator_capital=float(capital),
        gas_cost_usd=float(gas_cost),
        price_feedback=enable_feedback,
        market_depth_usd=float(market_depth),
    )

    before = result["before"]
    after = result["after"]
    ls = result["liquidator_stats"]

    # Metrics hĂ ng Ä‘áº§u
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("GiĂ¡ ETH cuá»‘i cĂ¹ng", f"${after['eth_price']:,.2f}", f"Ban Ä‘áº§u: ${eth_price:,.0f}")
    col2.metric("Vá»‹ tháº¿ bá»‹ thanh lĂ½", f"{after['n_touched']} / {after['n_borrowers']}", f"{after['touched_rate_pct']}%")
    col3.metric("Vá»‹ tháº¿ cĂ²n máº¥t an toĂ n", f"{after['n_still_unsafe']}", delta_color="inverse")
    col4.metric("Realized Bad Debt", f"${after['total_realized_bad_debt']:,.2f}", delta_color="inverse")
    col5.metric("Lá»£i nhuáº­n Liquidator", f"${ls['total_profit']:,.2f}")

    if enable_feedback and len(result["price_history"]) > 1:
        st.subheader("đŸ“‰ Diá»…n biáº¿n giĂ¡ ETH qua cĂ¡c vĂ²ng thanh lĂ½")
        st.line_chart(pd.DataFrame({"GiĂ¡ ETH ($)": result["price_history"]}))

    st.subheader("đŸ“ Báº£ng so sĂ¡nh chá»‰ sá»‘ TrÆ°á»›c vs Sau thanh lĂ½")
    comparison = pd.DataFrame({
        "Chá»‰ sá»‘ Ä‘Ă¡nh giĂ¡": [
            "Sá»‘ vá»‹ tháº¿ HF < 1 (Nguy hiá»ƒm)",
            "Sá»‘ borrower bá»‹ thanh lĂ½ (Touched)",
            "Sá»‘ borrower tráº£ háº¿t ná»£ (Fully Repaid)",
            "Sá»‘ borrower cĂ²n nguy hiá»ƒm (Still Unsafe)",
            "Tá»•ng giĂ¡ trá»‹ tĂ i sáº£n tháº¿ cháº¥p ($)",
            "Tá»•ng dÆ° ná»£ cĂ²n láº¡i ($)",
            "Realized Bad Debt ($ ná»£ xáº¥u thá»±c táº¿)",
            "Projected Deficit ($ thĂ¢m há»¥t dá»± kiáº¿n)",
            "Tá»· lá»‡ bá»‹ thanh lĂ½ (%)",
            "Tá»· lá»‡ hoĂ n tráº£ háº¿t ná»£ (%)"
        ],
        "TrÆ°á»›c thanh lĂ½": [
            before["n_undercollateralized"],
            before["n_touched"],
            before["n_repaid"],
            before["n_still_unsafe"],
            f"${before['total_collateral_value_usd']:,.2f}",
            f"${before['total_remaining_debt']:,.2f}",
            f"${before['total_realized_bad_debt']:,.2f}",
            f"${before['total_projected_deficit']:,.2f}",
            f"{before['touched_rate_pct']}%",
            f"{before['repaid_rate_pct']}%"
        ],
        "Sau thanh lĂ½": [
            after["n_undercollateralized"],
            after["n_touched"],
            after["n_repaid"],
            after["n_still_unsafe"],
            f"${after['total_collateral_value_usd']:,.2f}",
            f"${after['total_remaining_debt']:,.2f}",
            f"${after['total_realized_bad_debt']:,.2f}",
            f"${after['total_projected_deficit']:,.2f}",
            f"{after['touched_rate_pct']}%",
            f"{after['repaid_rate_pct']}%"
        ],
    })
    st.table(comparison)

    # Thá»‘ng kĂª hoáº¡t Ä‘á»™ng cá»§a Liquidator
    st.subheader("â¡ Thá»‘ng kĂª hoáº¡t Ä‘á»™ng Liquidator")
    lcol1, lcol2, lcol3, lcol4 = st.columns(4)
    lcol1.info(f"**Sá»‘ láº§n thanh lĂ½ thĂ nh cĂ´ng:** {ls['liquidation_count']}")
    lcol2.warning(f"**Bá» qua do khĂ´ng cĂ³ lĂ£i (Gas cao):** {ls['failed_no_profit']}")
    lcol3.error(f"**Bá» qua do thiáº¿u vá»‘n:** {ls['failed_no_capital']}")
    lcol4.success(f"**Vá»‘n Liquidator cĂ²n láº¡i:** ${ls['final_capital_usdc']:,.2f}")

    if result["liquidation_log"]:
        st.subheader("đŸ“ Lá»‹ch sá»­ chi tiáº¿t cĂ¡c lÆ°á»£t thanh lĂ½")
        df_log = pd.DataFrame(result["liquidation_log"])
        success_logs = df_log[df_log["success"] == True]
        if not success_logs.empty:
            display_cols = ["round", "borrower_id", "eth_price", "debt_repaid", "eth_received", "gross_profit_usd", "net_profit_usd", "bad_debt_created"]
            st.dataframe(success_logs[display_cols], use_container_width=True)
        else:
            st.info("KhĂ´ng cĂ³ giao dá»‹ch thanh lĂ½ nĂ o thĂ nh cĂ´ng.")

