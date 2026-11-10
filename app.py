"""
app.py — Streamlit Dashboard: DeFi Liquidation Risk Simulator

Chạy: python -m streamlit run app.py
"""
import streamlit as st
import pandas as pd
from simulation import run_scenario
from scenarios import generate_borrowers, INITIAL_ETH_PRICE, LIQUIDATOR_CAPITAL

st.set_page_config(page_title="DeFi Liquidation Risk Simulator", layout="wide")
st.title("🏦 DeFi Liquidation Risk Simulator")
st.caption("Mô phỏng và đánh giá rủi ro thanh lý trong giao thức cho vay phi tập trung (Lending Protocol)")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Thiết lập kịch bản")
n_borrowers = st.sidebar.slider("Số lượng người vay (Borrowers)", 10, 200, 50, step=10)
eth_price = st.sidebar.number_input("Giá ETH ban đầu ($)", value=2000.0, min_value=500.0, max_value=10000.0, step=100.0)
price_shock = st.sidebar.slider("Sốc giá ETH ngoại sinh (%)", -60, 10, -20, step=5)
gas_cost = st.sidebar.number_input("Chi phí gas mỗi giao dịch ($)", value=5.0, min_value=0.1, max_value=200.0, step=1.0)
capital = st.sidebar.number_input("Vốn Liquidator ban đầu (USDC)", value=500_000.0, min_value=1000.0, max_value=10_000_000.0, step=10000.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🌊 Phản hồi thị trường (Cascade)")
enable_feedback = st.sidebar.checkbox("Bật Price Feedback (Liquidation Spiral)", value=False)
market_depth = st.sidebar.select_slider(
    "Độ sâu thị trường (Market Depth)",
    options=[500_000, 2_000_000, 10_000_000, 50_000_000],
    value=10_000_000,
    format_func=lambda x: f"${x:,.0f} USD",
    disabled=not enable_feedback
)

run_btn = st.sidebar.button("▶ Chạy mô phỏng", type="primary")

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

    # Metrics hàng đầu
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Giá ETH cuối cùng", f"${after['eth_price']:,.2f}", f"Ban đầu: ${eth_price:,.0f}")
    col2.metric("Vị thế bị thanh lý", f"{after['n_touched']} / {after['n_borrowers']}", f"{after['touched_rate_pct']}%")
    col3.metric("Vị thế còn mất an toàn", f"{after['n_still_unsafe']}", delta_color="inverse")
    col4.metric("Realized Bad Debt", f"${after['total_realized_bad_debt']:,.2f}", delta_color="inverse")
    col5.metric("Lợi nhuận Liquidator", f"${ls['total_profit']:,.2f}")

    if enable_feedback and len(result["price_history"]) > 1:
        st.subheader("📉 Diễn biến giá ETH qua các vòng thanh lý")
        st.line_chart(pd.DataFrame({"Giá ETH ($)": result["price_history"]}))

    st.subheader("📊 Bảng so sánh chỉ số Trước vs Sau thanh lý")
    comparison = pd.DataFrame({
        "Chỉ số đánh giá": [
            "Số vị thế HF < 1 (Nguy hiểm)",
            "Số borrower bị thanh lý (Touched)",
            "Số borrower trả hết nợ (Fully Repaid)",
            "Số borrower còn nguy hiểm (Still Unsafe)",
            "Tổng giá trị tài sản thế chấp ($)",
            "Tổng dư nợ còn lại ($)",
            "Realized Bad Debt ($ nợ xấu thực tế)",
            "Projected Deficit ($ thâm hụt dự kiến)",
            "Tỷ lệ bị thanh lý (%)",
            "Tỷ lệ hoàn trả hết nợ (%)"
        ],
        "Trước thanh lý": [
            before["n_undercollateralized"],
            before["n_touched"],
            before["n_fully_repaid"],
            before["n_still_unsafe"],
            f"${before['total_collateral_value_usd']:,.2f}",
            f"${before['total_remaining_debt']:,.2f}",
            f"${before['total_realized_bad_debt']:,.2f}",
            f"${before['total_projected_deficit']:,.2f}",
            f"{before['touched_rate_pct']}%",
            f"{before['fully_repaid_rate_pct']}%"
        ],
        "Sau thanh lý": [
            after["n_undercollateralized"],
            after["n_touched"],
            after["n_fully_repaid"],
            after["n_still_unsafe"],
            f"${after['total_collateral_value_usd']:,.2f}",
            f"${after['total_remaining_debt']:,.2f}",
            f"${after['total_realized_bad_debt']:,.2f}",
            f"${after['total_projected_deficit']:,.2f}",
            f"{after['touched_rate_pct']}%",
            f"{after['fully_repaid_rate_pct']}%"
        ],
    })
    st.table(comparison)

    # Thống kê hoạt động của Liquidator
    st.subheader("⚡ Thống kê hoạt động Liquidator")
    lcol1, lcol2, lcol3, lcol4 = st.columns(4)
    lcol1.info(f"**Số lần thanh lý thành công:** {ls['liquidation_count']}")
    lcol2.warning(f"**Bỏ qua do không có lãi (Gas cao):** {ls['failed_no_profit']}")
    lcol3.error(f"**Bỏ qua do thiếu vốn:** {ls['failed_no_capital']}")
    lcol4.success(f"**Vốn Liquidator còn lại:** ${ls['final_capital_usdc']:,.2f}")

    if result["liquidation_log"]:
        st.subheader("📝 Lịch sử chi tiết các lượt thanh lý")
        df_log = pd.DataFrame(result["liquidation_log"])
        success_logs = df_log[df_log["success"] == True]
        if not success_logs.empty:
            display_cols = ["round", "borrower_id", "eth_price", "debt_repaid", "eth_received", "gross_profit_usd", "net_profit_usd", "bad_debt_created"]
            st.dataframe(success_logs[display_cols], use_container_width=True)
        else:
            st.info("Không có giao dịch thanh lý nào thành công.")
