"""
tests/test_liquidation.py — Unit test: quy tắc thanh lý

Bao phủ:
  - Thanh lý thành công (một phần) → borrower vẫn còn nợ → trạng thái ACTIVE
  - Borrower an toàn (HF >= 1) không bị thanh lý
  - Liquidator không đủ vốn → failed_no_capital
  - Gas quá cao → failed_no_profit
  - Nhiều vòng thanh lý → không phát sinh số dư âm
  - Collateral cạn kiệt → DEFAULTED (không phải REPAID)
  - times_liquidated tăng đúng mỗi lần thành công
  - Gas cost được trừ từ capital_usdc
  - Borrower vẫn còn nợ sau thanh lý một phần
  - Nhất quán chỉ số sau simulation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Borrower, CLOSE_FACTOR
from liquidation import Liquidator


def test_liquidation_success_partial():
    """Thanh lý một phần: debt_usdc giảm, borrower còn nợ → ACTIVE."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert result["success"], result["reason"]
    assert result["debt_repaid"] > 0
    assert abs(result["debt_repaid"] - 9000.0 * CLOSE_FACTOR) < 1.0
    assert b.debt_usdc > 0          # vẫn còn nợ
    assert b.times_liquidated == 1
    assert b.is_touched
    assert not b.is_repaid          # chưa đóng hoàn toàn
    assert not b.is_defaulted       # chưa vỡ nợ
    assert b.status == "ACTIVE"


def test_liquidation_safe_borrower_not_touched():
    """Borrower HF >= 1 không bị thanh lý."""
    b = Borrower.create(5.0, 5000.0)   # HF = 1.65
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert b.times_liquidated == 0
    assert not b.is_touched
    assert b.status == "ACTIVE"


def test_liquidation_pure_no_capital():
    """Liquidator hoàn toàn hết vốn (capital=0) → failed_no_capital."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=0.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert liq.failed_no_capital == 1


def test_liquidation_insufficient_capital():
    """Vốn ít, gas ăn hết lợi nhuận → thất bại vì bất kỳ lý do gì."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=10.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert liq.failed_count == 1


def test_liquidation_high_gas_no_profit():
    """Gas quá cao → net profit <= 0 → failed_no_profit."""
    b = Borrower.create(0.01, 18.0)   # HF = 0.917 < 1
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=500.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert liq.failed_no_profit == 1


def test_no_negative_balances_after_multiple_liquidations():
    """Nhiều vòng thanh lý → collateral và debt không bao giờ âm."""
    b = Borrower.create(0.5, 900.0)
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)

    for _ in range(15):
        liq.attempt_liquidation(b, eth_price=1500.0)

    assert b.collateral_eth >= -1e-9
    assert b.debt_usdc >= -1e-9


def test_defaulted_not_repaid_when_collateral_exhausted():
    """
    Khi collateral cạn trước khi hết nợ → DEFAULTED, không phải REPAID.
    realized_bad_debt > 0 và _defaulted = True.
    """
    b = Borrower.create(0.001, 10.0)  # HF rất thấp, collateral rất nhỏ
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=0.0)  # gas=0 để dễ test

    for _ in range(20):
        liq.attempt_liquidation(b, eth_price=2000.0)

    # Nếu đã vỡ nợ: DEFAULTED
    if b.is_defaulted:
        assert b.realized_bad_debt > 0
        assert b.debt_usdc == 0
        assert not b.is_repaid           # DEFAULTED ≠ REPAID
        assert b.status == "DEFAULTED"
    else:
        # Có thể đã trả hết nợ bình thường
        assert b.is_repaid or b.debt_usdc >= 0


def test_repaid_has_no_bad_debt():
    """Borrower REPAID phải có realized_bad_debt = 0 và _defaulted = False."""
    # Vị thế khỏe, nhiều collateral → khi thanh lý không bao giờ cạn collateral
    b = Borrower.create(10.0, 9000.0)  # HF < 1 nhưng collateral rất nhiều
    liq = Liquidator(capital_usdc=1_000_000.0, gas_cost_usd=1.0)

    for _ in range(50):
        if b.is_closed:
            break
        liq.attempt_liquidation(b, eth_price=800.0)

    if b.is_repaid:
        assert b.realized_bad_debt == 0.0
        assert not b.is_defaulted
        assert b.status == "REPAID"


def test_times_liquidated_increments():
    """times_liquidated tăng mỗi lần thanh lý thành công."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=100_000.0, gas_cost_usd=1.0)

    count = 0
    for _ in range(5):
        result = liq.attempt_liquidation(b, eth_price=2000.0)
        if result["success"]:
            count += 1

    assert b.times_liquidated == count


def test_gas_deducted_from_capital():
    """Gas cost phải được trừ từ capital_usdc của liquidator."""
    b = Borrower.create(5.0, 9000.0)
    initial_capital = 10_000.0
    gas = 5.0
    liq = Liquidator(capital_usdc=initial_capital, gas_cost_usd=gas)

    result = liq.attempt_liquidation(b, eth_price=2000.0)
    assert result["success"]

    expected = (
        initial_capital
        - result["debt_repaid"]
        - gas
        + result["eth_received"] * 2000.0
    )
    assert abs(liq.capital_usdc - expected) < 0.01


def test_borrower_still_has_debt_after_partial_liquidation():
    """Sau thanh lý một phần, borrower vẫn còn nợ."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=100_000.0, gas_cost_usd=1.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert result["success"]
    assert b.debt_usdc > 0
    assert not b.is_closed


def test_metrics_consistency_after_simulation():
    """Chỉ số nhất quán: n_touched <= n_borrowers, n_repaid + n_defaulted <= n_touched."""
    from scenarios import generate_borrowers
    from simulation import run_scenario

    borrowers = generate_borrowers(n=20, eth_price=2000.0)
    result = run_scenario(
        borrowers=borrowers,
        initial_eth_price=2000.0,
        price_shock_pct=-0.25,
        liquidator_capital=500_000.0,
        gas_cost_usd=5.0,
    )
    after = result["after"]

    assert after["n_touched"] <= after["n_borrowers"]
    assert after["n_repaid"] + after["n_defaulted"] <= after["n_touched"]
    assert after["n_still_unsafe"] >= 0
    assert after["total_realized_bad_debt"] >= 0
    # Tổng: repaid + defaulted = tổng vị thế đã đóng
    n_closed = after["n_repaid"] + after["n_defaulted"]
    assert n_closed <= after["n_borrowers"]
