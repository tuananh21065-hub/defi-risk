# -*- coding: utf-8 -*-
"""
test_model.py — Unit test: Borrower, Lender, LendingPool

Ví dụ tính tay (HF):
  Case 1 — An toàn:    col=5 ETH, debt=5000 USDC, price=2000 → HF = 5*2000*0.825/5000 = 1.65
  Case 2 — Đủ TL:      col=5 ETH, debt=9000 USDC, price=2000 → HF = 5*2000*0.825/9000 = 0.917
  Case 3 — Thiếu hụt:  col=1 ETH, debt=2000 USDC, price=1200 → HF = 1*1200*0.825/2000 = 0.495
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import (
    Borrower, Lender, LendingPool,
    LIQUIDATION_THRESHOLD, borrow_rate, supply_rate,
    INTEREST_U_OPT, INTEREST_BASE, INTEREST_SLOPE1, INTEREST_SLOPE2,
)


# ── Borrower: Health Factor ───────────────────────────────────────────────────

def test_hf_safe():
    b = Borrower.create(5.0, 5000.0)
    hf = b.health_factor(eth_price=2000.0)
    assert abs(hf - 1.65) < 0.001, f"HF={hf}"

def test_hf_undercollateralized():
    b = Borrower.create(5.0, 9000.0)
    hf = b.health_factor(eth_price=2000.0)
    assert abs(hf - 0.9167) < 0.001, f"HF={hf}"
    assert b.is_undercollateralized(2000.0)

def test_hf_severe_shortfall():
    b = Borrower.create(1.0, 2000.0)
    hf = b.health_factor(eth_price=1200.0)
    assert abs(hf - 0.495) < 0.001, f"HF={hf}"
    assert b.is_undercollateralized(1200.0)

def test_no_debt():
    b = Borrower.create(5.0, 0.0)
    assert b.health_factor(2000.0) == float("inf")

def test_collateral_non_negative_after_creation():
    b = Borrower.create(2.5, 3000.0)
    assert b.collateral_eth >= 0
    assert b.debt_usdc >= 0

def test_borrower_status_active():
    b = Borrower.create(2.0, 1000.0)
    assert b.status == "ACTIVE"
    assert not b.is_repaid
    assert not b.is_defaulted

def test_borrower_risk_appetite_stored():
    b = Borrower.create(1.0, 500.0, risk_appetite=0.8)
    assert b.risk_appetite == 0.8


# ── Lender ────────────────────────────────────────────────────────────────────

def test_lender_create():
    l = Lender.create(100_000.0, risk_appetite=0.3)
    assert l.supplied_usdc == 100_000.0
    assert l.risk_appetite == 0.3
    assert l.lender_id  # không rỗng

def test_lender_risk_appetite_range():
    for ra in [0.0, 0.5, 1.0]:
        l = Lender.create(50_000.0, risk_appetite=ra)
        assert 0.0 <= l.risk_appetite <= 1.0


# ── LendingPool ───────────────────────────────────────────────────────────────

def test_pool_utilization_basic():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=800_000.0)
    assert abs(pool.utilization - 0.80) < 1e-6

def test_pool_utilization_zero_supply():
    pool = LendingPool(total_supplied_usdc=0.0, total_debt_usdc=0.0)
    assert pool.utilization == 1.0  # sàn khi không có vốn

def test_pool_available_liquidity():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=600_000.0)
    assert abs(pool.available_liquidity_usdc - 400_000.0) < 1.0

def test_pool_available_liquidity_non_negative():
    pool = LendingPool(total_supplied_usdc=500_000.0, total_debt_usdc=700_000.0)
    assert pool.available_liquidity_usdc == 0.0

def test_pool_from_lenders_and_borrowers():
    borrowers = [Borrower.create(1.0, 10_000.0) for _ in range(3)]
    lenders   = [Lender.create(50_000.0) for _ in range(4)]
    pool = LendingPool.from_lenders_and_borrowers(lenders, borrowers)
    assert abs(pool.total_supplied_usdc - 200_000.0) < 1.0
    assert abs(pool.total_debt_usdc - 30_000.0) < 1.0

def test_pool_record_bad_debt():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=0.0)
    pool.record_bad_debt(50_000.0)
    assert abs(pool.realized_bad_debt - 50_000.0) < 1.0
    assert abs(pool.total_supplied_usdc - 950_000.0) < 1.0

def test_pool_bad_debt_does_not_go_negative():
    pool = LendingPool(total_supplied_usdc=10_000.0, total_debt_usdc=0.0)
    pool.record_bad_debt(999_999.0)  # vượt quá total_supplied
    assert pool.total_supplied_usdc >= 0.0

def test_pool_withdrawal_fulfillment_full():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=200_000.0)
    # available = 800k, request = 500k → fulfillment = 1.0
    wf = pool.withdrawal_fulfillment(500_000.0)
    assert abs(wf - 1.0) < 1e-6

def test_pool_withdrawal_fulfillment_partial():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=800_000.0)
    # available = 200k, request = 500k → fulfillment = 0.4
    wf = pool.withdrawal_fulfillment(500_000.0)
    assert abs(wf - 0.4) < 1e-6

def test_pool_withdrawal_fulfillment_no_request():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=0.0)
    assert pool.withdrawal_fulfillment(0.0) == 1.0

def test_pool_apply_interest_increases_debt():
    pool = LendingPool(total_supplied_usdc=1_000_000.0, total_debt_usdc=800_000.0)
    debt_before = pool.total_debt_usdc
    pool.apply_interest(dt_years=1/365)
    assert pool.total_debt_usdc > debt_before


# ── Mô hình lãi suất kink ────────────────────────────────────────────────────

def test_borrow_rate_at_zero():
    r = borrow_rate(0.0)
    assert abs(r - INTEREST_BASE) < 1e-6

def test_borrow_rate_at_u_opt():
    r = borrow_rate(INTEREST_U_OPT)
    expected = INTEREST_BASE + INTEREST_SLOPE1
    assert abs(r - expected) < 1e-6

def test_borrow_rate_at_full():
    r = borrow_rate(1.0)
    expected = INTEREST_BASE + INTEREST_SLOPE1 + INTEREST_SLOPE2
    assert abs(r - expected) < 1e-6

def test_borrow_rate_increases_with_utilization():
    rates = [borrow_rate(u/10) for u in range(11)]
    for i in range(len(rates)-1):
        assert rates[i] <= rates[i+1], f"Rate không tăng tại u={i/10}"

def test_supply_rate_less_than_borrow_rate():
    for u in [0.3, 0.6, 0.8, 0.95]:
        br = borrow_rate(u)
        sr = supply_rate(u)
        assert sr <= br + 1e-9, f"Supply rate {sr} > Borrow rate {br} tại u={u}"

def test_supply_rate_at_zero_util():
    # utilization=0 → không có vay → supply rate = 0
    assert abs(supply_rate(0.0)) < 1e-6
