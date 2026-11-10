# Model Specification — DeFi Risk Lab

> Tài liệu này mô tả công thức, định nghĩa và giả định của mô hình mô phỏng rủi ro thanh lý.

## 1. Các thực thể chính

### Borrower (Người vay)
| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `borrower_id` | str | ID định danh duy nhất |
| `collateral_eth` | float | Lượng ETH thế chấp |
| `debt_usdc` | float | Lượng USDC đã vay |
| `is_liquidated` | bool | Đã thanh lý hoàn toàn? |
| `shortfall` | float | Khoản thiếu hụt tài sản bảo đảm sau thanh lý |

---

## 2. Công thức cốt lõi

### Health Factor (HF)
$$HF = \frac{collateral\_eth \times eth\_price \times liquidation\_threshold}{debt\_usdc}$$

- Nếu `HF < 1`: vị thế **đủ điều kiện thanh lý** (undercollateralized)
- Nếu `HF ≥ 1`: vị thế **an toàn**
- Nếu `debt_usdc = 0`: HF = ∞

### Giá trị thế chấp (USD)
$$collateral\_value\_usd = collateral\_eth \times eth\_price$$

---

## 3. Tham số mô hình

| Tham số | Giá trị | Mô tả |
|---|---|---|
| `LIQUIDATION_THRESHOLD` | **0.825** (82.5%) | Ngưỡng xác định mức thế chấp đủ điều kiện thanh lý |
| `LTV` | **0.80** (80%) | Loan-to-Value tối đa tại thời điểm vay |
| `CLOSE_FACTOR` | **0.50** (50%) | Tối đa 50% dư nợ được thanh lý trong một lần |
| `LIQUIDATION_BONUS` | **0.05** (5%) | Thưởng ETH cho liquidator (5% trên giá trị trả nợ) |

> **Lưu ý:** Các tham số này lấy cảm hứng từ Aave V3 nhưng được đơn giản hóa cho mục đích nghiên cứu, **không phản ánh tham số mainnet thực tế**.

---

## 4. Quy trình thanh lý

### Điều kiện kích hoạt
1. `HF < 1` (vị thế undercollateralized)
2. Lợi nhuận ròng > 0 sau chi phí gas
3. Liquidator có đủ vốn USDC

### Tính toán thanh lý

**Lượng nợ tối đa được trả:**
$$max\_repay = debt\_usdc \times CLOSE\_FACTOR$$

**Lượng ETH nhận được:**
$$eth\_to\_receive = \frac{actual\_repay \times (1 + LIQUIDATION\_BONUS)}{eth\_price}$$

Giới hạn: `eth_to_receive ≤ collateral_eth` (không thể nhận nhiều hơn thế chấp hiện có)

**Lợi nhuận ròng:**
$$net\_profit = (eth\_to\_receive \times eth\_price - actual\_repay) - gas\_cost\_usd$$

### Shortfall (thiếu hụt)
Phát sinh khi sau thanh lý, giá trị thế chấp còn lại vẫn không đủ bù đắp dư nợ:

$$shortfall = debt\_usdc - \frac{collateral\_eth \times eth\_price}{1 + LIQUIDATION\_BONUS} \quad \text{(nếu > 0)}$$

---

## 5. Giả định mô hình

| Giả định | Chi tiết |
|---|---|
| **Stablecoin peg** | 1 USDC = 1 USD (không có depeg risk) |
| **Oracle giá** | Giá ETH là ngoại sinh (exogenous), không có độ trễ hoặc thao túng |
| **Lãi suất** | Không có lãi suất động (static debt) |
| **Thanh lý tức thì** | Liquidator bán ETH nhận được ngay tại giá hiện tại |
| **Vòng mô phỏng** | Mỗi round xử lý tuần tự tất cả vị thế |
| **Price feedback** | Mặc định OFF; có thể bật với `price_feedback=True` (SHOULD feature) |

---

## 6. Nguồn tham khảo

- [Aave V3 Risk Parameters](https://docs.aave.com/risk/asset-risk/risk-parameters)
- [Aave V3 Liquidations](https://docs.aave.com/developers/guides/liquidations)
- Gauntlet Network — DeFi Risk Research
- Chaos Labs — Protocol Risk Simulations
