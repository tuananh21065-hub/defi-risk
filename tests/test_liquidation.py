"""
test_liquidation.py — Unit test: quy tắc thanh lý
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Borrower
from liquidation import Liquidator

def test_liquidation_success():
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)
    assert result["success"], result["reason"]
    assert result["debt_repaid"] > 0
    assert b.collateral_eth >= 0
    assert b.debt_usdc >= 0

def test_liquidation_safe_borrower():
    b = Borrower.create(5.0, 5000.0)
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)
    assert not result["success"]

def test_liquidation_no_negative_balances():
    b = Borrower.create(0.5, 900.0)
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    for _ in range(10):
        liq.attempt_liquidation(b, eth_price=1500.0)
    assert b.collateral_eth >= -1e-9  # floating point tolerance
    assert b.debt_usdc >= -1e-9
