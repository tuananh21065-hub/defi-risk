# Ví dụ tính tay — DeFi Risk Lab

> 3 ví dụ minh họa cách tính Health Factor và xác định điều kiện thanh lý.

---

## Công thức

$$HF = \frac{collateral\_eth \times eth\_price \times liquidation\_threshold}{debt\_usdc}$$

Với `liquidation_threshold = 0.825`

---

## Ví dụ 1 — Vị thế An toàn (HF > 1)

| Tham số | Giá trị |
|---|---|
| Collateral | 5 ETH |
| Giá ETH | $2,000 |
| Dư nợ (debt) | $5,000 USDC |
| Liquidation Threshold | 0.825 |

**Tính:**
$$HF = \frac{5 \times 2000 \times 0.825}{5000} = \frac{8250}{5000} = \mathbf{1.65}$$

**Kết quả:** HF = 1.65 > 1 → ✅ **Vị thế an toàn**, không đủ điều kiện thanh lý.

Giá ETH phải giảm xuống dưới:
$$eth\_price_{min} = \frac{debt\_usdc}{collateral\_eth \times liq\_threshold} = \frac{5000}{5 \times 0.825} \approx \$1,212$$
mới có nguy cơ thanh lý.

---

## Ví dụ 2 — Đủ điều kiện thanh lý (HF < 1)

| Tham số | Giá trị |
|---|---|
| Collateral | 5 ETH |
| Giá ETH | $2,000 |
| Dư nợ (debt) | $9,000 USDC |
| Liquidation Threshold | 0.825 |

**Tính:**
$$HF = \frac{5 \times 2000 \times 0.825}{9000} = \frac{8250}{9000} \approx \mathbf{0.917}$$

**Kết quả:** HF = 0.917 < 1 → ⚠️ **Đủ điều kiện thanh lý.**

**Mô phỏng thanh lý (Close Factor = 50%):**
- Nợ được trả: `9000 × 0.50 = $4,500 USDC`
- ETH nhận (+ 5% bonus): `4500 × 1.05 / 2000 = 2.3625 ETH`
- Lợi nhuận gross: `4500 × 0.05 = $225`
- Lợi nhuận net (sau gas $5): **$220**

---

## Ví dụ 3 — Thiếu hụt nghiêm trọng (Shortfall)

| Tham số | Giá trị |
|---|---|
| Collateral | 1 ETH |
| Giá ETH | $1,200 |
| Dư nợ (debt) | $2,000 USDC |
| Liquidation Threshold | 0.825 |

**Tính:**
$$HF = \frac{1 \times 1200 \times 0.825}{2000} = \frac{990}{2000} = \mathbf{0.495}$$

**Kết quả:** HF = 0.495 < 1 → 🔴 **Thiếu hụt nghiêm trọng.**

Tổng giá trị thế chấp = $1,200 < Dư nợ = $2,000

**Shortfall ước tính:**
$$shortfall = debt - \frac{collateral\_value}{1 + bonus} = 2000 - \frac{1200}{1.05} \approx \$857$$

Ngay cả sau khi thanh lý toàn bộ thế chấp, giao thức vẫn **thiếu ~$857** — đây là **bad debt**, thường được xã hội hóa hoặc bù từ quỹ bảo hiểm.

---

## Bộ kiểm thử chuẩn hóa dùng chung (Benchmark Suite v0.1)

Áp dụng cho vị thế chuẩn dùng chung giữa mô phỏng Python và Smart Contract trên Sepolia Testnet ([tests/test_benchmark.py](file:///c:/Users/Tuana/.gemini/antigravity/scratch/defi-risk-simulation/tests/test_benchmark.py)):
- **Thế chấp:** 2 ETH
- **Dư nợ:** 2.000 USDC
- **Liquidation Threshold ($LT$):** 0.80

$$HF = \frac{Collateral \times P_{ETH} \times LT}{Debt} = \frac{2 \times P_{ETH} \times 0.80}{2000} = \frac{1.6 \times P_{ETH}}{2000}$$

| Mốc giá ETH ($P_{ETH}$) | Giá trị thế chấp ($V_{col}$) | LTV ($Debt / V_{col}$) | Health Factor ($HF$) | Đánh giá trạng thái |
|---|---|---|---|---|
| **$2.000** | $4.000 | 0.5000 (50%) | **1.60** | ✅ An toàn tuyệt đối ($HF \ge 1.0$) |
| **$1.500** | $3.000 | 0.6667 (66.67%) | **1.20** | ⚠️ Vùng rủi ro, tiệm cận ngưỡng thanh lý |
| **$1.250** | $2.500 | 0.8000 (80%) | **1.00** | 🚨 Đúng ngưỡng thanh lý ($HF = 1.0$) |
| **$1.000** | $2.000 | 1.0000 (100%) | **0.80** | 🔴 Dưới ngưỡng, thế chấp bằng nợ (bắt đầu nợ xấu) |

