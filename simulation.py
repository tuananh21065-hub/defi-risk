# -*- coding: utf-8 -*-
"""
simulation.py — Vòng mô phỏng: sốc giá/thanh khoản/lãi suất, chạy thanh lý

Luồng:
  1. Nhận danh sách Borrower, Lender, LendingPool và tham số kịch bản
  2. Áp dụng sốc ngoại sinh (giá, thanh khoản, lãi suất)
  3. Nếu strategy='adaptive': Borrower và Lender ra quyết định thích nghi
  4. Mỗi vòng: Liquidator xử lý tất cả vị thế HF < 1
  5. (Nếu bật price_feedback) Cập nhật giá ETH do bán ETH ra thị trường
  6. Áp dụng lãi suất cho pool theo bước thời gian
  7. Dừng khi không còn thanh lý thành công hoặc đạt max_rounds

Giả định price impact (tuyến tính, nghiên cứu):
  Δprice_pct = -(eth_sold * eth_price) / market_depth_usd
  Không phải mô hình AMM thực tế. Chỉ dùng để so sánh xu hướng định tính.
  Nguồn: Chaudhary & Pinna (2022) cũng dùng hàm slippage giả định.

Strategy:
  'fixed'    — Borrower và Lender không tự điều chỉnh
  'adaptive' — Borrower và Lender ra quyết định thích nghi theo RA và điều kiện
"""
from __future__ import annotations
import copy
from typing import List, Optional
from model import Borrower, Lender, LendingPool
from liquidation import Liquidator
from metrics import compute_metrics, compute_liquidation_coverage


def run_scenario(
    borrowers:          List[Borrower],
    initial_eth_price:  float,
    price_shock_pct:    float,
    liquidator_capital: float,
    gas_cost_usd:       float,
    # Pool / Lender
    lenders:            Optional[List[Lender]] = None,
    pool:               Optional[LendingPool]  = None,
    # Cú sốc thanh khoản (S2)
    liquidity_shock_pct: float = 0.0,     # % lender rút ngay lập tức
    # Cú sốc lãi suất (S3): tăng utilization nhân tạo bằng cách thêm vay
    demand_surge_usdc:   float = 0.0,     # USDC vay thêm do nhu cầu tăng
    # Cascade
    max_rounds:          int   = 20,
    price_feedback:      bool  = False,
    market_depth_usd:    float = 10_000_000.0,
    # Strategy
    strategy:            str   = "fixed",   # 'fixed' hoặc 'adaptive'
    # Bước thời gian cho lãi suất
    dt_years:            float = 1/365,
) -> dict:
    """
    Chạy một thực nghiệm (E1–E12) và trả về kết quả đầy đủ.

    Args:
        borrowers:           danh sách Borrower gốc (deep copy bên trong)
        initial_eth_price:   giá ETH trước sốc
        price_shock_pct:     sốc giá ngoại sinh (-0.20 = giảm 20%)
        liquidator_capital:  vốn USDC ban đầu của Liquidator
        gas_cost_usd:        chi phí gas mỗi lần thanh lý (USD)
        lenders:             danh sách Lender (None = không dùng pool)
        pool:                LendingPool (None = tạo tự động từ lenders+borrowers)
        liquidity_shock_pct: % lender rút ngay → giảm total_supplied (S2)
        demand_surge_usdc:   USDC vay thêm → tăng total_debt (S3)
        max_rounds:          vòng tối đa tránh vòng lặp vô hạn
        price_feedback:      True = bật cascade
        market_depth_usd:    độ sâu thị trường (chỉ dùng khi price_feedback=True)
        strategy:            'fixed' hoặc 'adaptive'
        dt_years:            bước thời gian cho lãi suất (mặc định 1 ngày)

    Returns:
        dict với params, before/after metrics, liquidation_log, liquidator_stats,
        price_history, rounds_run, pool_metrics
    """
    # Deep copy để không ảnh hưởng dữ liệu gốc
    borrowers_copy = [copy.deepcopy(b) for b in borrowers]
    lenders_copy   = [copy.deepcopy(l) for l in lenders] if lenders else []

    # Tạo pool nếu chưa có
    if pool is not None:
        pool_copy = copy.deepcopy(pool)
    elif lenders_copy:
        pool_copy = LendingPool.from_lenders_and_borrowers(lenders_copy, borrowers_copy)
    else:
        pool_copy = None

    # ── Áp dụng sốc giá ngoại sinh ───────────────────────────────────────────
    eth_price = initial_eth_price * (1.0 + price_shock_pct)

    # ── Áp dụng sốc thanh khoản (S2) ─────────────────────────────────────────
    total_withdrawal_requests = 0.0
    if pool_copy and liquidity_shock_pct > 0:
        withdrawal_amt = pool_copy.total_supplied_usdc * liquidity_shock_pct
        actual_withdraw = min(withdrawal_amt, pool_copy.available_liquidity_usdc)
        pool_copy.total_supplied_usdc -= actual_withdraw
        total_withdrawal_requests = withdrawal_amt  # ghi lại để tính fulfillment

    # ── Áp dụng cú sốc lãi suất / nhu cầu vay tăng (S3) ─────────────────────
    if pool_copy and demand_surge_usdc > 0:
        actual_surge = min(demand_surge_usdc, pool_copy.available_liquidity_usdc)
        pool_copy.total_debt_usdc += actual_surge
        # Tạo thêm debt cho borrower đại diện (phân phối đều)
        if borrowers_copy and actual_surge > 0:
            per_borrower = actual_surge / len(borrowers_copy)
            for b in borrowers_copy:
                if not b.is_closed:
                    b.debt_usdc += per_borrower

    # ── Snapshot trước thanh lý ───────────────────────────────────────────────
    before_metrics = compute_metrics(borrowers_copy, eth_price, pool_copy)
    n_eligible_before = before_metrics["n_undercollateralized"]

    liquidator   = Liquidator(capital_usdc=liquidator_capital, gas_cost_usd=gas_cost_usd)
    liq_log      = []
    price_history = [round(eth_price, 2)]
    rounds_run   = 0

    # ── Vòng lặp mô phỏng ────────────────────────────────────────────────────
    for round_num in range(max_rounds):
        rounds_run += 1
        eth_sold_this_round = 0.0
        any_success = False

        # Hành vi thích nghi của Borrower (trước khi thanh lý)
        if strategy == "adaptive" and pool_copy:
            for b in borrowers_copy:
                b.adaptive_action(eth_price, pool_copy)

        # Hành vi thích nghi của Lender
        if strategy == "adaptive" and pool_copy and lenders_copy:
            for l in lenders_copy:
                l.adaptive_action(pool_copy)

        # Thanh lý tất cả vị thế đủ điều kiện
        for borrower in borrowers_copy:
            if borrower.is_closed:
                continue
            if borrower.is_undercollateralized(eth_price):
                result = liquidator.attempt_liquidation(
                    borrower, eth_price=eth_price, sell_price=eth_price
                )
                result["round"]     = round_num + 1
                result["eth_price"] = round(eth_price, 2)
                liq_log.append(result)

                if result["success"]:
                    any_success = True
                    eth_sold_this_round += result["eth_received"]

                    # Cập nhật pool: debt giảm khi thanh lý
                    if pool_copy:
                        debt_repaid = result.get("debt_repaid", 0.0)
                        pool_copy.total_debt_usdc = max(
                            0.0, pool_copy.total_debt_usdc - debt_repaid
                        )
                        # Nếu phát sinh bad debt, ghi nhận vào pool
                        bad_debt_created = result.get("bad_debt_created", 0.0)
                        if bad_debt_created > 0:
                            pool_copy.record_bad_debt(bad_debt_created)

        # Price feedback (cascade)
        if price_feedback and eth_sold_this_round > 0:
            price_impact_pct = (eth_sold_this_round * eth_price) / market_depth_usd
            eth_price = max(eth_price * (1.0 - price_impact_pct), 1.0)
            price_history.append(round(eth_price, 2))

        # Áp dụng lãi suất cho pool
        if pool_copy:
            pool_copy.apply_interest(dt_years=dt_years)

        if not any_success:
            break

    # ── Snapshot sau thanh lý ─────────────────────────────────────────────────
    after_metrics = compute_metrics(borrowers_copy, eth_price, pool_copy)

    # ── Chỉ tiêu bổ sung ─────────────────────────────────────────────────────
    liq_coverage = compute_liquidation_coverage(
        n_eligible_before=n_eligible_before,
        n_touched_after=after_metrics["n_touched"],
    )

    withdrawal_fulfillment = None
    if pool_copy and total_withdrawal_requests > 0:
        from metrics import compute_withdrawal_fulfillment
        withdrawal_fulfillment = compute_withdrawal_fulfillment(
            pool_copy, total_withdrawal_requests
        )

    return {
        "params": {
            "initial_eth_price":   initial_eth_price,
            "price_shock_pct":     price_shock_pct,
            "post_shock_eth_price": round(initial_eth_price * (1.0 + price_shock_pct), 2),
            "final_eth_price":     round(eth_price, 2),
            "liquidator_capital":  liquidator_capital,
            "gas_cost_usd":        gas_cost_usd,
            "price_feedback":      price_feedback,
            "market_depth_usd":    market_depth_usd if price_feedback else None,
            "strategy":            strategy,
            "liquidity_shock_pct": liquidity_shock_pct,
            "demand_surge_usdc":   demand_surge_usdc,
        },
        "before":               before_metrics,
        "after":                after_metrics,
        "liquidation_log":      liq_log,
        "liquidator_stats": {
            "final_capital_usdc":   round(liquidator.capital_usdc, 2),
            "total_profit":         round(liquidator.total_profit, 2),
            "liquidation_count":    liquidator.liquidation_count,
            "failed_no_profit":     liquidator.failed_no_profit,
            "failed_no_capital":    liquidator.failed_no_capital,
            "eth_received_total":   round(liquidator.eth_received_total, 6),
        },
        "price_history":          price_history,
        "rounds_run":             rounds_run,
        "liquidation_coverage":   round(liq_coverage, 4),
        "withdrawal_fulfillment": (
            round(withdrawal_fulfillment, 4) if withdrawal_fulfillment is not None else None
        ),
    }
