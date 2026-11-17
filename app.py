# -*- coding: utf-8 -*-
"""
app.py — Streamlit Dashboard: DeFi Liquidation Risk Simulator

Chạy: python -X utf8 -m streamlit run app.py
"""
import streamlit as st
import pandas as pd
from simulation import run_scenario
from scenarios import (
    generate_borrowers, generate_lenders, make_pool,
    INITIAL_ETH_PRICE, LIQUIDATOR_CAPITAL,
)
from model import borrow_rate, supply_rate

st.set_page_config(page_title="DeFi Liquidation Risk Simulator", layout="wide")
st.title("🏦 DeFi Liquidation Risk Simulator")
st.caption("Mô phỏng và đánh giá rủi ro thanh lý trong giao thức cho vay phi tập trung (Lending Protocol)")

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Thiết lập kịch bản")

n_borrowers = st.sidebar.slider("Số lượng Borrower", 10, 200, 50, step=10)
n_lenders   = st.sidebar.slider("Số lượng Lender",    5, 100, 20, step=5)
eth_price   = st.sidebar.number_input("Giá ETH ban đầu ($)", value=2000.0,
                                       min_value=500.0, max_value=10000.0, step=100.0)
total_supply = st.sidebar.number_input("Tổng USDC Lender gửi vào Pool ($)",
                                        value=2_000_000.0, min_value=100_000.0,
                                        max_value=20_000_000.0, step=100_000.0)
price_shock  = st.sidebar.slider("Sốc giá ETH ngoại sinh (%)", -60, 10, -20, step=5)
gas_cost     = st.sidebar.number_input("Chi phí gas mỗi giao dịch ($)", value=5.0,
                                        min_value=0.1, max_value=200.0, step=1.0)
capital      = st.sidebar.number_input("Vốn Liquidator ban đầu (USDC)",
                                        value=500_000.0, min_value=1000.0,
                                        max_value=10_000_000.0, step=10_000.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🎭 Chiến lược tác nhân")
strategy = st.sidebar.radio(
    "Chiến lược Borrower / Lender",
    options=["fixed", "adaptive"],
    format_func=lambda x: "🔒 Fixed — không thích nghi" if x == "fixed"
                          else "🧠 Adaptive — thích nghi theo HF & điều kiện",
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("🌊 Phản hồi thị trường (Cascade)")
enable_feedback = st.sidebar.checkbox("Bật Price Feedback (Liquidation Spiral)", value=False)
market_depth = st.sidebar.select_slider(
    "Độ sâu thị trường (Market Depth)",
    options=[500_000, 2_000_000, 5_000_000, 10_000_000, 50_000_000],
    value=10_000_000,
    format_func=lambda x: f"${x:,.0f} USD",
    disabled=not enable_feedback,
)

st.sidebar.markdown("---")
st.sidebar.subheader("💧 Cú sốc thanh khoản (S2)")
liquidity_shock = st.sidebar.slider(
    "% Lender rút ngay lập tức", 0, 80, 0, step=5,
    help="S2: Lender rút USDC → available_liquidity giảm"
)

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Cú sốc lãi suất (S3)")
demand_surge = st.sidebar.number_input(
    "USDC vay thêm (nhu cầu tăng)", value=0.0, min_value=0.0,
    max_value=2_000_000.0, step=50_000.0,
    help="S3: Tăng total_debt → utilization tăng → lãi suất tăng"
)

run_btn = st.sidebar.button("▶ Chạy mô phỏng", type="primary")

# ── Chạy mô phỏng ────────────────────────────────────────────────────────────
if run_btn:
    borrowers = generate_borrowers(n=n_borrowers, eth_price=float(eth_price))
    lenders   = generate_lenders(n=n_lenders, total_supply_usdc=float(total_supply))
    pool      = make_pool(borrowers, lenders)

    result = run_scenario(
        borrowers           = borrowers,
        initial_eth_price   = float(eth_price),
        price_shock_pct     = price_shock / 100.0,
        liquidator_capital  = float(capital),
        gas_cost_usd        = float(gas_cost),
        lenders             = lenders,
        pool                = pool,
        liquidity_shock_pct = liquidity_shock / 100.0,
        demand_surge_usdc   = float(demand_surge),
        price_feedback      = enable_feedback,
        market_depth_usd    = float(market_depth),
        strategy            = strategy,
    )

    before = result["before"]
    after  = result["after"]
    ls     = result["liquidator_stats"]

    # ── Metrics hàng đầu ─────────────────────────────────────────────────────
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Giá ETH cuối cùng",
                f"${after['eth_price']:,.2f}",
                f"Ban đầu: ${eth_price:,.0f}")
    col2.metric("Vị thế bị thanh lý",
                f"{after['n_touched']} / {after['n_borrowers']}",
                f"{after['touched_rate_pct']}%")
    col3.metric("Vị thế còn mất an toàn",
                f"{after['n_still_unsafe']}", delta_color="inverse")
    col4.metric("Realized Bad Debt",
                f"${after['total_realized_bad_debt']:,.2f}", delta_color="inverse")
    col5.metric("Lợi nhuận Liquidator", f"${ls['total_profit']:,.2f}")
    col6.metric("Liquidation Coverage",
                f"{result['liquidation_coverage']*100:.1f}%")

    # ── Pool metrics ──────────────────────────────────────────────────────────
    if after.get("utilization") is not None:
        st.subheader("💧 Trạng thái Lending Pool")
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Utilization",
                   f"{after['utilization']*100:.2f}%",
                   f"Trước: {before.get('utilization', 0)*100:.2f}%")
        pc2.metric("Available Liquidity",
                   f"${after['available_liquidity_usdc']:,.0f}")
        pc3.metric("Borrow Rate",
                   f"{after['borrow_rate_annual']:.2f}%/năm")
        pc4.metric("Supply Rate",
                   f"{after['supply_rate_annual']:.2f}%/năm")

        if result.get("withdrawal_fulfillment") is not None:
            wf = result["withdrawal_fulfillment"]
            st.info(f"**Withdrawal Fulfillment:** {wf*100:.1f}% — "
                    f"{'✅ Đáp ứng đủ' if wf >= 1.0 else '⚠️ Không đáp ứng đủ yêu cầu rút'}")

    # ── Lãi suất kink chart ───────────────────────────────────────────────────
    with st.expander("📐 Mô hình lãi suất kink (Borrow Rate theo Utilization)"):
        u_range = [i / 100 for i in range(0, 101)]
        df_rate = pd.DataFrame({
            "Utilization (%)":    [u * 100 for u in u_range],
            "Borrow Rate (%/yr)": [borrow_rate(u) * 100 for u in u_range],
            "Supply Rate (%/yr)": [supply_rate(u) * 100 for u in u_range],
        }).set_index("Utilization (%)")
        st.line_chart(df_rate)
        st.caption("Giả định nghiên cứu — tham khảo cơ chế Aave V3. "
                   "Nhóm cần đối chiếu tham số thực tế trước khi nộp.")

    # ── Price cascade chart ───────────────────────────────────────────────────
    if enable_feedback and len(result["price_history"]) > 1:
        st.subheader("📉 Diễn biến giá ETH qua các vòng thanh lý (Cascade)")
        st.line_chart(pd.DataFrame({"Giá ETH ($)": result["price_history"]}))

    # ── Bảng so sánh Trước vs Sau ─────────────────────────────────────────────
    st.subheader("📊 Bảng so sánh chỉ số Trước vs Sau thanh lý")
    comparison_rows = [
        ("Số vị thế HF < 1 (Nguy hiểm)",         before["n_undercollateralized"],    after["n_undercollateralized"]),
        ("Số borrower bị thanh lý (Touched)",      before["n_touched"],                after["n_touched"]),
        ("Số borrower trả hết nợ (Repaid)",        before["n_repaid"],                 after["n_repaid"]),
        ("Số borrower vỡ nợ (Defaulted)",          before["n_defaulted"],              after["n_defaulted"]),
        ("Số borrower còn nguy hiểm (Still Unsafe)",before["n_still_unsafe"],          after["n_still_unsafe"]),
        ("Tổng giá trị tài sản thế chấp ($)",
         f"${before['total_collateral_value_usd']:,.0f}",
         f"${after['total_collateral_value_usd']:,.0f}"),
        ("Tổng dư nợ còn lại ($)",
         f"${before['total_remaining_debt']:,.0f}",
         f"${after['total_remaining_debt']:,.0f}"),
        ("Realized Bad Debt ($)",
         f"${before['total_realized_bad_debt']:,.2f}",
         f"${after['total_realized_bad_debt']:,.2f}"),
        ("Projected Deficit ($)",
         f"${before['total_projected_deficit']:,.2f}",
         f"${after['total_projected_deficit']:,.2f}"),
        ("Tỷ lệ bị thanh lý (%)",
         f"{before['touched_rate_pct']}%",
         f"{after['touched_rate_pct']}%"),
        ("Tỷ lệ hoàn trả hết nợ (%)",
         f"{before['repaid_rate_pct']}%",
         f"{after['repaid_rate_pct']}%"),
        ("Liquidation Coverage",
         "—",
         f"{result['liquidation_coverage']*100:.1f}%"),
    ]

    # Thêm hàng pool nếu có
    if after.get("utilization") is not None:
        comparison_rows += [
            ("Utilization (%)",
             f"{before.get('utilization', 0)*100:.2f}%",
             f"{after['utilization']*100:.2f}%"),
            ("Available Liquidity ($)",
             f"${before.get('available_liquidity_usdc', 0):,.0f}",
             f"${after['available_liquidity_usdc']:,.0f}"),
            ("Borrow Rate (%/yr)",
             f"{before.get('borrow_rate_annual', 0):.2f}%",
             f"{after['borrow_rate_annual']:.2f}%"),
        ]

    st.table(pd.DataFrame(comparison_rows,
                          columns=["Chỉ số đánh giá", "Trước thanh lý", "Sau thanh lý"]))

    # ── Thống kê Liquidator ───────────────────────────────────────────────────
    st.subheader("⚡ Thống kê hoạt động Liquidator")
    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.info(f"**Số lần thanh lý thành công:** {ls['liquidation_count']}")
    lc2.warning(f"**Bỏ qua do không có lãi (Gas cao):** {ls['failed_no_profit']}")
    lc3.error(f"**Bỏ qua do thiếu vốn:** {ls['failed_no_capital']}")
    lc4.success(f"**Vốn Liquidator còn lại:** ${ls['final_capital_usdc']:,.2f}")

    # ── Log chi tiết ─────────────────────────────────────────────────────────
    if result["liquidation_log"]:
        st.subheader("📝 Lịch sử chi tiết các lượt thanh lý")
        df_log = pd.DataFrame(result["liquidation_log"])
        success_logs = df_log[df_log["success"] == True]
        if not success_logs.empty:
            display_cols = [c for c in [
                "round", "borrower_id", "eth_price", "debt_repaid",
                "eth_received", "gross_profit_usd", "net_profit_usd",
                "bad_debt_created",
            ] if c in success_logs.columns]
            st.dataframe(success_logs[display_cols], use_container_width=True)
        else:
            st.info("Không có giao dịch thanh lý nào thành công.")
