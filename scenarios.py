"""
scenarios.py — Tham số thí nghiệm chuẩn hóa

Seed cố định = 42 để kết quả tái lập được.

Nhóm kịch bản:
  A. Scenario Analysis  — sốc giá (price_feedback=False)
  B. Gas Sensitivity    — gas thay đổi, sốc -20%
  C. Cascade Analysis   — price_feedback=True, market_depth thay đổi
  D. Capital Sensitivity— vốn liquidator thay đổi, sốc -20%
  E. Multi-seed Check   — chạy 5 seed khác nhau, kiểm tra xu hướng ổn định

Lưu ý:
  - Nhóm A, B, D là scenario analysis thuần túy, KHÔNG phải Monte Carlo.
  - Nhóm C mô phỏng liquidation cascade với giả định tuyến tính về market impact.
  - Nhóm E là robustness check, chưa phải Monte Carlo đầy đủ (chưa phân tích phân phối).
  - Chỉ gọi là Monte Carlo khi phân tích phân phối kết quả qua nhiều lần chạy ngẫu nhiên.
"""
import random
from typing import List
from model import Borrower, LTV

RANDOM_SEED = 42
INITIAL_ETH_PRICE = 2000.0
LIQUIDATOR_CAPITAL = 500_000.0  # 500,000 USDC


def generate_borrowers(n: int = 50, eth_price: float = 2000.0, seed: int = RANDOM_SEED) -> List[Borrower]:
    """
    Sinh danh sách n borrower với seed cho trước.

    - collateral_eth: uniform [0.1, 10.0] ETH
    - LTV tại thời điểm vay: uniform [50%, 100%] của LTV tối đa (0.80)
      → tạo danh mục đa dạng: vị thế an toàn lẫn vị thế gần ngưỡng thanh lý
    """
    rng = random.Random(seed)
    borrowers = []
    for _ in range(n):
        col_eth = round(rng.uniform(0.1, 10.0), 4)
        col_usd = col_eth * eth_price
        ltv_ratio = rng.uniform(0.5, 1.0) * LTV
        debt = round(col_usd * ltv_ratio, 2)
        borrowers.append(Borrower.create(col_eth, debt))
    return borrowers


# ── A. Scenario Analysis: sốc giá ─────────────────────────────────────────────
PRICE_SHOCK_SCENARIOS = [
    {"name": "baseline",  "price_shock_pct": 0.00,  "gas_cost_usd": 5.0,
     "price_feedback": False},
    {"name": "shock_10",  "price_shock_pct": -0.10, "gas_cost_usd": 5.0,
     "price_feedback": False},
    {"name": "shock_20",  "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": False},
    {"name": "shock_30",  "price_shock_pct": -0.30, "gas_cost_usd": 5.0,
     "price_feedback": False},
    {"name": "shock_40",  "price_shock_pct": -0.40, "gas_cost_usd": 5.0,
     "price_feedback": False},
]

# ── B. Gas Sensitivity: sốc -20%, gas thay đổi ────────────────────────────────
GAS_SENSITIVITY_SCENARIOS = [
    {"name": "gas_1",   "price_shock_pct": -0.20, "gas_cost_usd": 1.0,
     "price_feedback": False},
    {"name": "gas_5",   "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": False},
    {"name": "gas_20",  "price_shock_pct": -0.20, "gas_cost_usd": 20.0,
     "price_feedback": False},
    {"name": "gas_50",  "price_shock_pct": -0.20, "gas_cost_usd": 50.0,
     "price_feedback": False},
    {"name": "gas_100", "price_shock_pct": -0.20, "gas_cost_usd": 100.0,
     "price_feedback": False},
]

# ── C. Cascade Analysis: price_feedback=True, market_depth thay đổi ───────────
# Mục tiêu: so sánh có/không có cascade, và thanh khoản thị trường cao/thấp
# ảnh hưởng thế nào đến bad debt và số vị thế không được xử lý
CASCADE_SCENARIOS = [
    {"name": "cascade_no_feedback",  "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": False, "market_depth_usd": None},
    {"name": "cascade_deep_market",  "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": True,  "market_depth_usd": 50_000_000.0},
    {"name": "cascade_mid_market",   "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": True,  "market_depth_usd": 10_000_000.0},
    {"name": "cascade_thin_market",  "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": True,  "market_depth_usd": 2_000_000.0},
    {"name": "cascade_very_thin",    "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "price_feedback": True,  "market_depth_usd": 500_000.0},
]

# ── D. Capital Sensitivity: vốn liquidator thay đổi, sốc -20% ─────────────────
# Mục tiêu: đánh giá năng lực thanh lý (vốn) ảnh hưởng thế nào đến
# n_still_unsafe và bad debt khi các tham số khác cố định
CAPITAL_SENSITIVITY_SCENARIOS = [
    {"name": "capital_50k",  "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "liquidator_capital": 50_000.0,    "price_feedback": False},
    {"name": "capital_250k", "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "liquidator_capital": 250_000.0,   "price_feedback": False},
    {"name": "capital_500k", "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "liquidator_capital": 500_000.0,   "price_feedback": False},
    {"name": "capital_1M",   "price_shock_pct": -0.20, "gas_cost_usd": 5.0,
     "liquidator_capital": 1_000_000.0, "price_feedback": False},
]

# ── E. Multi-seed Robustness Check ─────────────────────────────────────────────
# Chạy kịch bản chuẩn (-20% / gas $5 / capital 500k) với 5 seed khác nhau
# Mục tiêu: kiểm tra xu hướng có ổn định không, kết luận không chỉ đúng với seed=42
# LƯU Ý: đây là robustness check, KHÔNG phải Monte Carlo (chưa phân tích phân phối)
MULTI_SEED_SEEDS = [42, 123, 7, 99, 2024]
