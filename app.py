"""
app.py — Streamlit Dashboard: DeFi Market Risk Monitor

Chạy: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from simulation import run_scenario
from scenarios import generate_borrowers, INITIAL_ETH_PRICE, LIQUIDATOR_CAPITAL

st.set_page_config(page_title="DeFi Market Risk Monitor", layout="wide")
st.title("🏦 DeFi Market Risk Monitor")
st.caption("Mô phỏng rủi ro thanh lý trong giao thức cho vay phi tập trung (mô hình rút gọn, không phản ánh Aave mainnet)")

# --- Sidebar controls ---
st.sidebar.header("Tham số kịch bản")
n_borrowers = st.sidebar.slider("Số người vay", 10, 200, 50, step=10)
eth_price = st.sidebar.number_input("Giá ETH ban đầu (USD)", value=2000, min_value=500, max_value=10000, step=100)
price_shock = st.sidebar.slider("Sốc giá ETH (%)", -50, 10, -20, step=5)
gas_cost = st.sidebar.number_input("Chi phí gas (USD)", value=5.0, min_value=0.1, max_value=200.0, step=1.0)
capital = st.sidebar.number_input("Vốn Liquidator (USDC)", value=500_000, min_value=1000, max_value=10_000_000, step=10000)

run_btn = st.sidebar.button("▶ Chạy mô phỏng", type="primary")

if run_btn:
    borrowers = generate_borrowers(n=n_borrowers, eth_price=float(eth_price))
    result = run_scenario(
        borrowers=borrowers,
        initial_eth_price=float(eth_price),
        price_shock_pct=price_shock / 100.0,
        liquidator_capital=float(capital),
        gas_cost_usd=float(gas_cost),
    )

    before = result["before"]
    after = result["after"]
    ls = result["liquidator_stats"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Giá ETH sau sốc", f"${after['eth_price']:,.0f}", f"{price_shock}%")
    col2.metric("Vị thế bị thanh lý", after["n_liquidated"])
    col3.metric("Shortfall (USD)", f"${after['total_shortfall']:,.2f}")
    col4.metric("Lợi nhuận Liquidator", f"${ls['total_profit']:,.2f}")

    st.subheader("So sánh Trước / Sau")
    comparison = pd.DataFrame({
        "Chỉ số": ["HF < 1 (đủ điều kiện TL)", "Đã thanh lý", "Tổng thế chấp (USD)", "Tổng dư nợ (USD)", "Shortfall (USD)", "Tỷ lệ thanh lý (%)"],
        "Trước": [before["n_undercollateralized"], before["n_liquidated"],
                  before["total_collateral_value_usd"], before["total_debt_usdc"],
                  before["total_shortfall"], before["liquidation_rate_pct"]],
        "Sau": [after["n_undercollateralized"], after["n_liquidated"],
                after["total_collateral_value_usd"], after["total_debt_usdc"],
                after["total_shortfall"], after["liquidation_rate_pct"]],
    })
    st.dataframe(comparison, use_container_width=True)

    if result["liquidation_log"]:
        st.subheader("Log thanh lý")
        df_log = pd.DataFrame(result["liquidation_log"])
        st.dataframe(df_log[df_log["success"]].head(50), use_container_width=True)
