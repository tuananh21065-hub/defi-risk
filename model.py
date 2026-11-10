"""
model.py — Mô hình dữ liệu Borrower và tính Health Factor

Giả định mô hình (rút gọn từ Aave V3):
- Tài sản thế chấp: ETH (collateral)
- Tài sản vay: USDC (debt), 1 USDC ≈ 1 USD
- Health Factor (HF) = (collateral_eth * eth_price * liquidation_threshold) / debt_usdc
  Nếu HF < 1: vị thế đủ điều kiện thanh lý
- liquidation_threshold mặc định = 0.825 (82.5% như Aave V3 với ETH)
- loan_to_value (LTV) mặc định = 0.80
"""
from dataclasses import dataclass, field
import uuid

LIQUIDATION_THRESHOLD = 0.825   # ngưỡng thanh lý (giả định, không phải Aave mainnet)
LTV = 0.80                       # loan-to-value tối đa
CLOSE_FACTOR = 0.50              # tối đa 50% nợ được thanh lý mỗi lần
LIQUIDATION_BONUS = 0.05         # 5% bonus thưởng cho liquidator

@dataclass
class Borrower:
    borrower_id: str
    collateral_eth: float   # ETH thế chấp
    debt_usdc: float        # USDC đã vay
    is_liquidated: bool = False
    shortfall: float = 0.0  # khoản thiếu hụt tài sản bảo đảm sau thanh lý

    @staticmethod
    def create(collateral_eth: float, debt_usdc: float) -> "Borrower":
        return Borrower(
            borrower_id=str(uuid.uuid4())[:8],
            collateral_eth=collateral_eth,
            debt_usdc=debt_usdc,
        )

    def health_factor(self, eth_price: float, liq_threshold: float = LIQUIDATION_THRESHOLD) -> float:
        """HF = (collateral_eth * eth_price * liq_threshold) / debt_usdc"""
        if self.debt_usdc <= 0:
            return float("inf")
        return (self.collateral_eth * eth_price * liq_threshold) / self.debt_usdc

    def is_undercollateralized(self, eth_price: float) -> bool:
        return self.health_factor(eth_price) < 1.0

    def collateral_value_usd(self, eth_price: float) -> float:
        return self.collateral_eth * eth_price
