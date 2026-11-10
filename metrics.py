"""
metrics.py — Tính chỉ số đánh giá sau mô phỏng

Phân biệt rõ ba loại chỉ số:

1. Chỉ số trạng thái borrower:
   - n_undercollateralized: đang HF < 1 (tại thời điểm snapshot)
   - n_touched: đã bị thanh lý ít nhất một lần (kể cả một phần)
   - n_fully_repaid: đã trả hết nợ (vị thế đóng hoàn toàn)
   - n_still_unsafe: HF < 1 sau tất cả các vòng thanh lý (chưa được xử lý)

2. Chỉ số tài chính:
   - total_collateral_value_usd: tổng giá trị thế chấp còn lại
   - total_remaining_debt: tổng nợ còn lại
   - total_realized_bad_debt: nợ thực sự không thể thu hồi (collateral đã cạn)
   - total_projected_deficit: ước tính nợ không thu hồi được nếu liquidate hết bây giờ

3. Tỷ lệ:
   - touched_rate_pct: % borrower đã bị thanh lý ít nhất một lần
   - fully_repaid_rate_pct: % borrower đã đóng vị thế hoàn toàn
"""
from __future__ import annotations
from typing import List
from model import Borrower, LIQUIDATION_THRESHOLD


def compute_metrics(borrowers: List[Borrower], eth_price: float) -> dict:
    n = len(borrowers)
    if n == 0:
        return {}

    n_under = sum(
        1 for b in borrowers
        if not b.is_fully_repaid and b.is_undercollateralized(eth_price)
    )
    n_touched = sum(1 for b in borrowers if b.is_touched)
    n_fully_repaid = sum(1 for b in borrowers if b.is_fully_repaid)
    # Vẫn còn HF < 1 sau tất cả vòng thanh lý → chưa được xử lý
    n_still_unsafe = sum(
        1 for b in borrowers
        if not b.is_fully_repaid and b.is_undercollateralized(eth_price)
    )

    total_col_usd = sum(b.collateral_value_usd(eth_price) for b in borrowers)
    total_debt = sum(b.debt_usdc for b in borrowers)
    total_bad_debt = sum(b.realized_bad_debt for b in borrowers)
    total_projected = sum(b.projected_liquidation_deficit(eth_price) for b in borrowers)

    touched_rate = (n_touched / n * 100) if n > 0 else 0.0
    repaid_rate = (n_fully_repaid / n * 100) if n > 0 else 0.0

    return {
        "eth_price": round(eth_price, 2),
        "n_borrowers": n,
        # --- Trạng thái borrower ---
        "n_undercollateralized": n_under,
        "n_touched": n_touched,
        "n_fully_repaid": n_fully_repaid,
        "n_still_unsafe": n_still_unsafe,
        # --- Tài chính ---
        "total_collateral_value_usd": round(total_col_usd, 2),
        "total_remaining_debt": round(total_debt, 2),
        "total_realized_bad_debt": round(total_bad_debt, 2),
        "total_projected_deficit": round(total_projected, 2),
        # --- Tỷ lệ ---
        "touched_rate_pct": round(touched_rate, 2),
        "fully_repaid_rate_pct": round(repaid_rate, 2),
    }
