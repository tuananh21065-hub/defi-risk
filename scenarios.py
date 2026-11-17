# -*- coding: utf-8 -*-
"""
scenarios.py — Tham số thí nghiệm chuẩn hóa theo thiết kế doc nghiên cứu

Thiết kế thực nghiệm (mục 4.5 doc):
  6 kịch bản thị trường × 2 chiến lược (Fixed / Adaptive) = 12 thực nghiệm E1–E12

  | Mã  | Kịch bản             | Thay đổi chính                         | Chỉ tiêu trọng tâm            |
  |-----|----------------------|----------------------------------------|-------------------------------|
  | S0  | Cơ sở                | Thị trường ổn định, chi phí bình thường| Liquidity, Utilization, HF    |
  | S1  | Cú sốc giá           | Giá ETH giảm mạnh                      | Liquidation Coverage, Bad Debt|
  | S2  | Cú sốc thanh khoản   | Lender rút USDC, thanh khoản giảm      | Available Liquidity, WF       |
  | S3  | Cú sốc lãi suất      | Nhu cầu vay tăng → utilization tăng    | Utilization, Borrow Rate      |
  | S4  | Cú sốc chi phí vận hành| Gas và trượt giá tăng                 | Liquidation Success Rate      |
  | S5  | Cú sốc kết hợp       | Giá giảm + thanh khoản thấp + gas cao  | Bad Debt, tổng hợp            |

Mỗi kịch bản chạy 2 lần:
  - strategy='fixed':    Borrower/Lender không thích nghi
  - strategy='adaptive': Borrower/Lender thích nghi theo HF và điều kiện thị trường

Lưu ý:
  - Tham số sốc (% giá, % thanh khoản...) cần có cơ sở từ dữ liệu hoặc được nêu rõ
    là giả định stress test. Nhóm cần bổ sung nguồn trước khi nộp.
  - Seed=42 cố định để kết quả tái lập được.
  - Multi-seed check (nhóm E cũ) được tích hợp vào từng kịch bản nếu cần.
"""
import random
from typing import List, Tuple
from model import Borrower, Lender, LendingPool, LTV

RANDOM_SEED        = 42
INITIAL_ETH_PRICE  = 2000.0
LIQUIDATOR_CAPITAL = 500_000.0   # 500,000 USDC


# ── Sinh danh sách tác nhân ──────────────────────────────────────────────────

def generate_borrowers(
    n: int = 50,
    eth_price: float = 2000.0,
    seed: int = RANDOM_SEED,
) -> List[Borrower]:
    """
    Sinh n Borrower với seed cho trước.
    - collateral_eth: uniform [0.1, 10.0]
    - LTV tại thời điểm vay: uniform [50%, 100%] của LTV tối đa
    - risk_appetite: uniform [0, 1]
    """
    rng = random.Random(seed)
    borrowers = []
    for _ in range(n):
        col_eth = round(rng.uniform(0.1, 10.0), 4)
        col_usd = col_eth * eth_price
        ltv_ratio = rng.uniform(0.5, 1.0) * LTV
        debt = round(col_usd * ltv_ratio, 2)
        ra   = round(rng.uniform(0.0, 1.0), 2)
        borrowers.append(Borrower.create(col_eth, debt, risk_appetite=ra))
    return borrowers


def generate_lenders(
    n: int = 20,
    total_supply_usdc: float = 2_000_000.0,
    seed: int = RANDOM_SEED,
) -> List[Lender]:
    """
    Sinh n Lender với tổng vốn gửi = total_supply_usdc.
    - supplied_usdc: phân bố đều
    - risk_appetite: uniform [0, 1]
    """
    rng = random.Random(seed + 1)
    lenders = []
    # Phân phối ngẫu nhiên tổng vốn
    shares = [rng.random() for _ in range(n)]
    total  = sum(shares)
    for s in shares:
        supplied = round(total_supply_usdc * s / total, 2)
        ra       = round(rng.uniform(0.0, 1.0), 2)
        lenders.append(Lender.create(supplied, risk_appetite=ra))
    return lenders


def make_pool(
    borrowers: List[Borrower],
    lenders: List[Lender],
) -> LendingPool:
    """Tạo LendingPool từ danh sách Borrower và Lender."""
    return LendingPool.from_lenders_and_borrowers(lenders, borrowers)


# ── 6 kịch bản thị trường (S0–S5) ───────────────────────────────────────────

def get_scenario_params(scenario: str) -> dict:
    """
    Trả về tham số kịch bản.
    scenario: 'S0'|'S1'|'S2'|'S3'|'S4'|'S5'
    """
    base = {
        "initial_eth_price":   INITIAL_ETH_PRICE,
        "price_shock_pct":     0.0,
        "liquidity_shock_pct": 0.0,
        "demand_surge_usdc":   0.0,
        "gas_cost_usd":        5.0,
        "price_feedback":      False,
        "market_depth_usd":    10_000_000.0,
        "liquidator_capital":  LIQUIDATOR_CAPITAL,
    }

    # S0: Cơ sở — thị trường ổn định
    if scenario == "S0":
        return {**base, "price_shock_pct": 0.0}

    # S1: Cú sốc giá — ETH giảm mạnh, có cascade
    # Mức -30% tham khảo biên độ điển hình trong stress test DeFi
    # (cần bổ sung nguồn dữ liệu lịch sử trước khi nộp)
    if scenario == "S1":
        return {**base, "price_shock_pct": -0.30, "price_feedback": True,
                "market_depth_usd": 5_000_000.0}

    # S2: Cú sốc thanh khoản — 40% lender rút ngay
    # (giả định stress test, cần cơ sở từ dữ liệu hoặc tài liệu)
    if scenario == "S2":
        return {**base, "liquidity_shock_pct": 0.40}

    # S3: Cú sốc lãi suất — nhu cầu vay tăng mạnh
    # demand_surge: 500k USDC thêm vào pool debt → utilization tăng
    if scenario == "S3":
        return {**base, "demand_surge_usdc": 500_000.0}

    # S4: Cú sốc chi phí vận hành — gas tăng mạnh, sốc giá -20%
    # Gas $80 tham khảo phân vị cao trong dữ liệu gas lịch sử Ethereum
    # (cần bổ sung nguồn trước khi nộp)
    if scenario == "S4":
        return {**base, "price_shock_pct": -0.20, "gas_cost_usd": 80.0}

    # S5: Cú sốc kết hợp — giá giảm + thanh khoản thấp + gas cao
    if scenario == "S5":
        return {**base,
                "price_shock_pct":     -0.30,
                "liquidity_shock_pct":  0.30,
                "gas_cost_usd":        50.0,
                "price_feedback":      True,
                "market_depth_usd":    2_000_000.0}

    raise ValueError(f"Kịch bản không hợp lệ: {scenario!r}. Chọn S0–S5.")


# ── 12 thực nghiệm E1–E12 ───────────────────────────────────────────────────

EXPERIMENTS = [
    # (experiment_id, scenario, strategy)
    ("E1",  "S0", "fixed"),
    ("E2",  "S0", "adaptive"),
    ("E3",  "S1", "fixed"),
    ("E4",  "S1", "adaptive"),
    ("E5",  "S2", "fixed"),
    ("E6",  "S2", "adaptive"),
    ("E7",  "S3", "fixed"),
    ("E8",  "S3", "adaptive"),
    ("E9",  "S4", "fixed"),
    ("E10", "S4", "adaptive"),
    ("E11", "S5", "fixed"),
    ("E12", "S5", "adaptive"),
]


# ── Multi-seed robustness check ──────────────────────────────────────────────
# Chạy kịch bản S1 (cú sốc giá) với nhiều seed khác nhau
# Mục tiêu: kiểm tra xu hướng có ổn định không
# LƯU Ý: đây là robustness check, KHÔNG phải Monte Carlo đầy đủ
ROBUSTNESS_SEEDS = [42, 123, 7, 99, 2024]
ROBUSTNESS_SCENARIO = "S1"
ROBUSTNESS_STRATEGY = "fixed"


# ── Sensitivity Analysis giữ nguyên từ bản cũ ─────────────────────────────
# Dùng để so sánh riêng lẻ từng tham số (giá/gas/vốn/market_depth)

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
