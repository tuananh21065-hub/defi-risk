"""
metrics.py — Tính chỉ số đánh giá sau mô phỏng
"""
from __future__ import annotations
from typing import List
from model import Borrower, LIQUIDATION_THRESHOLD

def compute_metrics(borrowers: List[Borrower], eth_price: float) -> dict:
    """
    Tính toàn bộ chỉ số cho một snapshot tại eth_price.
    
    Returns dict với:
      - n_borrowers: tổng số người vay
      - n_undercollateralized: HF < 1
      - n_liquidated: đã thanh lý hoàn toàn
      - total_collateral_value_usd: tổng giá trị thế chấp
      - total_debt_usdc: tổng dư nợ
      - total_shortfall: tổng thiếu hụt
      - liquidation_rate: tỷ lệ % được thanh lý
    """
    n = len(borrowers)
    n_under = sum(1 for b in borrowers if not b.is_liquidated and b.is_undercollateralized(eth_price))
    n_liq = sum(1 for b in borrowers if b.is_liquidated)
    total_col = sum(b.collateral_eth * eth_price for b in borrowers)
    total_debt = sum(b.debt_usdc for b in borrowers)
    total_shortfall = sum(b.shortfall for b in borrowers)
    liq_rate = (n_liq / n * 100) if n > 0 else 0.0

    return {
        "eth_price": eth_price,
        "n_borrowers": n,
        "n_undercollateralized": n_under,
        "n_liquidated": n_liq,
        "total_collateral_value_usd": round(total_col, 2),
        "total_debt_usdc": round(total_debt, 2),
        "total_shortfall": round(total_shortfall, 2),
        "liquidation_rate_pct": round(liq_rate, 2),
    }
