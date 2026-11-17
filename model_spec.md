# Model Specification — DeFi Risk Lab (DeFi Risk Simulation)
> **Phiên bản:** 0.1 | **Ngày lập:** 17/11/2026  
> **Tài liệu tham chiếu:** [config/parameters.py](file:///c:/Users/Tuana/.gemini/antigravity/scratch/defi-risk-simulation/config/parameters.py), [scope.md](file:///c:/Users/Tuana/.gemini/antigravity/scratch/defi-risk-simulation/scope.md), [tests/test_benchmark.py](file:///c:/Users/Tuana/.gemini/antigravity/scratch/defi-risk-simulation/tests/test_benchmark.py).

Tài liệu này mô tả chi tiết công thức toán học, quy tắc hành vi của tác nhân, cơ chế vận hành của giao thức và các giả định của mô hình mô phỏng DeFi Lending.

---

## 1. Các thực thể chính (Entities)

### 1.1. Borrower (Người vay)
| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `borrower_id` | `str` | Định danh người vay duy nhất |
| `collateral_eth` | `float` | Lượng ETH thế chấp hiện tại |
| `debt_usdc` | `float` | Dư nợ USDC hiện tại |
| `risk_appetite` ($RA$) | `float` | Khẩu vị rủi ro, phân phối $\text{Beta}(2, 2) \in [0, 1]$ |
| `strategy` | `str` | Chiến lược: `"fixed"` hoặc `"adaptive"` |
| `is_liquidated` | `bool` | Đã bị thanh lý hoàn toàn hay chưa |
| `shortfall` | `float` | Thâm hụt tài sản bảo đảm còn lại |

### 1.2. Lender (Người gửi tiền)
| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `lender_id` | `str` | Định danh người gửi tiền |
| `deposited_usdc` | `float` | Số dư USDC đang gửi trong bể |
| `risk_appetite` ($RA$) | `float` | Khẩu vị rủi ro, phân phối $\text{Beta}(2, 2) \in [0, 1]$ |
| `strategy` | `str` | Chiến lược: `"fixed"` hoặc `"adaptive"` |
| `pending_withdrawal` | `float` | Số USDC đang nằm trong hàng chờ rút tiền |
| `realized_loss` | `float` | Tổn thất nợ xấu gánh chịu theo tỷ lệ |

### 1.3. Liquidator (Người thanh lý)
| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `liquidator_id` | `str` | Định danh người thanh lý |
| `capital_usdc` | `float` | Vốn USDC sẵn có để thanh lý |
| `risk_appetite` ($RA$) | `float` | Khẩu vị rủi ro, phân phối $\text{Beta}(2, 2) \in [0, 1]$ |
| `strategy` | `str` | Chiến lược: `"fixed"` hoặc `"adaptive"` |
| `total_profit_usd` | `float` | Lợi nhuận tích lũy sau thanh lý |

### 1.4. Lending Pool (Bể cho vay USDC)
| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `total_supply` ($S$) | `float` | Tổng lượng USDC do Lender gửi vào bể |
| `total_borrowed` ($D$) | `float` | Tổng dư nợ USDC đang được vay |
| `available_cash` ($C$) | `float` | Thanh khoản USDC khả dụng ($C = S - D$) |
| `utilization_rate` ($U$) | `float` | Tỷ lệ sử dụng vốn ($U = D / S$) |
| `bad_debt_pool` | `float` | Tổng nợ xấu tích lũy của giao thức |
| `withdrawal_queue` | `list` | Danh sách các yêu cầu rút tiền đang chờ xử lý |

---

## 2. Công thức toán học cốt lõi

### 2.1. Định giá tài sản thế chấp & Health Factor (HF)
- **Giá trị thế chấp (USD):**
  $$V_{collateral} = collateral\_eth \times P_{ETH}$$
- **Tỷ lệ nợ trên thế chấp (Loan-to-Value - LTV):**
  $$LTV = \frac{debt\_usdc}{V_{collateral}}$$
- **Health Factor (HF):**
  $$HF = \frac{collateral\_eth \times P_{ETH} \times LT}{debt\_usdc}$$
  *(Quy ước: Nếu $debt\_usdc = 0$, $HF = \infty$. Vị thế bị xem là undercollateralized và đủ điều kiện thanh lý khi $HF < 1.0$).*

### 2.2. Mô hình Lãi suất Kink (Kink Interest Rate Model)
Tỷ lệ sử dụng vốn:
$$U = \frac{D}{S}$$
- Khi $U \le U_{opt}$:
  $$R_{borrow} = R_{base} + \frac{U}{U_{opt}} \times Slope_1$$
- Khi $U > U_{opt}$:
  $$R_{borrow} = R_{base} + Slope_1 + \frac{U - U_{opt}}{1 - U_{opt}} \times Slope_2$$
- Lãi suất người gửi:
  $$R_{supply} = U \times R_{borrow} \times (1 - Reserve\_Factor)$$

### 2.3. Quy trình thanh lý & Lợi nhuận Liquidator
- **Lượng nợ tối đa được thanh lý (Max Repay):**
  $$repay_{max} = debt\_usdc \times Close\_Factor$$
- **Lượng ETH chuyển giao cho Liquidator:**
  $$eth\_received = \frac{repay \times (1 + Liquidation\_Bonus)}{P_{ETH}}$$
  *(Ràng buộc an toàn: $eth\_received \le collateral\_eth$).*
- **Hàm trượt giá DEX khi Liquidator bán ETH lấy lại USDC:**
  $$\sigma = \gamma + s \times \left(\frac{x}{V}\right)^\omega \quad (\omega = 1, \; V = 1.000.000.000 \text{ USD})$$
  *(Trong đó $x = eth\_received \times P_{ETH}$ là quy mô lệnh bán).*
- **Giá bán ETH thực tế trên DEX sau trượt giá:**
  $$P_{sell} = P_{ETH} \times (1 - \sigma)$$
- **Lợi nhuận ròng của Liquidator:**
  $$\Pi_{liquidator} = (eth\_received \times P_{sell} - repay) - gas\_cost$$

### 2.4. Nợ xấu (Bad Debt) & Xã hội hóa tổn thất
- Nếu sau thanh lý, giá trị thế chấp còn lại không đủ bù đắp dư nợ còn lại:
  $$Collateral_{rem} \times P_{ETH} < Debt_{rem}$$
- Khoản nợ xấu phát sinh (loại I theo Qin):
  $$BadDebt = Debt_{rem} - (Collateral_{rem} \times P_{ETH})$$
- Phân bổ tổn thất cho Lender (Haircut):
  $$Loss_{i} = BadDebt \times \frac{deposited\_usdc_{i}}{Total\_Supply}$$

---

## 3. Quy tắc hành vi tác nhân (Fixed vs Adaptive)

### 3.1. Borrower
- **Cố định (Fixed):** Không vay thêm. Nếu $HF < h_{fixed}$ (quét $1.05, 1.10, 1.20$), thực hiện bổ sung thế chấp hoặc trả lời $25\%$ dư nợ.
- **Thích nghi (Adaptive):**
  - Tính toán lợi suất ETH trong $k$ bước gần nhất.
  - Thiết lập ngưỡng động phụ thuộc $RA$: $h_{min}(RA) = a - b \times RA$; $h_{target}(RA) = c - d \times RA$.
  - Nếu $HF < h_{min}(RA)$ hoặc giá giảm nhanh: bổ sung thế chấp / trả nợ đưa HF về $h_{target}(RA)$, nếu lợi ích bảo vệ vị thế $> gas\_cost$.
  - Khi HF cao an toàn và lãi vay thấp: có xác suất vay thêm vốn (tỷ lệ thuận với $RA$).

### 3.2. Lender
- **Cố định (Fixed):** Giữ nguyên số dư gửi, không nạp thêm, không rút tiền trong suốt 168 bước.
- **Thích nghi (Adaptive):**
  - Xác suất rút vốn tăng khi utilization $U > U_{opt}$, khi phát sinh nợ xấu trong bể, hoặc khi lãi suất gửi $R_{supply} < R_{benchmark}$.
  - $RA$ càng thấp $\implies$ phản ứng rút vốn càng nhanh (tháo chạy bảo toàn vốn).
  - Có xu hướng nạp thêm tiền khi $R_{supply}$ cao và utilization an toàn.

### 3.3. Liquidator
- **Cố định (Fixed):** Chọn vị thế đầu tiên có $HF < 1$, trả cố định $Close\_Factor \times debt$, thanh lý nếu lợi nhuận sau phí gas cố định $> 0$.
- **Thích nghi (Adaptive):**
  - Quét toàn bộ vị thế vi phạm, ước tính lợi nhuận ròng thực tế sau khi tính đến trượt giá sàn DEX $\sigma$ và phí gas thời điểm thực thi.
  - Sắp xếp và ưu tiên thanh lý vị thế có $\Pi_{net}$ kỳ vọng cao nhất.
  - Tạm hoãn thanh lý nếu thanh khoản DEX quá mỏng hoặc gas quá cao làm $\Pi_{net} \le 0$.

---

## 4. Bảng kiểm tra chuẩn hóa (Benchmark Test Suite)

Áp dụng cho vị thế chuẩn: **2 ETH thế chấp, nợ 2.000 USDC, LT = 0.80**.

| Giá ETH ($P_{ETH}$) | Giá trị thế chấp ($V_{col}$) | LTV | Health Factor ($HF$) | Trạng thái vị thế |
|---|---|---|---|---|
| **2.000 USD** | 4.000 USD | 0.5000 | **1.60** | An toàn tuyệt đối |
| **1.500 USD** | 3.000 USD | 0.6667 | **1.20** | Tiệm cận vùng rủi ro |
| **1.250 USD** | 2.500 USD | 0.8000 | **1.00** | Đúng ngưỡng thanh lý ($HF = 1.0$) |
| **1.000 USD** | 2.000 USD | 1.0000 | **0.80** | Dưới ngưỡng, thế chấp bằng nợ (bắt đầu nợ xấu) |

---

## 5. Ràng buộc an toàn & Giả định kỹ thuật

1. **Ràng buộc an toàn tham số:** $LT \times (1 + Liquidation\_Bonus) < 1.0$. Với $LT=0.80$ và $Bonus=0.05 \implies 0.80 \times 1.05 = 0.84 < 1.0$ (thỏa mãn).
2. **Khẩu vị rủi ro:** $0 \le RA \le 1$ với mọi tác nhân.
3. **Bảo toàn bể:** Tổng cung USDC của bể cho vay không bao gồm giá trị của ETH thế chấp.
4. **Peg ổn định:** 1 USDC = 1 USD trong toàn bộ quá trình mô phỏng.
5. **Thực thi Smart Contract:** Hợp đồng trên Sepolia tuân thủ chính xác các ngưỡng kiểm thử trong Bảng mục 4.
