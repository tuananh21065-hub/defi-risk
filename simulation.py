"""
simulation.py — Vòng mô phỏng: sốc giá, chạy thanh lý, ghi log

Luồng:
1. Nhận danh sách Borrower và tham số kịch bản
2. Áp dụng sốc giá ETH
3. Chạy Liquidator qua tất cả vị thế
4. Ghi log kết quả từng bước
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
    price_shock_pct: float,       # ví dụ -0.20 là giảm 20%
    liquidator_capital: float,
    gas_cost_usd: float,
    max_rounds: int = 10,
    price_feedback: bool = False,  # SHOULD: feedback giá từ AMM
    feedback_coefficient: float = 0.0,
) -> dict:
    """
    Chạy một kịch bản mô phỏng và trả về kết quả.

    Returns:
        dict với metrics trước/sau, log thanh lý, tham số đầu vào
    """
    # Deep copy để không làm thay đổi dữ liệu gốc
    borrowers_copy = [copy.deepcopy(b) for b in borrowers]
    eth_price = initial_eth_price * (1 + price_shock_pct)

    liquidator = Liquidator(capital_usdc=liquidator_capital, gas_cost_usd=gas_cost_usd)

    before_metrics = compute_metrics(borrowers_copy, eth_price)
    liquidation_log = []

    for round_num in range(max_rounds):
        any_liquidated = False
        for borrower in borrowers_copy:
            if borrower.is_liquidated:
                continue
            if borrower.is_undercollateralized(eth_price):
                result = liquidator.attempt_liquidation(borrower, eth_price)
                result["round"] = round_num + 1
                result["eth_price"] = eth_price
                liquidation_log.append(result)
                if result["success"]:
                    any_liquidated = True

        # SHOULD: Price feedback — giá giảm thêm do bán ETH
        if price_feedback and feedback_coefficient > 0 and any_liquidated:
            eth_price = eth_price * (1 - feedback_coefficient)

        if not any_liquidated:
            break  # không còn giao dịch, dừng

    after_metrics = compute_metrics(borrowers_copy, eth_price)

    return {
        "params": {
            "initial_eth_price": initial_eth_price,
            "price_shock_pct": price_shock_pct,
            "final_eth_price": eth_price,
            "liquidator_capital": liquidator_capital,
            "gas_cost_usd": gas_cost_usd,
            "price_feedback": price_feedback,
        },
        "before": before_metrics,
        "after": after_metrics,
        "liquidation_log": liquidation_log,
        "liquidator_stats": {
            "total_profit": liquidator.total_profit,
            "liquidation_count": liquidator.liquidation_count,
            "failed_count": liquidator.failed_count,
        },
    }
