# DeFi Liquidation Risk Simulator (DeFi Risk Lab)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tuananh21065-hub/defi-risk/blob/main/defi_risk_lab_colab.ipynb)

> Mô hình hóa và mô phỏng rủi ro thanh lý dây chuyền trong giao thức cho vay phi tập trung (DeFi Lending) — mô hình rút gọn dựa trên cơ chế Aave V3.

---

## 🚀 Chạy trực tiếp trên Google Colab

Bạn có thể chạy toàn bộ dự án, kiểm thử và xem biểu đồ tương tác trực tiếp trên trình duyệt mà không cần cài đặt Python local:

👉 **[Bấm vào đây để mở trên Google Colab](https://colab.research.google.com/github/tuananh21065-hub/defi-risk/blob/main/defi_risk_lab_colab.ipynb)**

File notebook: [`defi_risk_lab_colab.ipynb`](defi_risk_lab_colab.ipynb)

---

## 🎯 Câu hỏi nghiên cứu (Research Questions)

- **RQ1 (Điều kiện thị trường & Chi phí vận hành):** Biến động giá ETH, độ biến động theo giờ, chi phí gas và trượt giá DEX ảnh hưởng như thế nào đến khả năng thanh lý và mức độ an toàn của giao thức?
- **RQ2 (Hành vi thích nghi & Tương tác tác nhân):** Hành vi thích nghi (Adaptive) của Borrower, Lender và Liquidator tương tác với nhau ra sao khi nhiều cú sốc xảy ra đồng thời (giá, thanh khoản, lãi suất, chi phí vận hành), và làm gia tăng hay giảm nhẹ rủi ro hệ thống so với hành vi cố định (Fixed)?

---

## 📁 Cấu trúc dự án

```
defi-risk-simulation/
├── config/
│   ├── parameters.py         # Bảng tham số mô phỏng v0.1 (PAPER, ASSUMPTION, PLACEHOLDER, TODO)
│   └── __init__.py
├── model.py                  # Dataclass Borrower, Health Factor, trạng thái vị thế
├── liquidation.py            # Quy tắc thanh lý, gas accounting, nợ xấu
├── simulation.py             # Vòng lặp mô phỏng 168h, trượt giá DEX phi tuyến
├── scenarios.py              # 6 kịch bản chuẩn hóa S0–S5 và ma trận E1–E12
├── metrics.py                # Tính chỉ số đánh giá (trạng thái borrower, lender & tài chính)
├── app.py                    # Streamlit interactive dashboard (168h timeline, so sánh Fixed vs Adaptive)
├── main.py                   # Entry point: chạy thực nghiệm E1–E12, xuất kết quả CSV
├── defi_risk_lab_colab.ipynb # Google Colab interactive notebook
├── tests/
│   ├── test_benchmark.py     # Bộ kiểm thử chuẩn hóa dùng chung cho Python & Smart Contract
│   ├── test_model.py         # Test tính HF, ràng buộc số dư
│   └── test_liquidation.py   # Test quy tắc thanh lý, gas, bad debt (19 tests)
├── results/                  # CSV kết quả mô phỏng
├── model_spec.md             # Đặc tả toán học, quy tắc tác nhân và cơ chế giao thức
├── scope.md                  # Phạm vi dự án cập nhật (MUST / SHOULD / NOT NOW)
└── examples.md               # Ví dụ tính tay và test vectors chuẩn
```

---

## ⚙️ Cài đặt & Chạy trên máy cục bộ (Local)

### 1. Cài đặt thư viện
```bash
pip install streamlit pandas matplotlib seaborn pytest ipywidgets
```

### 2. Chạy toàn bộ các nhóm kịch bản và xuất CSV
```bash
python -X utf8 main.py
```
Kết quả được lưu tại `results/results.csv`.

### 3. Chạy giao diện Web Simulator (Streamlit)
```bash
python -m streamlit run app.py
```
Mở trình duyệt tại `http://localhost:8501`.

### 4. Chạy Unit Tests & Benchmark Suite
```bash
pytest tests/ -v
```
*(Hiện có 19/19 tests kiểm tra toàn diện logic toán học, trạng thái và bộ kiểm thử chuẩn hóa).*

---

## 📊 Khung kịch bản nghiên cứu (Scenarios S0–S5)

1. **S0 (Cơ sở / Baseline):** Không có cú sốc, giữ nguyên đường giá 168h, gas $10, trượt giá chuẩn.
2. **S1 (Cú sốc giá):** ETH giảm 43% trong 24 bước (từ t=24), hệ số biến động ×10 (Kiểm tra H1, H4).
3. **S2 (Cú sốc thanh khoản):** Lender rút 50% tổng cung trong 12 bước từ t=24 (Kiểm tra H3).
4. **S3 (Cú sốc lãi suất):** Tỷ lệ sử dụng vốn $U$ tăng vọt lên 0.90 trong 12 bước, kích hoạt lãi suất dốc $Slope_2$.
5. **S4 (Cú sốc chi phí vận hành):** Phí gas tăng 100 USD/tx, trượt giá $s \times 5, V \times 0.1$, ETH giảm 25% (Kiểm tra H2, H5).
6. **S5 (Cú sốc kết hợp):** Đồng thời kích hoạt sốc giá S1 (-43%), sốc thanh khoản S2 (rút 50%) và sốc vận hành S4 (gas $100, trượt giá tăng) (Kiểm tra H5, H6).

Ma trận thực nghiệm gồm **12 thực nghiệm chính (E1–E12)** đối chiếu trực tiếp chiến lược **Cố định (Fixed)** và **Thích nghi (Adaptive)** trên cùng seed (42) và cùng đường giá.

---

## 🔢 Tham số mô hình cốt lõi (v0.1)

| Tham số | Ký hiệu | Giá trị chuẩn | Các mức quét thực nghiệm | Nhãn & Nguồn |
|---|---|---|---|---|
| Liquidation Threshold | $LT$ | 0.80 | 0.70; 0.75; 0.80; 0.85 | `PLACEHOLDER` (Qin ví dụ; Aave V3) |
| Liquidation Bonus | $Bonus$ | 0.05 (5%) | 0.05; 0.08; 0.10; 0.15 | `PAPER` (Qin: Aave 5-15%, Compound 8%) |
| Close Factor | $CF$ | 0.50 (50%) | Cố định 0.50 | `PAPER` (Chaudhary & Pinna; Qin) |
| Lãi suất Kink | $U_{opt}$ | 0.80 (80%) | 0.45; 0.80; 0.90 | `PLACEHOLDER` (Base 0%, Slope1 4%, Slope2 75%) |
| Thời gian mô phỏng | $T$ | 168 bước | 168 giờ (7 ngày) | `ASSUMPTION` (ABM cần chân trời dài) |
| Số lần Monte Carlo | $N$ | 100 / 1.000 | 100 (dev) / 1.000 (chính thức) | `PAPER` (Chaudhary & Pinna) |
| Phí Gas | $gas$ | $10 / $100 | $10 (thấp) vs $100 (nghẽn mạng) | `PAPER` (Qin) |
| Hàm trượt giá DEX | $\sigma(x)$ | $\gamma + s(x/V)^\omega$ | $\gamma=0.003, s=1.0, V=10^9$ USD | `PAPER` (Chaudhary & Pinna) |

---

## ⚠️ Giả định và giới hạn nghiên cứu

> **Lưu ý:** Đây là mô hình mô phỏng nghiên cứu học thuật, rút gọn và trừu tượng hóa, không phản ánh toàn bộ quy tắc on-chain của Aave mainnet.

- **Giá trị tài sản:** 1 USDC = 1 USD (bỏ qua rủi ro stablecoin depeg).
- **Lãi suất:** Nợ tĩnh trong phiên mô phỏng (không có lãi suất động theo thời gian dài).
- **Price Impact:** Áp dụng mô hình tuyến tính $\Delta P = -\frac{ETH_{sold} \times P}{MarketDepth}$, không phải mô hình Curve hay Uniswap v3 AMM hoàn chỉnh.
- **Slippage nội bộ:** Liquidator bán ETH theo giá tại vòng hiện tại, tác động trượt giá lan sang vòng tiếp theo.

---

## 📚 Tài liệu tham khảo

- [Aave V3 Technical Whitepaper & Documentation](https://docs.aave.com/)
- [Aave Risk Framework & Parameters](https://docs.aave.com/risk/)
- Gauntlet Network & Chaos Labs: DeFi Market Risk Simulation Methodologies
- Euler Finance: Understanding Liquidation Mechanics and Bad Debt
