"""
tests/test_benchmark.py — Bộ kiểm thử chuẩn dùng chung cho Python và Smart Contract
(Theo Mục 5 của Bảng tham số mô phỏng v0.1)

Thiết lập chuẩn:
- Thế chấp: 2 ETH
- Dư nợ: 2.000 USDC
- Liquidation Threshold (LT): 0.80

Mốc giá:
- ETH = 2.000 USD -> Collateral = 4.000 USD, LTV = 0.50, HF = 1.6
- ETH = 1.500 USD -> Collateral = 3.000 USD, LTV = 0.6667, HF = 1.2
- ETH = 1.250 USD -> Collateral = 2.500 USD, LTV = 0.80, HF = 1.0 (ngưỡng thanh lý)
- ETH = 1.000 USD -> Collateral = 2.000 USD, LTV = 1.00, HF = 0.8 (thế chấp bằng nợ)
"""

import pytest
from model import Borrower
from config.parameters import (
    validate_parameters,
    LIQUIDATION_THRESHOLD,
    LIQUIDATION_BONUS,
    BORROWER_LTV
)


def test_parameter_constraints():
    """Kiểm tra các bất đẳng thức ràng buộc tham số cốt lõi."""
    errors = validate_parameters()
    assert len(errors) == 0, f"Vi phạm ràng buộc tham số: {errors}"
    
    # LT * (1 + Bonus) < 1
    lt = LIQUIDATION_THRESHOLD.value
    bonus = LIQUIDATION_BONUS.value
    assert lt * (1 + bonus) < 1.0


def test_benchmark_case_table():
    """Kiểm tra chính xác 4 mốc giá trị trong bảng benchmark."""
    collateral_eth = 2.0
    debt_usdc = 2000.0
    lt = 0.80

    borrower = Borrower.create(collateral_eth=collateral_eth, debt_usdc=debt_usdc)

    # 1. Giá 2000 USD
    p1 = 2000.0
    val1 = collateral_eth * p1
    ltv1 = debt_usdc / val1
    hf1 = borrower.health_factor(p1, liq_threshold=lt)
    assert val1 == 4000.0
    assert pytest.approx(ltv1, 0.001) == 0.50
    assert pytest.approx(hf1, 0.001) == 1.60
    assert not borrower.is_undercollateralized(p1)

    # 2. Giá 1500 USD
    p2 = 1500.0
    val2 = collateral_eth * p2
    ltv2 = debt_usdc / val2
    hf2 = borrower.health_factor(p2, liq_threshold=lt)
    assert val2 == 3000.0
    assert pytest.approx(ltv2, 0.001) == 0.6667
    assert pytest.approx(hf2, 0.001) == 1.20
    assert not borrower.is_undercollateralized(p2)

    # 3. Giá 1250 USD (Đúng ngưỡng thanh lý HF = 1.0)
    p3 = 1250.0
    val3 = collateral_eth * p3
    ltv3 = debt_usdc / val3
    hf3 = borrower.health_factor(p3, liq_threshold=lt)
    assert val3 == 2500.0
    assert pytest.approx(ltv3, 0.001) == 0.80
    assert pytest.approx(hf3, 0.001) == 1.00
    # Tại HF = 1.00, theo định nghĩa HF < 1 mới undercollateralized
    assert hf3 >= 1.0

    # 4. Giá 1000 USD (Bắt đầu thiếu hụt / nợ bằng tài sản thế chấp)
    p4 = 1000.0
    val4 = collateral_eth * p4
    ltv4 = debt_usdc / val4
    hf4 = borrower.health_factor(p4, liq_threshold=lt)
    assert val4 == 2000.0
    assert pytest.approx(ltv4, 0.001) == 1.00
    assert pytest.approx(hf4, 0.001) == 0.80
    assert borrower.health_factor(p4, liq_threshold=lt) < 1.0
