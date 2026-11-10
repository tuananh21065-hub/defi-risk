"""
metrics.py — Tính chỉ số đánh giá sau mô phỏng

Phân loại borrower (3 trạng thái loại trừ nhau):
  - ACTIVE:    còn nợ, chưa đóng vị thế
  - REPAID:    nợ về 0, không phát sinh bad debt
  - DEFAULTED: vỡ nợ — collateral cạn trước khi hết nợ → realized_bad_debt > 0

Lưu ý phân biệt:
  - n_repaid ≠ n_defaulted (tuy cả hai đều có debt_usdc = 0)
  - n_still_unsafe: HF < 1 sau tất cả vòng thanh lý → vị thế nguy hiểm chưa được xử lý
  - total_projected_deficit: ước tính (chưa thực hiện thanh lý)
  - total_realized_bad_debt: đã thực sự xảy ra (collateral đã cạn)
"""
from __future__ import annotations
from typing import List
from model import Borrower


def compute_metrics(borrowers: List[Borrower], eth_price: float) -> dict:
    n = len(borrowers)
    if n == 0:
        return {}

    n_touched    = sum(1 for b in borrowers if b.is_touched)
    n_repaid     = sum(1 for b in borrowers if b.is_repaid)
    n_defaulted  = sum(1 for b in borrowers if b.is_defaulted)
    n_still_unsafe = sum(
        1 for b in borrowers
        if not b.is_closed and b.is_undercollateralized(eth_price)
    )
    # HF < 1 tại thời điểm snapshot (kể cả active và chưa xử lý)
    n_undercollateralized = sum(
        1 for b in borrowers
        if not b.is_closed and b.is_undercollateralized(eth_price)
    )

    total_col_usd    = sum(b.collateral_value_usd(eth_price) for b in borrowers)
    total_debt       = sum(b.debt_usdc for b in borrowers)
    total_bad_debt   = sum(b.realized_bad_debt for b in borrowers)
    total_projected  = sum(b.projected_liquidation_deficit(eth_price) for b in borrowers)

    touched_rate   = (n_touched   / n * 100) if n > 0 else 0.0
    repaid_rate    = (n_repaid    / n * 100) if n > 0 else 0.0
    defaulted_rate = (n_defaulted / n * 100) if n > 0 else 0.0

    return {
        "eth_price": round(eth_price, 2),
        "n_borrowers": n,
        # --- Trạng thái ---
        "n_undercollateralized": n_undercollateralized,
        "n_touched": n_touched,
        "n_repaid": n_repaid,
        "n_defaulted": n_defaulted,
        "n_still_unsafe": n_still_unsafe,
        # --- Tài chính ---
        "total_collateral_value_usd": round(total_col_usd, 2),
        "total_remaining_debt": round(total_debt, 2),
        "total_realized_bad_debt": round(total_bad_debt, 2),
        "total_projected_deficit": round(total_projected, 2),
        # --- Tỷ lệ ---
        "touched_rate_pct": round(touched_rate, 2),
        "repaid_rate_pct": round(repaid_rate, 2),
        "defaulted_rate_pct": round(defaulted_rate, 2),
    }
