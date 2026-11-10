"""
test_model.py — Unit test: tính HF và ràng buộc số dư

Ví dụ tính tay (examples.md):
  Case 1 — An toàn:    col=5 ETH, debt=5000 USDC, price=2000 → HF = 5*2000*0.825/5000 = 1.65
  Case 2 — Đủ TL:      col=5 ETH, debt=9000 USDC, price=2000 → HF = 5*2000*0.825/9000 = 0.917
  Case 3 — Thiếu hụt:  col=1 ETH, debt=2000 USDC, price=1200 → HF = 1*1200*0.825/2000 = 0.495
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Borrower, LIQUIDATION_THRESHOLD

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
