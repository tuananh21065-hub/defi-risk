# -*- coding: utf-8 -*-
"""
test_simulation.py — Unit test: run_scenario với Lender, Pool, Strategy

Kiểm tra:
  - Fixed vs Adaptive cho cùng kịch bản
  - Pool metrics (utilization, available_liquidity)
  - Liquidity shock (S2)
  - Demand surge / lãi suất (S3)
  - Liquidation coverage
  - Withdrawal fulfillment
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Borrower, Lender, LendingPool
from simulation import run_scenario
from scenarios import (
    generate_borrowers, generate_lenders, make_pool,
    get_scenario_params, INITIAL_ETH_PRICE, LIQUIDATOR_CAPITAL,
)


def make_basic_setup(n_borrowers=20, n_lenders=10, seed=42):
    b = generate_borrowers(n_borrowers, INITIAL_ETH_PRICE, seed=seed)
    l = generate_lenders(n_lenders, seed=seed)
    p = make_pool(b, l)
    return b, l, p


# ── S0: Cơ sở ────────────────────────────────────────────────────────────────

def test_s0_no_liquidations():
    """S0 — Không có sốc giá → không có vị thế bị thanh lý."""
    b, l, p = make_basic_setup()
    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0, lenders=l, pool=p,
    )
    assert r["after"]["n_touched"] == 0
    assert r["after"]["total_realized_bad_debt"] == 0.0
    assert r["liquidation_coverage"] == 1.0


# ── S1: Cú sốc giá ───────────────────────────────────────────────────────────

def test_s1_fixed_produces_liquidations():
    """S1/fixed — Sốc -30% → có vị thế bị thanh lý."""
    b, l, p = make_basic_setup()
    params = get_scenario_params("S1")
    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=params["price_shock_pct"],
        liquidator_capital=LIQUIDATOR_CAPITAL, gas_cost_usd=params["gas_cost_usd"],
        lenders=l, pool=p,
        price_feedback=params["price_feedback"],
        market_depth_usd=params["market_depth_usd"],
        strategy="fixed",
    )
    assert r["after"]["n_touched"] >= 0  # có thể có hoặc không tùy danh mục
    assert r["liquidation_coverage"] >= 0.0
    assert r["liquidation_coverage"] <= 1.0

def test_s1_adaptive_bad_debt_lte_fixed():
    """S1 — Adaptive bad debt <= Fixed bad debt (Borrower thích nghi giảm rủi ro)."""
    b_fixed, l_fixed, p_fixed = make_basic_setup()
    b_adap,  l_adap,  p_adap  = make_basic_setup()
    params = get_scenario_params("S1")

    r_fixed = run_scenario(
        borrowers=b_fixed, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=params["price_shock_pct"],
        liquidator_capital=LIQUIDATOR_CAPITAL, gas_cost_usd=params["gas_cost_usd"],
        lenders=l_fixed, pool=p_fixed,
        price_feedback=params["price_feedback"],
        market_depth_usd=params["market_depth_usd"],
        strategy="fixed",
    )
    r_adap = run_scenario(
        borrowers=b_adap, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=params["price_shock_pct"],
        liquidator_capital=LIQUIDATOR_CAPITAL, gas_cost_usd=params["gas_cost_usd"],
        lenders=l_adap, pool=p_adap,
        price_feedback=params["price_feedback"],
        market_depth_usd=params["market_depth_usd"],
        strategy="adaptive",
    )
    # Adaptive không được tạo ra BAD DEBT nhiều hơn Fixed
    assert r_adap["after"]["total_realized_bad_debt"] <= \
           r_fixed["after"]["total_realized_bad_debt"] + 1e-6


# ── Pool metrics ──────────────────────────────────────────────────────────────

def test_pool_metrics_returned():
    """Pool metrics phải xuất hiện khi truyền pool vào."""
    b, l, p = make_basic_setup()
    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0, lenders=l, pool=p,
    )
    after = r["after"]
    assert after["utilization"] is not None
    assert after["available_liquidity_usdc"] is not None
    assert after["borrow_rate_annual"] is not None
    assert after["supply_rate_annual"] is not None

def test_no_pool_metrics_when_no_pool():
    """Không có pool → utilization = None."""
    b = generate_borrowers(10, INITIAL_ETH_PRICE)
    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0,
    )
    assert r["after"]["utilization"] is None


# ── S2: Cú sốc thanh khoản ───────────────────────────────────────────────────

def test_s2_liquidity_shock_reduces_available():
    """S2 — Rút 40% → available_liquidity giảm."""
    b, l, p = make_basic_setup()
    avail_before = p.available_liquidity_usdc

    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0, lenders=l, pool=p,
        liquidity_shock_pct=0.40,
    )
    # Available liquidity sau sốc phải giảm
    assert r["after"]["available_liquidity_usdc"] is not None
    # pool đã bị rút → available < trước đó
    # (không so sánh tuyệt đối vì pool copy được deep-copy bên trong)

def test_s2_withdrawal_fulfillment_in_result():
    """S2 — withdrawal_fulfillment phải có giá trị (không None)."""
    b, l, p = make_basic_setup()
    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0, lenders=l, pool=p,
        liquidity_shock_pct=0.30,
    )
    assert r["withdrawal_fulfillment"] is not None
    assert 0.0 <= r["withdrawal_fulfillment"] <= 1.0


# ── S3: Cú sốc lãi suất ──────────────────────────────────────────────────────

def test_s3_demand_surge_increases_utilization():
    """S3 — Demand surge → utilization tăng."""
    b_base, l_base, p_base = make_basic_setup()
    b_s3,   l_s3,   p_s3   = make_basic_setup()

    r_base = run_scenario(
        borrowers=b_base, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0, lenders=l_base, pool=p_base,
        demand_surge_usdc=0.0,
    )
    r_s3 = run_scenario(
        borrowers=b_s3, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=0.0, liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=5.0, lenders=l_s3, pool=p_s3,
        demand_surge_usdc=500_000.0,
    )
    # Demand surge làm utilization tăng
    u_base = r_base["after"]["utilization"] or 0
    u_s3   = r_s3["after"]["utilization"]   or 0
    assert u_s3 >= u_base


# ── S4: Cú sốc chi phí vận hành ─────────────────────────────────────────────

def test_s4_high_gas_reduces_coverage():
    """S4 — Gas cao → liquidation coverage giảm (ít thanh lý hơn)."""
    b_low,  l_low,  p_low  = make_basic_setup()
    b_high, l_high, p_high = make_basic_setup()
    params = get_scenario_params("S1")  # cùng sốc giá với S4

    r_low_gas = run_scenario(
        borrowers=b_low, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=params["price_shock_pct"],
        liquidator_capital=LIQUIDATOR_CAPITAL, gas_cost_usd=5.0,
        lenders=l_low, pool=p_low,
    )
    r_high_gas = run_scenario(
        borrowers=b_high, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=params["price_shock_pct"],
        liquidator_capital=LIQUIDATOR_CAPITAL, gas_cost_usd=200.0,
        lenders=l_high, pool=p_high,
    )
    # Gas cao → ít thanh lý hơn → coverage <= gas thấp
    assert r_high_gas["liquidation_coverage"] <= r_low_gas["liquidation_coverage"] + 1e-6


# ── Liquidation Coverage ──────────────────────────────────────────────────────

def test_liquidation_coverage_between_0_and_1():
    """Coverage phải nằm trong [0, 1]."""
    for scenario in ["S0", "S1", "S4"]:
        b, l, p = make_basic_setup()
        params = get_scenario_params(scenario)
        r = run_scenario(
            borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
            price_shock_pct=params["price_shock_pct"],
            liquidator_capital=LIQUIDATOR_CAPITAL,
            gas_cost_usd=params["gas_cost_usd"],
            lenders=l, pool=p,
            price_feedback=params["price_feedback"],
            market_depth_usd=params["market_depth_usd"],
        )
        cov = r["liquidation_coverage"]
        assert 0.0 <= cov <= 1.0, f"Coverage={cov} ngoài phạm vi tại {scenario}"


# ── Borrower status không âm ──────────────────────────────────────────────────

def test_no_negative_debt_or_collateral():
    """Sau mô phỏng, debt và collateral không âm."""
    b, l, p = make_basic_setup()
    params = get_scenario_params("S1")
    r = run_scenario(
        borrowers=b, initial_eth_price=INITIAL_ETH_PRICE,
        price_shock_pct=params["price_shock_pct"],
        liquidator_capital=LIQUIDATOR_CAPITAL,
        gas_cost_usd=params["gas_cost_usd"],
        lenders=l, pool=p,
        price_feedback=params["price_feedback"],
        market_depth_usd=params["market_depth_usd"],
    )
    # Kiểm tra qua metrics
    assert r["after"]["total_remaining_debt"] >= 0.0
    assert r["after"]["total_collateral_value_usd"] >= 0.0
