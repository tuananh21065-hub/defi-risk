"""
scenarios.py — Tham số thí nghiệm chuẩn hóa

Các kịch bản thí nghiệm:
  1. Baseline: không có sốc giá
  2. Sốc nhẹ: -10% ETH
  3. Sốc vừa: -20% ETH
  4. Sốc nặng: -30% ETH
  5. Thí nghiệm gas: sốc -20%, gas thay đổi

Seed cố định = 42 để tái lập kết quả.
"""
import random
from typing import List
from model import Borrower, LTV, LIQUIDATION_THRESHOLD

RANDOM_SEED = 42

def generate_borrowers(n: int = 50, eth_price: float = 2000.0) -> List[Borrower]:
    """
    Sinh dữ liệu n người vay với seed cố định.
    
    - collateral_eth: uniform [0.1, 10.0]
    - LTV tại thời điểm vay: uniform [50%, 80%] của LTV tối đa
    """
    rng = random.Random(RANDOM_SEED)
    borrowers = []
    for _ in range(n):
        col_eth = round(rng.uniform(0.1, 10.0), 4)
        col_usd = col_eth * eth_price
        # LTV từ 50% đến 100% của LTV tối đa (tạo vị thế đa dạng)
        ltv_ratio = rng.uniform(0.5, 1.0) * LTV
        debt = round(col_usd * ltv_ratio, 2)
        borrowers.append(Borrower.create(col_eth, debt))
    return borrowers


# --- Tham số kịch bản ---
INITIAL_ETH_PRICE = 2000.0
LIQUIDATOR_CAPITAL = 500_000.0  # 500,000 USDC

PRICE_SHOCK_SCENARIOS = [
    {"name": "baseline",   "price_shock_pct": 0.00,  "gas_cost_usd": 5.0},
    {"name": "shock_10",   "price_shock_pct": -0.10, "gas_cost_usd": 5.0},
    {"name": "shock_20",   "price_shock_pct": -0.20, "gas_cost_usd": 5.0},
    {"name": "shock_30",   "price_shock_pct": -0.30, "gas_cost_usd": 5.0},
]

GAS_SENSITIVITY_SCENARIOS = [
    {"name": "gas_1",  "price_shock_pct": -0.20, "gas_cost_usd": 1.0},
    {"name": "gas_5",  "price_shock_pct": -0.20, "gas_cost_usd": 5.0},
    {"name": "gas_20", "price_shock_pct": -0.20, "gas_cost_usd": 20.0},
    {"name": "gas_50", "price_shock_pct": -0.20, "gas_cost_usd": 50.0},
]
