"""
model.py — Mô hình dữ liệu Borrower và tính Health Factor

Giả định mô hình (rút gọn từ Aave V3):
- Tài sản thế chấp: ETH (collateral)
- Tài sản vay: USDC (debt), 1 USDC ≈ 1 USD
- Health Factor (HF) = (collateral_eth * eth_price * liquidation_threshold) / debt_usdc
  Nếu HF < 1: vị thế đủ điều kiện thanh lý
- liquidation_threshold = 0.825 (giả định nghiên cứu, không phải Aave mainnet)
- loan_to_value (LTV) = 0.80
- close_factor = 0.50: tối đa 50% nợ được thanh lý mỗi lần
- liquidation_bonus = 0.05: liquidator nhận thêm 5% ETH

Trạng thái borrower (3 loại, loại trừ nhau):
  - ACTIVE:    còn nợ, collateral còn — vị thế đang hoạt động bình thường
  - REPAID:    nợ về 0 do được thanh lý đủ — đóng hoàn toàn không phát sinh bad debt
  - DEFAULTED: collateral cạn trước khi hết nợ — phần nợ còn lại trở thành bad debt

Lưu ý: is_fully_repaid (cũ) đã được thay bằng is_repaid + is_defaulted để tránh
nhầm lẫn giữa "trả hết nợ" và "vỡ nợ". Cả hai trường hợp đều có debt_usdc=0
nhưng ý nghĩa hoàn toàn khác nhau.
"""
from dataclasses import dataclass
import uuid

LIQUIDATION_THRESHOLD = 0.825   # ngưỡng thanh lý (giả định, không phải Aave mainnet)
LTV = 0.80                       # loan-to-value tối đa
CLOSE_FACTOR = 0.50              # tối đa 50% nợ được thanh lý mỗi lần
LIQUIDATION_BONUS = 0.05         # 5% bonus thưởng cho liquidator


@dataclass
class Borrower:
    borrower_id: str
    collateral_eth: float           # ETH thế chấp
    debt_usdc: float                # USDC đã vay
    times_liquidated: int = 0       # số lần bị thanh lý thành công (kể cả một phần)
    realized_bad_debt: float = 0.0  # nợ không thu hồi được khi collateral cạn
    _defaulted: bool = False        # True khi collateral đã cạn mà vẫn còn nợ

    @staticmethod
    def create(collateral_eth: float, debt_usdc: float) -> "Borrower":
        return Borrower(
            borrower_id=str(uuid.uuid4())[:8],
            collateral_eth=collateral_eth,
            debt_usdc=debt_usdc,
        )

    # ── Health Factor ──────────────────────────────────────────────────────────

    def health_factor(self, eth_price: float, liq_threshold: float = LIQUIDATION_THRESHOLD) -> float:
        """HF = (collateral_eth * eth_price * liq_threshold) / debt_usdc"""
        if self.debt_usdc <= 0:
            return float("inf")
        return (self.collateral_eth * eth_price * liq_threshold) / self.debt_usdc

    def is_undercollateralized(self, eth_price: float) -> bool:
        """HF < 1: vị thế đủ điều kiện thanh lý."""
        return self.health_factor(eth_price) < 1.0

    # ── Trạng thái vị thế ─────────────────────────────────────────────────────

    @property
    def is_touched(self) -> bool:
        """Đã bị thanh lý ít nhất một lần (kể cả một phần)."""
        return self.times_liquidated > 0

    @property
    def is_repaid(self) -> bool:
        """
        Nợ về 0 mà KHÔNG phát sinh bad debt — vị thế đóng hoàn toàn.
        Collateral vẫn còn hoặc được thanh lý vừa đủ.
        """
        return self.debt_usdc <= 0 and not self._defaulted

    @property
    def is_defaulted(self) -> bool:
        """
        Vỡ nợ: collateral đã cạn kiệt trước khi hết nợ.
        Phần nợ còn lại (realized_bad_debt > 0) không thể thu hồi được.
        """
        return self._defaulted

    @property
    def is_closed(self) -> bool:
        """Vị thế đã đóng: hoặc repaid hoặc defaulted (debt_usdc <= 0)."""
        return self.debt_usdc <= 0

    @property
    def status(self) -> str:
        """Nhãn trạng thái dạng chuỗi để hiển thị."""
        if self._defaulted:
            return "DEFAULTED"
        if self.debt_usdc <= 0:
            return "REPAID"
        return "ACTIVE"

    # ── Chỉ số tài chính ──────────────────────────────────────────────────────

    def projected_liquidation_deficit(self, eth_price: float) -> float:
        """
        Phần nợ dự kiến không thể thu hồi nếu liquidate hết toàn bộ collateral còn lại.
        Đây là ước tính (projected), chưa phải bad debt thực sự (realized).
        projected_deficit = max(0, debt - collateral_value / (1 + bonus))
        """
        recoverable = (self.collateral_eth * eth_price) / (1 + LIQUIDATION_BONUS)
        return max(0.0, self.debt_usdc - recoverable)

    def collateral_value_usd(self, eth_price: float) -> float:
        return self.collateral_eth * eth_price
