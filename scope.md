# Phạm vi dự án — DeFi Risk Lab (DeFi Risk Simulation)
> **Phiên bản:** 0.1 | **Ngày lập:** 17/11/2026  
> **Đề tài:** Nghiên cứu khả năng chống chịu rủi ro của giao thức cho vay DeFi dưới tác động của biến động thị trường và hành vi tương tác giữa các tác nhân (Bài tập lớn Blockchain).  
> **Tài liệu tham chiếu:** [config/parameters.py](file:///c:/Users/Tuana/.gemini/antigravity/scratch/defi-risk-simulation/config/parameters.py), [tests/test_benchmark.py](file:///c:/Users/Tuana/.gemini/antigravity/scratch/defi-risk-simulation/tests/test_benchmark.py).

---

## 1. Tóm tắt dự án & Mục tiêu mới

### 1.1. Bối cảnh & Đề tài
Nghiên cứu khả năng chống chịu rủi ro và an toàn tài chính của giao thức cho vay phi tập trung (DeFi Lending Pool) khi đối mặt với các cú sốc thị trường cực đoan (giá tài sản thế chấp sụt giảm, biến động tăng vọt, phí gas tăng cao, thanh khoản DEX cạn kiệt) và sự tương tác phức tạp giữa các nhóm tác nhân có hành vi thích nghi.

### 1.2. Mô hình nghiên cứu
- **Cấu trúc thị trường:** Một bể thanh khoản USDC, sử dụng ETH làm tài sản thế chấp duy nhất. 1 USDC = 1 USD (bảo đảm chốt giá). Không cộng dồn ETH thế chấp vào tổng cung USDC của bể.
- **Phương pháp luận:** Kết hợp **Mô phỏng đa tác nhân (Agent-Based Model - ABM)**, **Mô phỏng ngẫu nhiên Monte Carlo** và **Kiểm thử sức chịu đựng (Stress Testing)**.
- **Thời gian mô phỏng:** 168 bước thời gian (tương đương 7 ngày, mỗi bước 1 giờ).
- **Quy mô Monte Carlo:** 100 lần chạy (giai đoạn phát triển / kiểm thử); 1.000 lần chạy (giai đoạn thực nghiệm chính thức).
- **Cơ chế đối chứng:** Cố định `seed = 42` trên cùng đường giá để so sánh công bằng giữa chiến lược Cố định (Fixed) và Thích nghi (Adaptive).

### 1.3. Ba sản phẩm chuyển giao bắt buộc (Deliverables)
1. **Mô phỏng Python (Core ABM Engine):** Động cơ mô phỏng 168 bước, tích hợp mô hình lãi suất có điểm gãy (Kink model), hàng chờ rút tiền, hàm trượt giá DEX phi tuyến, chi phí gas và cơ chế xã hội hóa nợ xấu.
2. **Dashboard tương tác (Streamlit Dashboard):** Giao diện web trực quan hóa diễn biến theo thời gian thực (168h), cho phép chọn kịch bản S0–S5, đối chiếu trực tiếp chiến lược Fixed vs Adaptive và biểu diễn các chỉ số thanh lý, nợ xấu, utilization.
3. **Smart Contract trên Testnet:** Hợp đồng thông minh Lending Pool tối giản triển khai và kiểm thử trên **Ethereum Sepolia Testnet** (yêu cầu bắt buộc theo đề bài; Sepolia là testnet chuẩn được ethereum.org khuyến nghị).

---

## 2. Hai câu hỏi nghiên cứu cốt lõi (Core Research Questions)

- **RQ1 (Điều kiện thị trường & Chi phí vận hành):**  
  > *Biến động giá ETH, mức độ biến động lợi suất theo giờ, chi phí gas mạng lưới ($10 vs $100/tx) và trượt giá DEX ảnh hưởng như thế nào đến khả năng giải chấp kịp thời của Liquidator, tỷ lệ thanh lý thành công và nguy cơ phát sinh nợ xấu (bad debt) cho giao thức?*

- **RQ2 (Hành vi thích nghi & Tương tác tác nhân dưới các cú sốc đồng thời):**  
  > *Sự tương tác giữa hành vi thích nghi (Adaptive) của Borrower (tự vệ vị thế / nạp thêm thế chấp / trả nợ / vay thêm), Lender (tháo chạy thanh khoản khi nhận thấy rủi ro) và Liquidator (chọn lọc vị thế tối ưu lợi nhuận) làm khuếch đại hay giảm nhẹ rủi ro hệ thống so với hành vi cố định (Fixed), đặc biệt khi đồng thời xảy ra nhiều cú sốc (giá sụt giảm, thanh khoản cạn kiệt, lãi suất tăng vọt, chi phí vận hành leo thang)?*

---

## 3. Bảng so sánh thay đổi Scope (Scope Delta: v0.0 cũ vs v0.1 mới)

| Thành phần | Scope v0.0 (Cũ - Đã lỗi thời) | Scope v0.1 (Mới - Chuẩn hiện hành) | Lý do điều chỉnh |
|---|---|---|---|
| **Các nhóm tác nhân (Agents)** | Chỉ có Borrower và 1 Liquidator đơn lẻ. Người vay thụ động, không có hành vi tự vệ. | **3 nhóm tác nhân:** Borrower, Lender (50), Liquidator (10-30). Đầy đủ 2 chế độ: **Fixed** và **Adaptive**. | Yêu cầu mô hình ABM phản ánh chính xác thị trường tài chính tương tác. |
| **Giao thức & Thanh khoản** | Bể thanh khoản tĩnh, nợ cố định không lãi suất, không có Lender. | Bể USDC năng động; có **Lãi suất Kink (U_opt = 0.8)**; **Hàng chờ rút tiền (Queue)** khi cạn thanh khoản. | Mô phỏng chính xác rủi ro thanh khoản rút tiền (Bank-run) và sốc lãi suất. |
| **Cơ chế Nợ xấu (Bad Debt)** | Chỉ tính `shortfall` lý thuyết, không phân bổ. Đánh dấu ❌ NOT NOW ở cơ chế xã hội hóa. | **Xã hội hóa nợ xấu loại I (Qin):** Sau thanh lý, phần thiếu hụt được phân bổ trực tiếp cho Lender gánh chịu theo tỷ lệ. | Đánh giá chính xác tổn thất của người gửi tiền và an toàn giao thức. |
| **Mô hình Trượt giá DEX** | Thị trường tĩnh hoặc giả định trượt giá tuyến tính đơn giản. Đánh dấu ❌ NOT NOW ở AMM thực. | **Hàm trượt giá phi tuyến (Chaudhary & Pinna):** $\sigma = \gamma + s \times (x/V)^\omega$ với $\omega=1, V=10^9$. | Phản ánh chi phí thanh lý thực tế khi Liquidator xả ETH ra thị trường. |
| **Khung Kịch bản & Thí nghiệm** | 4 mức sốc giá tĩnh (0%, -10%, -20%, -30%) trong vài round rời rạc. | **6 kịch bản chuẩn hóa S0–S5** trong 168 bước; ma trận **12 thực nghiệm E1–E12** kiểm chứng các giả thuyết H1–H6. | Khung Stress Testing chuẩn mực theo khuyến nghị học thuật. |
| **Smart Contract** | ❌ Đánh dấu `NOT NOW: Smart contract integration / on-chain execution`. | **BẮT BUỘC (MUST):** Hợp đồng Lending Pool rút gọn triển khai trên **Ethereum Sepolia Testnet** cùng bộ test dùng chung. | Yêu cầu bắt buộc từ đề bài bài tập lớn Blockchain. |
| **Bộ kiểm thử dùng chung** | Testcase phân tán trong pytest. | **Bộ kiểm thử chuẩn (Benchmark Suite)** dùng chung giữa Python và Smart Contract (2 ETH, 2.000 USDC, LT 0.8 tại 4 mốc giá). | Bảo đảm tính nhất quán toán học tuyệt đối giữa mô phỏng và hợp đồng on-chain. |

---

## 4. Phân loại yêu cầu theo khung MoSCoW

```
                  ┌──────────────────────────────────────────────┐
                  │           KHUNG PHẠM VI DỰ ÁN (MoSCoW)        │
                  └──────────────────────┬───────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
 ┌───────────────┐               ┌───────────────┐               ┌───────────────┐
 │     MUST      │               │    SHOULD     │               │    NOT NOW    │
 │ (Bắt buộc v0.1)│               │  (Giai đoạn 2)│               │ (Ngoài phạm vi)│
 └───────────────┘               └───────────────┘               └───────────────┘
```

### 4.1. MUST — Bắt buộc phải có (Core Requirements)

#### A. Kiến trúc Mô phỏng Đa tác nhân (ABM)
- [x] **Không gian thời gian:** 168 bước (mỗi bước = 1 giờ = 7 ngày).
- [x] **Cơ chế Seed:** Cố định `seed = 42` để tái lập toàn bộ đường giá và ngẫu nhiên hóa; đảm bảo so sánh đối xứng giữa kịch bản Fixed và Adaptive.
- [x] **Tác nhân Borrower:**
  - Quy mô: 100 tác nhân (dev) / 1.000 tác nhân (chính thức).
  - Vị thế ban đầu: Lognormal, trung bình 5.000 USD; LTV ban đầu trung bình 0.60 (tối thiểu 0.45); $HF_{init} = LT / LTV = 0.8 / 0.6 \approx 1.33$.
  - Khẩu vị rủi ro: $RA \sim \text{Beta}(2, 2) \in [0, 1]$.
  - **Chiến lược Fixed:** Không vay thêm. Nếu $HF < h_{fixed}$ (quét 1.05, 1.10, 1.20) thì bổ sung thế chấp hoặc trả nợ 25% dư nợ.
  - **Chiến lược Adaptive:** Quan sát lợi suất ETH trong $k$ bước; nếu $HF < h_{min}(RA)$ hoặc giá giảm nhanh $\to$ bổ sung thế chấp/trả nợ đến khi đạt $h_{target}(RA)$ (nếu lợi ích ròng > phí gas); khi HF cao và lãi vay thấp $\to$ vay thêm với xác suất tăng theo RA.
- [x] **Tác nhân Lender:**
  - Quy mô: 50 tác nhân. Tổng cung ban đầu $S_0 = D_0 / U_0$ ($U_0 = 0.60$, thanh khoản khả dụng $Cash_0 = 40\%$). Quét $U_0 \in \{0.5, 0.7, 0.9\}$.
  - **Chiến lược Fixed:** Gửi tiền thụ động, không nạp thêm, không rút tiền trong suốt 168 bước.
  - **Chiến lược Adaptive:** Tỷ lệ rút tiền tăng khi tỷ lệ sử dụng vốn ($U$) tăng cao, khi xuất hiện nợ xấu, hoặc lãi gửi thấp hơn lãi tham chiếu (RA thấp rút trước); gửi thêm khi lãi gửi cao và $U$ thấp.
- [x] **Tác nhân Liquidator:**
  - Quy mô: 10 tác nhân (quét 3, 10, 30). Mỗi bước xáo trộn ngẫu nhiên thứ tự hành động; mỗi vị thế chỉ bị thanh lý 1 lần trong 1 bước thời gian.
  - **Chiến lược Fixed:** Chọn vị thế vi phạm ($HF < 1$) đầu tiên theo thứ tự, trả đúng $Close\ Factor \times Dư\ nợ$ (50%), chỉ gửi giao dịch nếu lợi nhuận ròng ước tính $> 0$ với phí gas cố định.
  - **Chiến lược Adaptive:** Quét toàn bộ vị thế đủ điều kiện, sắp xếp và ưu tiên vị thế mang lại lợi nhuận ròng kỳ vọng cao nhất sau khi trừ phí gas hiện tại và hàm trượt giá DEX $\sigma$; hoãn thanh lý nếu lợi nhuận âm.

#### B. Cơ chế Giao thức & Kinh tế học DeFi
- [x] **Tài sản:** ETH làm thế chấp, USDC là tài sản vay (1 USDC = 1 USD). Không cộng ETH thế chấp vào tổng cung USDC.
- [x] **Tham số thanh lý:**
  - $Close\ Factor = 0.50$ (PAPER).
  - $Liquidation\ Threshold\ (LT) = 0.80$ (quét: 0.70, 0.75, 0.80, 0.85).
  - $Liquidation\ Bonus = 0.05$ (quét: 0.05, 0.08, 0.10, 0.15).
  - Ràng buộc an toàn: $LT \times (1 + Bonus) < 1.0$ (Qin).
- [x] **Mô hình Lãi suất Kink (Piecewise Linear Interest Rate):**
  - $U = \frac{Total\ Borrowed}{Total\ Supply}$
  - Nếu $U \le U_{opt}$: $R_{borrow} = R_{base} + \frac{U}{U_{opt}} \times Slope_1$
  - Nếu $U > U_{opt}$: $R_{borrow} = R_{base} + Slope_1 + \frac{U - U_{opt}}{1 - U_{opt}} \times Slope_2$
  - Lãi suất người gửi: $R_{supply} = U \times R_{borrow} \times (1 - Reserve\ Factor)$
  - Tham số cơ sở: $R_{base}=0.0$, $Slope_1=0.04$, $Slope_2=0.75$, $U_{opt}=0.80$, $Reserve\ Factor=0.10$. Quét $U_{opt} \in \{0.45, 0.80, 0.90\}$.
- [x] **Hàng chờ rút tiền (Withdrawal Queue):**
  - Khi yêu cầu rút tiền vượt quá thanh khoản khả dụng ($Cash$), giao thức chi trả tối đa phần khả dụng; phần còn lại đưa vào hàng chờ ưu tiên theo thời gian yêu cầu để thanh toán ở các bước sau khi có dòng tiền nạp hoặc trả nợ.
- [x] **Xã hội hóa Nợ xấu (Bad Debt Socialization):**
  - Khi thanh lý xong mà giá trị tài sản thế chấp còn lại không đủ bù đắp dư nợ còn lại ($Collateral \times P < Debt$), khoản chênh lệch là Nợ xấu loại I (Qin).
  - Nợ xấu được ghi nhận và khấu trừ trực tiếp vào tổng tài sản của các Lender theo tỷ lệ tiền gửi (haircut).

#### C. Mô hình Thị trường & Chi phí Vận hành
- [x] **Mô hình đường giá ETH:** Lấy chuỗi 168 giờ, co giãn theo hệ số biến động mục tiêu (1.0 gốc vs 10.0 cú sốc).
- [x] **Chi phí Gas:** Hai mức khảo sát chuẩn: 10 USD/tx (thấp) và 100 USD/tx (cao - nghẽn mạng).
- [x] **Hàm trượt giá DEX phi tuyến:**
  $$\sigma(x) = \gamma + s \times \left(\frac{x}{V}\right)^\omega \quad (\omega = 1, \; V = 1.000.000.000 \text{ USD})$$
  - $\gamma = 0.003$ (phí swap cơ sở 0.3%).
  - $s = 1.0$ (kịch bản bình thường) và $s = 5.0, V = 100.000.000 \text{ USD}$ (kịch bản sốc thanh khoản thị trường).

#### D. Ma trận 6 Kịch bản (S0–S5) & 12 Thực nghiệm (E1–E12)
- [x] **S0 (Cơ sở):** Giữ nguyên đường giá lịch sử, biến động 1.0, gas $10, trượt giá chuẩn, không có rút vốn đột ngột.
- [x] **S1 (Cú sốc giá):** ETH giảm 43% trong 24 bước (từ bước 24), biến động x10. Kiểm tra giả thuyết H1, H4.
- [x] **S2 (Cú sốc thanh khoản):** Lender rút 50% tổng cung trong 12 bước (từ bước 24). Kiểm tra giả thuyết H3.
- [x] **S3 (Cú sốc lãi suất):** Tác động utilization tăng vọt lên 0.90 trong 12 bước (từ bước 24), kích hoạt vùng lãi suất dốc $Slope_2$.
- [x] **S4 (Cú sốc chi phí vận hành):** Phí gas tăng vọt 100 USD/tx, trượt giá tăng ($s \times 5, V \times 0.1$), giá ETH giảm 25% trong 24 bước. Kiểm tra giả thuyết H2, H5.
- [x] **S5 (Cú sốc kết hợp):** Đồng thời kích hoạt sốc giá S1 (-43%), sốc thanh khoản S2 (rút 50%) và sốc vận hành S4 (gas $100, trượt giá tăng). Kiểm tra giả thuyết H5, H6.
- [x] **Chạy đối xứng:** Thực nghiệm E1 đến E12 (E_lẻ: Fixed, E_chẵn: Adaptive) trên cùng điều kiện ban đầu và đường giá.

#### E. Smart Contract trên Testnet Sepolia
- [x] **Hợp đồng Lending Pool tối giản (Solidity):**
  - Chức năng cốt lõi: `deposit(amount)`, `borrow(amount)`, `repay(amount)`, `withdraw(amount)`, `liquidate(borrower, amount)`.
  - Tích hợp Oracle mock (có thể cập nhật giá ETH để mô phỏng sốc giá).
  - Logic tính Health Factor, Close Factor (50%), Liquidation Bonus (5%) tương thích với Python.
- [x] **Triển khai & Kiểm thử trên Ethereum Sepolia Testnet:**
  - Triển khai hợp đồng lên Sepolia (testnet chuẩn của ethereum.org).
  - Kịch bản kiểm thử on-chain tương ứng với bộ benchmark testcase.

#### F. Bộ kiểm thử chuẩn dùng chung (Shared Benchmark Suite)
- [x] **Ràng buộc bất biến:**
  - $LT \times (1 + Bonus) < 1.0$
  - $LTV_{init} < LT$ với mọi Borrower
  - $0 \le RA \le 1$
  - Tổng cung USDC không gồm ETH thế chấp
- [x] **Test Vector chuẩn hóa (2 ETH thế chấp, nợ 2.000 USDC, LT = 0.80):**
  - $P = 2.000$ USD $\implies Collateral = 4.000$ USD, $LTV = 0.50$, $HF = 1.60$ (An toàn)
  - $P = 1.500$ USD $\implies Collateral = 3.000$ USD, $LTV = 0.6667$, $HF = 1.20$ (Cảnh báo)
  - $P = 1.250$ USD $\implies Collateral = 2.500$ USD, $LTV = 0.80$, $HF = 1.00$ (Chạm ngưỡng thanh lý)
  - $P = 1.000$ USD $\implies Collateral = 2.000$ USD, $LTV = 1.00$, $HF = 0.80$ (Thế chấp bằng nợ, bắt đầu nợ xấu)
- [x] Kiểm thử an toàn: Chặn vay vượt trần $LTV$, chặn rút vượt thanh khoản khả dụng $Cash$.

#### G. Streamlit Dashboard
- [x] Cập nhật giao diện hỗ trợ xem kết quả theo chuỗi thời gian 168 bước.
- [x] Bảng chọn kịch bản S0–S5 và chế độ chiến lược (Fixed vs Adaptive).
- [x] Biểu đồ đường (Line charts) theo thời gian: Giá ETH, Health Factor trung bình, Tỷ lệ sử dụng vốn ($U$), Lãi suất vay/gửi, Dư nợ xấu tích lũy, Chiều dài hàng chờ rút tiền.
- [x] Bảng đối chiếu các chỉ số tổng hợp giữa Fixed và Adaptive.

---

### 4.2. SHOULD — Nên có (Giai đoạn hoàn thiện & Mở rộng)

- [ ] **Tích hợp dữ liệu thị trường lịch sử thật:**
  - Nạp chuỗi dữ liệu nến 1h ETHUSDT thực tế từ Binance Vision (thay cho giả định độ lệch chuẩn).
  - Nạp chuỗi phí gas lịch sử thực tế của Ethereum Mainnet theo giờ.
- [ ] **Hiệu chỉnh tham số hành vi thích nghi (Calibration):**
  - Thực hiện grid search tìm bộ tham số tối ưu $a, b, c, d, k$ cho Borrower thích nghi và lãi suất tham chiếu cho Lender.
- [ ] **Thực nghiệm Hybrid Tác nhân (cho giả thuyết H6):**
  - Chạy các tổ hợp hỗn hợp: chỉ Borrower thích nghi, chỉ Lender thích nghi, hoặc chỉ Liquidator thích nghi để bóc tách độ nhạy đóng góp của từng nhóm vào rủi ro chung.
- [ ] **Cơ chế thanh lý 2 bước (Qin):**
  - Thực nghiệm so sánh giữa mô hình thanh lý tức thì 1 bước (Chaudhary & Pinna) và mô hình 2 bước tối ưu (Qin).
- [ ] **Xuất báo cáo tự động:**
  - Xuất bảng biểu và đồ thị sang định dạng LaTeX / Markdown phục vụ viết báo cáo khoa học.

---

### 4.3. NOT NOW — Ngoài phạm vi bài tập lớn

- ❌ **Đa tài sản thế chấp (Multi-collateral):** Không hỗ trợ WBTC, stETH hay altcoins; giữ nguyên phạm vi 1 cặp duy nhất ETH thế chấp / USDC nợ.
- ❌ **Tấn công Flash Loan phức tạp / Governance attack:** Không mô phỏng các cuộc tấn công thao túng giá qua flash loan hoặc chiếm quyền biểu quyết quản trị.
- ❌ **Mô phỏng chi tiết MEV / Mempool (PGA, Flashbots Builder):** Không giả lập mempool cạnh tranh priority gas auction ở cấp độ node p2p; rủi ro thực thi đã được phản ánh đầy đủ qua chi phí gas và trượt giá DEX.
- ❌ **Triển khai Mainnet thực tế:** Chỉ triển khai và tương tác trên Ethereum Sepolia Testnet để kiểm thử hợp đồng an toàn, không tốn phí thật.
- ❌ **Lan truyền rủi ro liên giao thức (Cross-protocol Contagion):** Không kết nối mô hình với giao thức bên ngoài như MakerDAO, Compound, Morpho.

---

## 5. Danh mục việc còn thiếu (TODO & Action Items)

| Hạng mục | Trạng thái | Nguồn dữ liệu / Kế hoạch xử lý | Ghi chú |
|---|---|---|---|
| **Giá ETH ban đầu ($P_0$) & Biến động theo giờ ($\sigma_{1h}$)** | `TODO` | Lấy từ tập dữ liệu nến 1h ETHUSDT của Binance Vision tại ngày chốt. | Tạm dùng $P_0 = 2.000$ USD cho testcase phát triển. |
| **Phí gas thực tế** | `TODO` | Thu thập chuỗi gas lịch sử theo ngày của Ethereum. | Tạm dùng mức thử chuẩn $10 và $100 theo nghiên cứu của Qin. |
| **Tham số chuẩn Aave V3** | `TODO` | Đối chiếu tài liệu chính thức Aave V3 Governance và Risk Parameters, ghi ngày tra. | Tham số $LT=0.80$, $Bonus=0.05$ đang dùng mức chuẩn. |
| **Độ lệch chuẩn Lognormal danh mục Borrower** | `TODO` | Tham chiếu từ phân phối dư nợ trong công bố của Chaudhary & Pinna (2022). | Tạm dùng kỳ vọng 5.000 USD. |
| **Hệ số hàm hành vi thích nghi ($a, b, c, d, k$)** | `TODO` | Khảo sát bằng grid search kiểm định tính ổn định. | $h_{min} = a - b \times RA$, $h_{target} = c - d \times RA$. |
| **Smart Contract Sepolia** | `TODO` | Viết hợp đồng Solidity rút gọn, viết script Hardhat/Foundry triển khai lên Sepolia. | Chuẩn bị faucet Sepolia ETH để deploy. |

---

## 6. Ràng buộc & Cảnh báo phương pháp luận

> [!IMPORTANT]
> - Mọi thí nghiệm so sánh giữa **Fixed** và **Adaptive** (E1 vs E2, ..., E11 vs E12) bắt buộc phải chạy trên **cùng một đường giá ETH** và **cùng điều kiện danh mục ban đầu** (seed = 42).
> - Tổng cung USDC của bể thanh khoản **tuyệt đối không bao gồm** giá trị của ETH thế chấp.
> - Ràng buộc an toàn giao thức: $LT \times (1 + Bonus) < 1.0$ phải luôn được thỏa mãn trong mọi bộ tham số quét để tránh nợ xấu ngay tại thời điểm thanh lý.
> - Tài liệu này là cơ sở kỹ thuật chuẩn để đồng bộ toàn bộ mã nguồn mô phỏng Python, Streamlit app và Smart Contract. Mọi thay đổi logic đều phải được cập nhật tại đây trước khi chỉnh sửa mã nguồn.
