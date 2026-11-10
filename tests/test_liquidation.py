"""
tests/test_liquidation.py — Unit test: quy tắc thanh lý

Bao phủ các trường hợp:
  - Thanh lý thành công (một phần)
  - Borrower an toàn (HF >= 1) không bị thanh lý
  - Liquidator không đủ vốn
  - Gas quá cao → không có lợi
  - Thanh lý một phần nhiều lần → không phát sinh số dư âm
  - Collateral cạn kiệt → ghi nhận realized_bad_debt
  - times_liquidated tăng đúng mỗi lần
  - Gas cost được trừ từ capital_usdc
  - Borrower vẫn còn nợ sau thanh lý một phần
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Borrower, CLOSE_FACTOR
from liquidation import Liquidator


def test_liquidation_success_partial():
    """Thanh lý một phần: debt_usdc giảm, borrower vẫn còn nợ."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert result["success"], result["reason"]
    assert result["debt_repaid"] > 0
    # Close factor = 50% → tối đa trả 4500 USDC
    assert abs(result["debt_repaid"] - 9000.0 * CLOSE_FACTOR) < 1.0
    # Borrower vẫn còn nợ (vì chỉ trả 50%)
    assert b.debt_usdc > 0
    assert b.times_liquidated == 1
    assert b.is_touched


def test_liquidation_safe_borrower_not_touched():
    """Borrower HF >= 1 không bị thanh lý."""
    b = Borrower.create(5.0, 5000.0)   # HF = 1.65 → an toàn
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert b.times_liquidated == 0
    assert not b.is_touched


def test_liquidation_insufficient_capital():
    """Liquidator không đủ vốn → thất bại (failed_no_capital hoặc failed_no_profit)."""
    b = Borrower.create(5.0, 9000.0)
    # capital=$10, gas=$5 → actual_repay được giới hạn ở $10
    # nhưng với $10 trả nợ thì gross_profit ≈ $0.5 < gas $5 → vào failed_no_profit
    liq = Liquidator(capital_usdc=10.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert liq.failed_count == 1  # thất bại vì bất kỳ lý do gì


def test_liquidation_pure_no_capital():
    """Liquidator hoàn toàn hết vốn (capital=0) → failed_no_capital."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=0.0, gas_cost_usd=5.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert not result["success"]
    assert liq.failed_no_capital == 1


def test_liquidation_high_gas_no_profit():
    """Gas quá cao → net profit <= 0 → không thanh lý."""
    # collateral nhỏ → bonus thấp → gas ăn hết lợi nhuận
    b = Borrower.create(0.01, 18.0)   # HF = 0.01*2000*0.825/18 = 0.917 < 1
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


def test_realized_bad_debt_when_collateral_exhausted():
    """Khi collateral cạn → phần nợ còn lại trở thành realized_bad_debt."""
    # Vị thế cực kỳ thiếu hụt: collateral rất nhỏ, nợ lớn
    b = Borrower.create(0.001, 10.0)  # HF = 0.001*2000*0.825/10 = 0.165
    liq = Liquidator(capital_usdc=10_000.0, gas_cost_usd=0.0)  # gas=0 để dễ test

    # Thanh lý nhiều vòng cho đến khi collateral cạn
    for _ in range(20):
        liq.attempt_liquidation(b, eth_price=2000.0)

    # Khi collateral = 0, nợ còn lại phải được ghi vào realized_bad_debt
    assert b.collateral_eth <= 1e-9
    assert b.realized_bad_debt > 0 or b.is_fully_repaid


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

    # capital sau = capital_ban_đầu - debt_repaid - gas + eth_received * price
    expected = (
        initial_capital
        - result["debt_repaid"]
        - gas
        + result["eth_received"] * 2000.0
    )
    assert abs(liq.capital_usdc - expected) < 0.01


def test_borrower_still_has_debt_after_partial_liquidation():
    """Sau thanh lý một phần, borrower vẫn còn nợ (close_factor < 1)."""
    b = Borrower.create(5.0, 9000.0)
    liq = Liquidator(capital_usdc=100_000.0, gas_cost_usd=1.0)
    result = liq.attempt_liquidation(b, eth_price=2000.0)

    assert result["success"]
    assert b.debt_usdc > 0, "Phải còn nợ sau thanh lý một phần"
    assert not b.is_fully_repaid


def test_metrics_consistency_after_simulation():
    """Chỉ số nhất quán: n_touched <= n_borrowers, n_fully_repaid <= n_touched."""
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
    assert after["n_fully_repaid"] <= after["n_touched"]
    assert after["n_still_unsafe"] >= 0
    assert after["total_realized_bad_debt"] >= 0
