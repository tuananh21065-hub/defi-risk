"""
simulation.py — Vòng mô phỏng: sốc giá, chạy thanh lý, ghi log

Luồng:
1. Nhận danh sách Borrower và tham số kịch bản
2. Áp dụng sốc giá ETH ban đầu
3. Mỗi vòng: chạy Liquidator qua tất cả vị thế còn HF < 1
4. (Nếu bật price_feedback) Cập nhật giá ETH dựa trên lượng ETH bán ra
   theo mô hình tác động giá tuyến tính (giả định nghiên cứu)
5. Dừng khi không còn thanh lý thành công hoặc đạt max_rounds

Price feedback — Giả định và cơ sở lựa chọn:
  Công thức: Δprice_pct = -(eth_sold × eth_price) / market_depth_usd
  Ý nghĩa market_depth_usd:
    Đại diện cho tổng giá trị thanh khoản thị trường (USD) có thể hấp thụ lệnh bán
    mà không gây biến động giá. Khi ETH bán ra chiếm phần lớn thanh khoản → giá
    giảm nhiều hơn.
  Các mức tham khảo (giả định nghiên cứu):
    - $50M: thị trường sâu, impact nhỏ (ví dụ: giai đoạn thị trường bình thường)
    - $10M: thị trường trung bình
    - $2M:  thị trường kém thanh khoản (ví dụ: giai đoạn stress)
    - $500K: thị trường rất mỏng (cực đoan)
  Giới hạn: mô hình tuyến tính này không phản ánh đúng AMM thực tế (constant product,
  concentrated liquidity…). Chỉ dùng để so sánh xu hướng định tính.

Lợi nhuận liquidator và slippage:
  Trong mỗi vòng, liquidator bán ETH tại giá hiện tại (eth_price) TRƯỚC khi
  price impact được áp dụng cho vòng tiếp theo. Điều này phản ánh thực tế:
  liquidator giao dịch trong vòng hiện tại, còn price impact lan ra ở vòng sau.
  Slippage cục bộ trong cùng một lệnh (intra-round) hiện chưa được mô hình hóa
  — đây là giới hạn đã được ghi nhận trong model_spec.md.
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
    market_depth_usd: float = 10_000_000.0,
) -> dict:
    """
    Chạy một kịch bản mô phỏng và trả về kết quả đầy đủ.

    Args:
        borrowers:          danh sách Borrower gốc (sẽ được deep copy)
        initial_eth_price:  giá ETH trước khi sốc
        price_shock_pct:    mức sốc giá ngoại sinh, ví dụ -0.20 là giảm 20%
        liquidator_capital: vốn USDC ban đầu của liquidator
        gas_cost_usd:       chi phí gas mỗi lần thanh lý (USD)
        max_rounds:         số vòng tối đa để tránh vòng lặp vô hạn
        price_feedback:     True = bật cơ chế cascade (giá giảm thêm do bán ETH)
        market_depth_usd:   thanh khoản thị trường (USD); chỉ dùng khi price_feedback=True

    Returns:
        dict với params, before/after metrics, liquidation_log, liquidator_stats,
        price_history, rounds_run
    """
    borrowers_copy = [copy.deepcopy(b) for b in borrowers]
    eth_price = initial_eth_price * (1 + price_shock_pct)

    liquidator = Liquidator(capital_usdc=liquidator_capital, gas_cost_usd=gas_cost_usd)
    before_metrics = compute_metrics(borrowers_copy, eth_price)
    liquidation_log = []
    price_history = [round(eth_price, 2)]
    rounds_run = 0  # biến đếm vòng riêng, độc lập với price_history

    for round_num in range(max_rounds):
        rounds_run += 1
        eth_sold_this_round = 0.0
        any_success = False

        for borrower in borrowers_copy:
            if borrower.is_closed:
                continue
            if borrower.is_undercollateralized(eth_price):
                # Liquidator bán ETH tại giá hiện tại (trước khi price impact vòng này)
                result = liquidator.attempt_liquidation(
                    borrower, eth_price=eth_price, sell_price=eth_price
                )
                result["round"] = round_num + 1
                result["eth_price"] = round(eth_price, 2)
                liquidation_log.append(result)
                if result["success"]:
                    any_success = True
                    eth_sold_this_round += result["eth_received"]

        # --- Price feedback: giá giảm do liquidator bán ETH ra thị trường ---
        # Áp dụng SAU khi tất cả thanh lý trong vòng này hoàn tất
        if price_feedback and eth_sold_this_round > 0:
            price_impact_pct = (eth_sold_this_round * eth_price) / market_depth_usd
            eth_price = max(eth_price * (1 - price_impact_pct), 1.0)  # sàn $1
            price_history.append(round(eth_price, 2))

        if not any_success:
            break

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
        "rounds_run": rounds_run,
    }
