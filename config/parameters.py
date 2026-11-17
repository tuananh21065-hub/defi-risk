"""
config/parameters.py — Bảng tham số mô phỏng DeFi Lending (Bài tập lớn Blockchain)
Phiên bản: 0.1
Ngày lập: 17/11/2026

Tài liệu lưu trữ tham số để đưa vào code, không phải nội dung báo cáo.
Ý nghĩa của nhãn:
- PAPER: Lấy từ bài đã đọc toàn văn, có ghi nguồn.
- ASSUMPTION: Giả định của nhóm, không có nguồn trong bốn bài. Báo cáo phải ghi rõ là giả định.
- PLACEHOLDER: Số tạm để chạy thử code, không có nguồn xác thực. Phải thay trước khi chạy thí nghiệm chính thức.
- TODO: Chưa có giá trị. Không tự bịa số; lấy từ dữ liệu hoặc hỏi lại.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class ParameterTag(str, Enum):
    PAPER = "PAPER"
    ASSUMPTION = "ASSUMPTION"
    PLACEHOLDER = "PLACEHOLDER"
    TODO = "TODO"


@dataclass(frozen=True)
class ParameterMeta:
    value: Any
    tag: ParameterTag
    source_notes: str
    scan_values: Optional[List[Any]] = None


# ==============================================================================
# 1. THAM SỐ CHUNG
# ==============================================================================

# --- Mô phỏng ---
TIME_STEP_HOURS = ParameterMeta(
    value=1,  # 1 giờ
    tag=ParameterTag.ASSUMPTION,
    source_notes="Chaudhary và Pinna dùng bước 1 phút trong 1 ngày; Bertucci dùng bước ngày."
)

SIMULATION_STEPS = ParameterMeta(
    value=168,  # 168 giờ = 7 ngày
    tag=ParameterTag.ASSUMPTION,
    source_notes="Chaudhary và Pinna chỉ chạy 1 ngày vì người dùng thụ động; tác nhân thích nghi cần chân trời dài hơn."
)

MONTE_CARLO_RUNS_DEV = ParameterMeta(
    value=100,
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna: 1.000 lần cho mỗi bộ tham số. Mức 100 do nhóm chọn để chạy thử."
)

MONTE_CARLO_RUNS_OFFICIAL = ParameterMeta(
    value=1000,
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna: 1.000 lần cho mỗi bộ tham số."
)

RANDOM_SEED = ParameterMeta(
    value=42,
    tag=ParameterTag.ASSUMPTION,
    source_notes="Seed cố định để tái lập và so sánh công bằng giữa hai nhóm chiến lược Fixed và Adaptive."
)

# --- Giao thức (Protocol) ---
ASSETS = ParameterMeta(
    value={"collateral": "ETH", "debt": "USDC", "peg_usd": 1.0},
    tag=ParameterTag.ASSUMPTION,
    source_notes="Phạm vi phiên bản đầu. Không cộng ETH thế chấp vào tổng cung USDC của bể."
)

CLOSE_FACTOR = ParameterMeta(
    value=0.50,
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna (1/2); Qin: Aave và Compound 50%, dYdX 100%."
)

LIQUIDATION_THRESHOLD = ParameterMeta(
    value=0.80,
    tag=ParameterTag.PLACEHOLDER,
    source_notes="Qin dùng 0.8 làm ví dụ. Giá trị Aave V3 phải tra lại, ghi ngày tra. Các mức quét là ASSUMPTION.",
    scan_values=[0.70, 0.75, 0.80, 0.85]
)

LIQUIDATION_BONUS = ParameterMeta(
    value=0.05,
    tag=ParameterTag.PAPER,
    source_notes="Qin: Aave 5% đến 15% tùy thị trường, Compound 8%, dYdX 5%.",
    scan_values=[0.05, 0.08, 0.10, 0.15]
)

# Lãi suất có điểm gãy (Kink Interest Rate Model)
KINK_INTEREST_RATE = ParameterMeta(
    value={
        "base_rate": 0.00,
        "slope1": 0.04,
        "slope2": 0.75,
        "u_optimal": 0.80,
        "reserve_factor": 0.10,
    },
    tag=ParameterTag.PLACEHOLDER,
    source_notes="Không có nguồn xác thực. Các mức 45%, 80%, 90% thấy trong kho Aave risk-v3 (nguồn thứ cấp). Bertucci có bảng hiệu chỉnh nhưng chưa đọc được.",
    scan_values={"u_optimal": [0.45, 0.80, 0.90]}
)

MIN_LIQUIDITY_RESERVE = ParameterMeta(
    value=0.00,  # 0% làm gốc
    tag=ParameterTag.ASSUMPTION,
    source_notes="Thí nghiệm mở rộng theo đề cương nhóm.",
    scan_values=[0.00, 0.05, 0.08, 0.10]
)

WITHDRAWAL_RULE = ParameterMeta(
    value="PROPORTIONAL_OR_QUEUE",
    tag=ParameterTag.ASSUMPTION,
    source_notes="Đáp ứng tối đa bằng thanh khoản khả dụng; phần còn lại xếp hàng sang bước sau, ghi thời điểm yêu cầu."
)

BAD_DEBT_RULE = ParameterMeta(
    value="LENDER_SOCIALIZED",
    tag=ParameterTag.PAPER,
    source_notes="Định nghĩa nợ xấu loại I theo Qin: thế chấp < dư nợ. Việc Lender chịu theo tỷ lệ là giả định của nhóm."
)

# --- Thị trường (Market) ---
INITIAL_ETH_PRICE = ParameterMeta(
    value=None,  # TODO
    tag=ParameterTag.TODO,
    source_notes="Lấy giá ETHUSDT tại một ngày cố định, ghi ngày và nguồn (Binance Vision)."
)

HOURLY_VOLATILITY = ParameterMeta(
    value=None,  # TODO
    tag=ParameterTag.TODO,
    source_notes="Độ lệch chuẩn lợi suất log theo giờ, tính từ dữ liệu ETHUSDT nến 1 giờ."
)

PRICE_PATH_MODEL = ParameterMeta(
    value="HISTORICAL_SCALED",
    tag=ParameterTag.PAPER,
    source_notes="Lấy ngẫu nhiên một đoạn lịch sử dài 168 giờ, co giãn theo biến động mục tiêu (Chaudhary và Pinna 2022)."
)

VOLATILITY_MULTIPLIER = ParameterMeta(
    value=1.0,  # gốc
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna thử tăng biến động theo giờ hơn 10 lần (cú sốc = 10.0).",
    scan_values=[1.0, 10.0]
)

GAS_FEE_USD = ParameterMeta(
    value=10.0,  # thấp
    tag=ParameterTag.PAPER,
    source_notes="Qin thử hai mức: 10 USD (thấp) và 100 USD (cao). Gas thực tế: TODO, tính từ chuỗi gas lịch sử.",
    scan_values=[10.0, 50.0, 100.0]
)

SLIPPAGE_FUNCTION = ParameterMeta(
    value={
        "formula": "sigma = gamma + s * (x / V)**omega",
        "gamma": 0.003,      # PLACEHOLDER
        "s": 1.0,            # PLACEHOLDER
        "omega": 1.0,        # PAPER
        "V": 1_000_000_000.0 # PAPER: 1 tỷ USD
    },
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna. Bài dùng cho Polygon; áp cho ETH trên Ethereum là suy rộng của nhóm."
)

# --- Tác nhân (Agents) ---
BORROWER_POPULATION = ParameterMeta(
    value={"dev": 100, "prod": 1000},
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna dùng 1.000 người dùng. Nhóm dùng 100 người để phát triển nhanh."
)

BORROWER_PORTFOLIO = ParameterMeta(
    value={
        "distribution": "lognormal",
        "mean_usd": 5000.0,
        "std_usd": None  # TODO
    },
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna. Độ lệch lognormal: TODO."
)

BORROWER_LTV = ParameterMeta(
    value={"mean": 0.60, "min": 0.45},
    tag=ParameterTag.PAPER,
    source_notes="Chaudhary và Pinna (LTV = nợ / giá trị thế chấp). HF ban đầu = LT / LTV = 0.8 / 0.6 = 1.33."
)

LENDER_POPULATION = ParameterMeta(
    value={
        "count": 50,
        "u0_initial": 0.60,
        "available_liquidity_ratio": 0.40  # 1 - U0
    },
    tag=ParameterTag.ASSUMPTION,
    source_notes="50 Lender. Tổng cung = tổng nợ ban đầu / U0; U0 = 0.60. Quét U0: 0.5; 0.7; 0.9.",
    scan_values=[0.50, 0.70, 0.90]
)

LIQUIDATOR_POPULATION = ParameterMeta(
    value={"count": 10},
    tag=ParameterTag.ASSUMPTION,
    source_notes="Qin quan sát 2.011 địa chỉ thật; số trong mô phỏng do nhóm chọn. Mỗi bước xáo trộn thứ tự bằng seed.",
    scan_values=[3, 10, 30]
)

RISK_APPETITE_DISTRIBUTION = ParameterMeta(
    value={"dist": "Beta", "alpha": 2.0, "beta": 2.0, "bounds": [0.0, 1.0]},
    tag=ParameterTag.ASSUMPTION,
    source_notes="RA là tham số mô hình, không phải phép đo tâm lý người dùng thật."
)


# ==============================================================================
# 2. KỊCH BẢN THỬ NGHIỆM (S0 ĐẾN S5)
# ==============================================================================

@dataclass
class ScenarioConfig:
    code: str
    name: str
    description: str
    eth_price_shock_pct: float = 0.0
    shock_start_step: int = 24
    shock_duration_steps: int = 24
    volatility_mult: float = 1.0
    gas_fee_usd: float = 10.0
    slippage_s_mult: float = 1.0
    slippage_v_mult: float = 1.0
    lender_withdraw_pct: float = 0.0
    lender_withdraw_duration_steps: int = 12
    target_utilization: Optional[float] = None
    target_utilization_duration_steps: int = 12
    scan_options: Dict[str, List[Any]] = field(default_factory=dict)
    tag: ParameterTag = ParameterTag.ASSUMPTION


SCENARIOS: Dict[str, ScenarioConfig] = {
    "S0": ScenarioConfig(
        code="S0",
        name="Cơ sở (Baseline)",
        description="Đường cơ sở để so sánh. Không có cú sốc ngoại sinh.",
        eth_price_shock_pct=0.0,
        volatility_mult=1.0,
        gas_fee_usd=10.0,
        slippage_s_mult=1.0,
        slippage_v_mult=1.0,
        lender_withdraw_pct=0.0,
        target_utilization=None,
        tag=ParameterTag.ASSUMPTION
    ),
    "S1": ScenarioConfig(
        code="S1",
        name="Cú sốc giá (Price Shock)",
        description="ETH giảm 43% trong 24 bước từ bước 24 (Qin ghi ETH giảm 43% ngày 13/3/2020).",
        eth_price_shock_pct=-0.43,
        shock_start_step=24,
        shock_duration_steps=24,
        volatility_mult=1.0,  # Biến thể 10.0
        gas_fee_usd=10.0,
        slippage_s_mult=1.0,
        slippage_v_mult=1.0,
        lender_withdraw_pct=0.0,
        scan_options={"eth_price_shock_pct": [-0.10, -0.20, -0.30, -0.43]},
        tag=ParameterTag.PAPER
    ),
    "S2": ScenarioConfig(
        code="S2",
        name="Cú sốc thanh khoản (Liquidity Shock)",
        description="Lender rút 50% tổng cung rải trong 12 bước từ bước 24.",
        eth_price_shock_pct=0.0,
        gas_fee_usd=10.0,
        slippage_s_mult=1.0,
        slippage_v_mult=1.0,
        lender_withdraw_pct=0.50,
        lender_withdraw_duration_steps=12,
        scan_options={"lender_withdraw_pct": [0.30, 0.50, 0.70]},
        tag=ParameterTag.ASSUMPTION
    ),
    "S3": ScenarioConfig(
        code="S3",
        name="Cú sốc lãi suất (Interest Rate Shock)",
        description="Utilization mục tiêu đạt 0.90 trong 12 bước từ bước 24, vượt U_opt 0.8 để kích hoạt slope2.",
        eth_price_shock_pct=0.0,
        gas_fee_usd=10.0,
        slippage_s_mult=1.0,
        slippage_v_mult=1.0,
        target_utilization=0.90,
        target_utilization_duration_steps=12,
        scan_options={"target_utilization": [0.85, 0.90, 0.95]},
        tag=ParameterTag.ASSUMPTION
    ),
    "S4": ScenarioConfig(
        code="S4",
        name="Cú sốc chi phí vận hành (Operational Cost Shock)",
        description="Giá ETH giảm 25% trong 24 bước; Gas tăng vọt 100 USD; Trượt giá tăng (s x 5, V x 0.1).",
        eth_price_shock_pct=-0.25,
        shock_start_step=24,
        shock_duration_steps=24,
        gas_fee_usd=100.0,
        slippage_s_mult=5.0,
        slippage_v_mult=0.1,
        scan_options={"gas_fee_usd": [10.0, 50.0, 100.0]},
        tag=ParameterTag.PAPER
    ),
    "S5": ScenarioConfig(
        code="S5",
        name="Cú sốc kết hợp (Combined Shock)",
        description="Kết hợp S1, S2, S4 bắt đầu cùng bước 24: ETH giảm 43%, rút 50%, Gas 100 USD, Trượt giá tăng mạnh.",
        eth_price_shock_pct=-0.43,
        shock_start_step=24,
        shock_duration_steps=24,
        gas_fee_usd=100.0,
        slippage_s_mult=5.0,
        slippage_v_mult=0.1,
        lender_withdraw_pct=0.50,
        lender_withdraw_duration_steps=12,
        tag=ParameterTag.ASSUMPTION
    )
}


# ==============================================================================
# 3. QUY TẮC HÀNH VI TÁC NHÂN (FIXED VS ADAPTIVE)
# ==============================================================================

BORROWER_BEHAVIOR = {
    "Fixed": {
        "can_borrow_more": False,
        "check_hf": True,
        "h_fixed_options": [1.05, 1.10, 1.20],
        "default_h_fixed": 1.10,
        "repay_ratio": 0.25,  # trả 25% dư nợ nếu HF < h_fixed
        "tag": ParameterTag.ASSUMPTION
    },
    "Adaptive": {
        "k_lookback_steps": 6,  # quét k bước
        "h_min_formula": "h_min = a - b * RA",
        "h_target_formula": "h_target = c - d * RA",
        "coefficients": {"a": None, "b": None, "c": None, "d": None},  # TODO
        "borrow_more_enabled": True,  # khi HF cao và borrow_rate thấp
        "tag": ParameterTag.ASSUMPTION
    }
}

LENDER_BEHAVIOR = {
    "Fixed": {
        "can_deposit_more": False,
        "can_withdraw": False,
        "tag": ParameterTag.ASSUMPTION
    },
    "Adaptive": {
        "withdraw_triggers": ["high_utilization", "bad_debt_occurred", "apy_below_benchmark"],
        "benchmark_apy": None,  # TODO
        "adaptive_ratio_scans": [0.0, 0.50, 1.0],  # 0%, 50%, 100%
        "tag": ParameterTag.ASSUMPTION
    }
}

LIQUIDATOR_BEHAVIOR = {
    "Fixed": {
        "selection": "FIRST_ELIGIBLE",
        "repay_amount": "CLOSE_FACTOR * debt",
        "condition": "estimated_net_profit > 0 with fixed gas",
        "tag": ParameterTag.PAPER
    },
    "Adaptive": {
        "selection": "MAX_PROFIT_SORTED",
        "slippage_aware": True,
        "gas_aware": True,
        "wait_if_negative_profit": True,
        "ra_participation": True,
        "models": ["Chaudhary_Pinna_2022", "Qin_Two_Step"],
        "tag": ParameterTag.PAPER
    }
}


# ==============================================================================
# 4. MA TRẬN THÍ NGHIỆM (E1 ĐẾN E12)
# ==============================================================================

EXPERIMENT_MATRIX = [
    {"experiment_id": "E1",  "scenario": "S0", "strategy": "Fixed",    "hypothesis": "Baseline Fixed"},
    {"experiment_id": "E2",  "scenario": "S0", "strategy": "Adaptive", "hypothesis": "Baseline Adaptive"},
    {"experiment_id": "E3",  "scenario": "S1", "strategy": "Fixed",    "hypothesis": "Test H1, H4 (Price Shock)"},
    {"experiment_id": "E4",  "scenario": "S1", "strategy": "Adaptive", "hypothesis": "Test H1, H4 (Price Shock)"},
    {"experiment_id": "E5",  "scenario": "S2", "strategy": "Fixed",    "hypothesis": "Test H3 (Liquidity Shock)"},
    {"experiment_id": "E6",  "scenario": "S2", "strategy": "Adaptive", "hypothesis": "Test H3 (Liquidity Shock)"},
    {"experiment_id": "E7",  "scenario": "S3", "strategy": "Fixed",    "hypothesis": "Interest Rate Shock"},
    {"experiment_id": "E8",  "scenario": "S3", "strategy": "Adaptive", "hypothesis": "Interest Rate Shock"},
    {"experiment_id": "E9",  "scenario": "S4", "strategy": "Fixed",    "hypothesis": "Test H2, H5 (Operational Cost Shock)"},
    {"experiment_id": "E10", "scenario": "S4", "strategy": "Adaptive", "hypothesis": "Test H2, H5 (Operational Cost Shock)"},
    {"experiment_id": "E11", "scenario": "S5", "strategy": "Fixed",    "hypothesis": "Test H5, H6 (Combined Shock)"},
    {"experiment_id": "E12", "scenario": "S5", "strategy": "Adaptive", "hypothesis": "Test H5, H6 (Combined Shock)"},
]


# ==============================================================================
# 5. BỘ KIỂM THỬ CHUẨN (SHARED BENCHMARK TEST SUITE)
# ==============================================================================

BENCHMARK_BORROWER_TEST = {
    "collateral_eth": 2.0,
    "debt_usdc": 2000.0,
    "liquidation_threshold": 0.80,
    "price_points": [
        {"eth_price": 2000.0, "collateral_value": 4000.0, "ltv": 0.5000, "hf": 1.60, "eligible": False},
        {"eth_price": 1500.0, "collateral_value": 3000.0, "ltv": 0.6667, "hf": 1.20, "eligible": False},
        {"eth_price": 1250.0, "collateral_value": 2500.0, "ltv": 0.8000, "hf": 1.00, "eligible": False},
        {"eth_price": 1000.0, "collateral_value": 2000.0, "ltv": 1.0000, "hf": 0.80, "eligible": True},
    ]
}


def validate_parameters() -> List[str]:
    """Kiểm tra các ràng buộc lý thuyết trong mục 5."""
    issues = []
    
    # 1. LT * (1 + Bonus) < 1 (Qin Phụ lục C)
    lt = LIQUIDATION_THRESHOLD.value
    bonus = LIQUIDATION_BONUS.value
    if lt * (1 + bonus) >= 1.0:
        issues.append(f"Vi phạm ràng buộc: LT * (1 + Bonus) = {lt * (1 + bonus):.4f} >= 1.0")

    for scan_lt in LIQUIDATION_THRESHOLD.scan_values or []:
        for scan_bonus in LIQUIDATION_BONUS.scan_values or []:
            if scan_lt * (1 + scan_bonus) >= 1.0:
                issues.append(f"Vi phạm quét: LT ({scan_lt}) * (1 + Bonus ({scan_bonus})) = {scan_lt * (1 + scan_bonus):.4f} >= 1.0")

    # 2. LTV ban đầu < LT
    if BORROWER_LTV.value["mean"] >= lt:
        issues.append(f"LTV trung bình ({BORROWER_LTV.value['mean']}) >= LT ({lt})")

    return issues


if __name__ == "__main__":
    validation_errors = validate_parameters()
    if validation_errors:
        print("[FAIL] Phát hiện vi phạm ràng buộc tham số:")
        for err in validation_errors:
            print(" -", err)
    else:
        print("[PASS] Tất cả các ràng buộc lý thuyết (LT * (1+Bonus) < 1, LTV < LT) đều thỏa mãn!")
