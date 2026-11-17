# -*- coding: utf-8 -*-
"""
model.py — Mô hình dữ liệu: Borrower, Lender, LendingPool

Giả định mô hình (tham khảo cơ chế Aave V3):
  - Tài sản thế chấp: ETH; Tài sản vay: USDC (1 USDC ≈ 1 USD)
  - HF = (collateral_eth * eth_price * liquidation_threshold) / debt_usdc
  - Vị thế đủ điều kiện thanh lý khi HF < 1

Trạng thái Borrower (3 loại, loại trừ nhau):
  ACTIVE    — còn nợ, collateral còn
  REPAID    — nợ về 0, không phát sinh bad debt
  DEFAULTED — collateral cạn trước khi hết nợ → bad debt

Mô hình lãi suất kink (tham khảo Aave V3):
  Nếu U <= U_opt: Borrow Rate = BASE + SLOPE1 * (U / U_opt)
  Nếu U >  U_opt: Borrow Rate = BASE + SLOPE1 + SLOPE2 * ((U - U_opt) / (1 - U_opt))
  Supply Rate ≈ Borrow Rate * U * (1 - RESERVE_FACTOR)

Nguồn tham số: Aave V3 Documentation (tham khảo), ngày tra cứu 2026-11.
Nhóm cần đối chiếu lại tham số thực tế trước khi nộp.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import uuid

# ── Tham số giao thức (tham khảo Aave V3) ────────────────────────────────────
LIQUIDATION_THRESHOLD = 0.825   # ngưỡng thanh lý
LTV                   = 0.80    # loan-to-value tối đa
CLOSE_FACTOR          = 0.50    # tối đa 50% nợ được thanh lý mỗi lần
LIQUIDATION_BONUS     = 0.05    # 5% bonus cho liquidator

# ── Mô hình lãi suất kink (tham khảo Aave V3) ────────────────────────────────
INTEREST_BASE          = 0.00   # lãi suất cơ sở (năm)
INTEREST_SLOPE1        = 0.04   # slope khi U <= U_opt
INTEREST_SLOPE2        = 0.75   # slope khi U > U_opt (tăng mạnh)
INTEREST_U_OPT         = 0.80   # utilization tối ưu
RESERVE_FACTOR         = 0.10   # 10% lãi vay được giữ lại làm dự trữ


def borrow_rate(utilization: float) -> float:
    """
    Lãi suất vay theo mô hình kink.
    utilization = Tổng dư nợ / Tổng USDC cung cấp
    Trả về lãi suất năm (annualized).
    """
    u = max(0.0, min(utilization, 1.0))
    if u <= INTEREST_U_OPT:
        return INTEREST_BASE + INTEREST_SLOPE1 * (u / INTEREST_U_OPT)
    else:
        excess = (u - INTEREST_U_OPT) / (1.0 - INTEREST_U_OPT)
        return INTEREST_BASE + INTEREST_SLOPE1 + INTEREST_SLOPE2 * excess


def supply_rate(utilization: float) -> float:
    """Lãi suất gửi xấp xỉ = borrow_rate * U * (1 - reserve_factor)."""
    return borrow_rate(utilization) * utilization * (1.0 - RESERVE_FACTOR)


# ── Borrower ──────────────────────────────────────────────────────────────────

@dataclass
class Borrower:
    borrower_id:        str
    collateral_eth:     float          # ETH thế chấp
    debt_usdc:          float          # USDC đã vay
    risk_appetite:      float = 0.5    # 0=thận trọng, 1=chấp nhận rủi ro cao
    times_liquidated:   int   = 0      # số lần bị thanh lý thành công
    realized_bad_debt:  float = 0.0    # nợ không thu hồi khi collateral cạn
    _defaulted:         bool  = False  # True khi collateral đã cạn mà còn nợ

    @staticmethod
    def create(collateral_eth: float, debt_usdc: float,
               risk_appetite: float = 0.5) -> "Borrower":
        return Borrower(
            borrower_id=str(uuid.uuid4())[:8],
            collateral_eth=collateral_eth,
            debt_usdc=debt_usdc,
            risk_appetite=risk_appetite,
        )

    # ── Health Factor ─────────────────────────────────────────────────────────

    def health_factor(self, eth_price: float,
                      liq_threshold: float = LIQUIDATION_THRESHOLD) -> float:
        """HF = (collateral_eth * eth_price * liq_threshold) / debt_usdc"""
        if self.debt_usdc <= 0:
            return float("inf")
        return (self.collateral_eth * eth_price * liq_threshold) / self.debt_usdc

    def is_undercollateralized(self, eth_price: float) -> bool:
        """HF < 1: đủ điều kiện thanh lý."""
        return self.health_factor(eth_price) < 1.0

    # ── Trạng thái ────────────────────────────────────────────────────────────

    @property
    def is_touched(self) -> bool:
        return self.times_liquidated > 0

    @property
    def is_repaid(self) -> bool:
        """Nợ về 0, không có bad debt."""
        return self.debt_usdc <= 0 and not self._defaulted

    @property
    def is_defaulted(self) -> bool:
        """Collateral cạn trước khi hết nợ."""
        return self._defaulted

    @property
    def is_closed(self) -> bool:
        return self.debt_usdc <= 0

    @property
    def status(self) -> str:
        if self._defaulted:
            return "DEFAULTED"
        if self.debt_usdc <= 0:
            return "REPAID"
        return "ACTIVE"

    # ── Chỉ số tài chính ──────────────────────────────────────────────────────

    def projected_liquidation_deficit(self, eth_price: float) -> float:
        """
        Phần nợ dự kiến không thể thu hồi nếu liquidate hết toàn bộ collateral.
        projected_deficit = max(0, debt - collateral_value / (1 + bonus))
        """
        recoverable = (self.collateral_eth * eth_price) / (1.0 + LIQUIDATION_BONUS)
        return max(0.0, self.debt_usdc - recoverable)

    def collateral_value_usd(self, eth_price: float) -> float:
        return self.collateral_eth * eth_price

    # ── Hành vi thích nghi (Adaptive strategy) ────────────────────────────────

    def adaptive_action(self, eth_price: float, pool: "LendingPool",
                        import_random=None) -> str:
        """
        Quyết định thích nghi của Borrower dựa trên HF và Risk Appetite (RA).
        Trả về: 'repay_partial' | 'add_collateral' | 'none'

        Logic:
        - Nếu HF tiến gần ngưỡng (HF < 1.2) và RA thấp → ưu tiên hành động
        - Xác suất hành động = f(RA, HF) dạng đơn giản hóa
        - Borrower thận trọng (RA thấp) hành động sớm hơn khi HF giảm
        """
        import random as _random
        rng = import_random or _random

        if self.is_closed:
            return "none"

        hf = self.health_factor(eth_price)
        # Vùng nguy hiểm: HF < 1.3
        if hf >= 1.3:
            return "none"

        # Xác suất hành động tỷ lệ nghịch với HF và tỷ lệ nghịch với RA
        # Borrower thận trọng (RA=0) có P cao hơn, chấp nhận rủi ro (RA=1) ít hành động hơn
        p_action = (1.3 - hf) / 1.3 * (1.0 - self.risk_appetite * 0.5)

        if rng.random() > p_action:
            return "none"

        # Chọn hành động: trả nợ một phần hoặc bổ sung thế chấp
        if pool.available_liquidity_usdc > 0 and self.debt_usdc > 10:
            # Trả 10% nợ nếu pool có đủ thanh khoản và còn đủ nợ
            repay_amt = min(self.debt_usdc * 0.10, pool.available_liquidity_usdc)
            self.debt_usdc -= repay_amt
            pool.total_debt_usdc -= repay_amt
            pool.total_supplied_usdc += repay_amt
            return "repay_partial"
        return "none"


# ── Lender ────────────────────────────────────────────────────────────────────

@dataclass
class Lender:
    lender_id:      str
    supplied_usdc:  float          # USDC đã gửi vào pool
    risk_appetite:  float = 0.5    # 0=thận trọng, 1=chấp nhận rủi ro

    @staticmethod
    def create(supplied_usdc: float, risk_appetite: float = 0.5) -> "Lender":
        return Lender(
            lender_id=str(uuid.uuid4())[:8],
            supplied_usdc=supplied_usdc,
            risk_appetite=risk_appetite,
        )

    def adaptive_action(self, pool: "LendingPool",
                        import_random=None) -> str:
        """
        Quyết định thích nghi của Lender dựa trên utilization và Risk Appetite.
        Trả về: 'withdraw_partial' | 'deposit_more' | 'none'

        Logic:
        - Lender thận trọng (RA thấp) rút vốn khi utilization cao
        - Lender chấp nhận rủi ro có thể gửi thêm khi lãi suất tăng
        """
        import random as _random
        rng = import_random or _random

        u = pool.utilization
        # Nếu utilization quá cao (> 90%) và RA thấp → rút một phần
        if u > 0.90:
            p_withdraw = (u - 0.90) / 0.10 * (1.0 - self.risk_appetite)
            if rng.random() < p_withdraw:
                withdraw_amt = min(self.supplied_usdc * 0.20,
                                   pool.available_liquidity_usdc)
                if withdraw_amt > 0:
                    self.supplied_usdc -= withdraw_amt
                    pool.total_supplied_usdc -= withdraw_amt
                    return "withdraw_partial"

        # Nếu lãi suất gửi hấp dẫn (> 5% năm) và RA cao → gửi thêm
        sr = supply_rate(u)
        if sr > 0.05 and self.risk_appetite > 0.6:
            p_deposit = self.risk_appetite * 0.3
            if rng.random() < p_deposit:
                deposit_amt = self.supplied_usdc * 0.10
                self.supplied_usdc += deposit_amt
                pool.total_supplied_usdc += deposit_amt
                return "deposit_more"

        return "none"


# ── LendingPool ───────────────────────────────────────────────────────────────

@dataclass
class LendingPool:
    """
    Bể thanh khoản USDC: gom vốn của Lender, cho Borrower vay.

    total_supplied_usdc: tổng USDC đã được gửi vào pool
    total_debt_usdc:     tổng USDC đang được vay
    available_liquidity = total_supplied - total_debt
    utilization         = total_debt / total_supplied (khi total_supplied > 0)
    """
    total_supplied_usdc: float
    total_debt_usdc:     float = 0.0
    realized_bad_debt:   float = 0.0   # nợ xấu đã xác nhận, giảm total_supplied

    @staticmethod
    def from_lenders_and_borrowers(lenders: list, borrowers: list) -> "LendingPool":
        total_supplied = sum(l.supplied_usdc for l in lenders)
        total_debt     = sum(b.debt_usdc for b in borrowers)
        return LendingPool(
            total_supplied_usdc=total_supplied,
            total_debt_usdc=total_debt,
        )

    @property
    def available_liquidity_usdc(self) -> float:
        """USDC có thể rút hoặc cho vay thêm."""
        return max(0.0, self.total_supplied_usdc - self.total_debt_usdc)

    @property
    def utilization(self) -> float:
        """U = total_debt / total_supplied."""
        if self.total_supplied_usdc <= 0:
            return 1.0
        return min(1.0, self.total_debt_usdc / self.total_supplied_usdc)

    @property
    def current_borrow_rate(self) -> float:
        return borrow_rate(self.utilization)

    @property
    def current_supply_rate(self) -> float:
        return supply_rate(self.utilization)

    def apply_interest(self, dt_years: float = 1/365) -> float:
        """
        Áp dụng lãi suất vay cho một bước thời gian dt_years.
        Dư nợ tăng; phần lãi sau reserve_factor được cộng vào total_supplied.
        Trả về tổng lãi vay phát sinh trong bước này.
        """
        interest = self.total_debt_usdc * self.current_borrow_rate * dt_years
        self.total_debt_usdc += interest
        # Phần lãi sau khi trừ reserve được cộng vào total_supplied (trả cho Lender)
        lender_interest = interest * (1.0 - RESERVE_FACTOR)
        self.total_supplied_usdc += lender_interest
        return interest

    def record_bad_debt(self, amount: float) -> None:
        """Ghi nhận nợ xấu — giảm total_supplied (Lender chịu lỗ)."""
        self.realized_bad_debt += amount
        self.total_supplied_usdc = max(0.0, self.total_supplied_usdc - amount)

    def withdrawal_fulfillment(self, requested_usdc: float) -> float:
        """
        Tỷ lệ đáp ứng yêu cầu rút tiền.
        = min(available, requested) / requested
        """
        if requested_usdc <= 0:
            return 1.0
        fulfilled = min(self.available_liquidity_usdc, requested_usdc)
        return fulfilled / requested_usdc
