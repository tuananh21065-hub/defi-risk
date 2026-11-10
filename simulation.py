"""
simulation.py — Vòng mô phỏng: sốc giá, chạy thanh lý, ghi log

Luồng:
1. Nhận danh sách Borrower và tham số kịch bản
2. Áp dụng sốc giá ETH ban đầu
3. Mỗi vòng: chạy Liquidator qua tất cả vị thế còn HF < 1
4. (Nếu bật price_feedback) Cập nhật giá ETH dựa trên lượng ETH bán ra
   và market_depth — sau đó kiểm tra lại HF toàn bộ danh mục
5. Dừng khi không còn thanh lý thành công hoặc đạt max_rounds

Price feedback (cơ chế liquidation cascade):
  Δprice = -(eth_sold * eth_price) / market_depth
  Giá trị market_depth (USD) đại diện cho thanh khoản thị trường:
  - Cao (~50M USD): thị trường hấp thụ tốt, impact nhỏ
  - Thấp (~1M USD): thị trường kém thanh khoản, bán ETH gây giảm giá lớn
  Đây là giả định nghiên cứu (tuyến tính), không phải mô hình AMM đầy đủ.

Lưu ý: price_feedback=False → chỉ mô phỏng cú sốc ban đầu (scenario analysis).
        price_feedback=True  → mô phỏng cơ chế cascade (liquidation spiral).
"""
from __future__ import annotations
import copy
from typing import List
from model import Borrower
from liquidation import Liquidator
from metrics import compute_metrics


def run_scenario(
    borrowers: List[Borrower],
    initial_eth_price: float,
    price_shock_pct: float,
    liquidator_capital: float,
    gas_cost_usd: float,
    max_rounds: int = 20,
    price_feedback: bool = False,
    market_depth_usd: float = 10_000_000.0,  # USD — thanh khoản thị trường
) -> dict:
    """
    Chạy một kịch bản mô phỏng và trả về kết quả đầy đủ.

    Args:
        borrowers: danh sách Borrower gốc (sẽ được deep copy)
        initial_eth_price: giá ETH trước khi sốc
        price_shock_pct: mức sốc giá, ví dụ -0.20 là giảm 20%
        liquidator_capital: vốn USDC ban đầu của liquidator
        gas_cost_usd: chi phí gas mỗi lần thanh lý (USD)
        max_rounds: số vòng tối đa để tránh vòng lặp vô hạn
        price_feedback: True = bật cơ chế cascade (giá giảm thêm do bán ETH)
        market_depth_usd: thanh khoản thị trường (USD); chỉ dùng khi price_feedback=True

    Returns:
        dict với params, before/after metrics, liquidation_log, liquidator_stats,
        price_history (nếu feedback bật)
    """
    borrowers_copy = [copy.deepcopy(b) for b in borrowers]
    eth_price = initial_eth_price * (1 + price_shock_pct)

    liquidator = Liquidator(capital_usdc=liquidator_capital, gas_cost_usd=gas_cost_usd)
    before_metrics = compute_metrics(borrowers_copy, eth_price)
    liquidation_log = []
    price_history = [eth_price]

    for round_num in range(max_rounds):
        eth_sold_this_round = 0.0
        any_success = False

        for borrower in borrowers_copy:
            if borrower.is_fully_repaid:
                continue
            if borrower.is_undercollateralized(eth_price):
                result = liquidator.attempt_liquidation(borrower, eth_price)
                result["round"] = round_num + 1
                result["eth_price"] = round(eth_price, 2)
                liquidation_log.append(result)
                if result["success"]:
                    any_success = True
                    eth_sold_this_round += result["eth_received"]

        # --- Price feedback: giá giảm do liquidator bán ETH ra thị trường ---
        if price_feedback and eth_sold_this_round > 0:
            # Mô hình tuyến tính: Δprice = -(ETH_bán × giá) / market_depth
            price_impact = (eth_sold_this_round * eth_price) / market_depth_usd
            eth_price = max(eth_price * (1 - price_impact), 1.0)  # sàn $1 để tránh ÷0
            price_history.append(round(eth_price, 2))

        if not any_success:
            break  # không còn thanh lý nào, dừng

    after_metrics = compute_metrics(borrowers_copy, eth_price)

    return {
        "params": {
            "initial_eth_price": initial_eth_price,
            "price_shock_pct": price_shock_pct,
            "post_shock_eth_price": round(initial_eth_price * (1 + price_shock_pct), 2),
            "final_eth_price": round(eth_price, 2),
            "liquidator_capital": liquidator_capital,
            "gas_cost_usd": gas_cost_usd,
            "price_feedback": price_feedback,
            "market_depth_usd": market_depth_usd if price_feedback else None,
            "rounds_run": len(price_history),
        },
        "before": before_metrics,
        "after": after_metrics,
        "liquidation_log": liquidation_log,
        "liquidator_stats": {
            "final_capital_usdc": round(liquidator.capital_usdc, 2),
            "total_profit": round(liquidator.total_profit, 2),
            "liquidation_count": liquidator.liquidation_count,
            "failed_no_profit": liquidator.failed_no_profit,
            "failed_no_capital": liquidator.failed_no_capital,
            "eth_received_total": round(liquidator.eth_received_total, 6),
        },
        "price_history": price_history,
    }
