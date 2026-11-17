# -*- coding: utf-8 -*-
"""
metrics.py — Tính chỉ số đánh giá sau mô phỏng

Chỉ tiêu theo doc nghiên cứu (Chương 4.5.3):
  S0/S1: HF, n_undercollateralized, bad debt, liquidation coverage
  S2:    Available Liquidity, Withdrawal Fulfillment
  S3:    Utilization, Borrow Rate, Supply APY, Available Liquidity
  S4:    Liquidation Success Rate, net profit Liquidator
  S5:    Tổng hợp

Phân loại borrower (3 trạng thái loại trừ nhau):
  ACTIVE    — còn nợ, chưa đóng vị thế
  REPAID    — nợ về 0, không phát sinh bad debt
  DEFAULTED — vỡ nợ — collateral cạn trước khi hết nợ

Lưu ý:
  - n_repaid ≠ n_defaulted (tuy cả hai đều có debt_usdc = 0)
  - n_still_unsafe: HF < 1 sau tất cả vòng → vị thế nguy hiểm chưa xử lý
  - liquidation_coverage = n_touched / n_eligible_before (nếu có)
  - withdrawal_fulfillment = phần yêu cầu rút được đáp ứng
"""
from __future__ import annotations
from typing import List, Optional
from model import Borrower, LendingPool, borrow_rate, supply_rate


def compute_metrics(
    borrowers: List[Borrower],
    eth_price: float,
    pool: Optional[LendingPool] = None,
) -> dict:
    """
    Tính toàn bộ chỉ số đánh giá.

    Args:
        borrowers: danh sách Borrower tại thời điểm snapshot
        eth_price: giá ETH tại thời điểm snapshot
        pool:      LendingPool (nếu có) để tính utilization, liquidity, lãi suất
    """
    n = len(borrowers)
    if n == 0:
        return {}

    # ── Trạng thái Borrower ──────────────────────────────────────────────────
    n_touched         = sum(1 for b in borrowers if b.is_touched)
    n_repaid          = sum(1 for b in borrowers if b.is_repaid)
    n_defaulted       = sum(1 for b in borrowers if b.is_defaulted)
    n_still_unsafe    = sum(
        1 for b in borrowers
        if not b.is_closed and b.is_undercollateralized(eth_price)
    )
    n_undercollateralized = n_still_unsafe  # alias rõ nghĩa hơn

    # ── Tài chính Borrower ───────────────────────────────────────────────────
    total_col_usd   = sum(b.collateral_value_usd(eth_price) for b in borrowers)
    total_debt      = sum(b.debt_usdc for b in borrowers)
    total_bad_debt  = sum(b.realized_bad_debt for b in borrowers)
    total_projected = sum(b.projected_liquidation_deficit(eth_price) for b in borrowers)

    # ── Tỷ lệ ────────────────────────────────────────────────────────────────
    touched_rate   = n_touched   / n * 100
    repaid_rate    = n_repaid    / n * 100
    defaulted_rate = n_defaulted / n * 100

    result = {
        "eth_price":    round(eth_price, 2),
        "n_borrowers":  n,
        # Trạng thái
        "n_undercollateralized": n_undercollateralized,
        "n_touched":             n_touched,
        "n_repaid":              n_repaid,
        "n_defaulted":           n_defaulted,
        "n_still_unsafe":        n_still_unsafe,
        # Tài chính
        "total_collateral_value_usd": round(total_col_usd, 2),
        "total_remaining_debt":       round(total_debt, 2),
        "total_realized_bad_debt":    round(total_bad_debt, 2),
        "total_projected_deficit":    round(total_projected, 2),
        # Tỷ lệ
        "touched_rate_pct":   round(touched_rate, 2),
        "repaid_rate_pct":    round(repaid_rate, 2),
        "defaulted_rate_pct": round(defaulted_rate, 2),
        # Pool (mặc định None nếu không có pool)
        "utilization":              None,
        "available_liquidity_usdc": None,
        "borrow_rate_annual":       None,
        "supply_rate_annual":       None,
        "total_supplied_usdc":      None,
        "pool_bad_debt":            None,
    }

    # ── Chỉ tiêu LendingPool (S2, S3) ────────────────────────────────────────
    if pool is not None:
        u = pool.utilization
        result.update({
            "utilization":              round(u, 4),
            "available_liquidity_usdc": round(pool.available_liquidity_usdc, 2),
            "borrow_rate_annual":       round(borrow_rate(u) * 100, 4),   # %/năm
            "supply_rate_annual":       round(supply_rate(u) * 100, 4),   # %/năm
            "total_supplied_usdc":      round(pool.total_supplied_usdc, 2),
            "pool_bad_debt":            round(pool.realized_bad_debt, 2),
        })

    return result


def compute_withdrawal_fulfillment(
    pool: LendingPool,
    total_withdrawal_requests: float,
) -> float:
    """
    Tỷ lệ đáp ứng yêu cầu rút tiền (Withdrawal Fulfillment).
    = min(available_liquidity, requested) / requested
    Chỉ tiêu trọng tâm cho kịch bản S2 (cú sốc thanh khoản).
    """
    return pool.withdrawal_fulfillment(total_withdrawal_requests)


def compute_liquidation_coverage(
    n_eligible_before: int,
    n_touched_after: int,
) -> float:
    """
    Liquidation Coverage = số vị thế được xử lý / số vị thế đủ điều kiện ban đầu.
    Chỉ tiêu trọng tâm cho kịch bản S1 (cú sốc giá) và S5 (cú sốc kết hợp).
    """
    if n_eligible_before <= 0:
        return 1.0
    return min(1.0, n_touched_after / n_eligible_before)
