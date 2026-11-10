# DeFi Liquidation Risk Simulator (DeFi Risk Lab)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tuananh21065-hub/defi-risk/blob/main/defi_risk_lab_colab.ipynb)

> Mô hình hóa và mô phỏng rủi ro thanh lý dây chuyền trong giao thức cho vay phi tập trung (DeFi Lending) — mô hình rút gọn dựa trên cơ chế Aave V3.

---

## 🚀 Chạy trực tiếp trên Google Colab

Bạn có thể chạy toàn bộ dự án, kiểm thử và xem biểu đồ tương tác trực tiếp trên trình duyệt mà không cần cài đặt Python local:

👉 **[Bấm vào đây để mở trên Google Colab](https://colab.research.google.com/github/tuananh21065-hub/defi-risk/blob/main/defi_risk_lab_colab.ipynb)**

File notebook: [`defi_risk_lab_colab.ipynb`](defi_risk_lab_colab.ipynb)

---

## 🎯 Câu hỏi nghiên cứu

Khi giá ETH biến động mạnh, chi phí thực thi (gas), năng lực vốn của liquidator và thanh khoản thị trường (market depth) ảnh hưởng ra sao đến:
- Số vị thế đủ điều kiện thanh lý ($HF < 1$)
- Số vị thế thực sự được thanh lý (`Touched`)
- Phân biệt giữa người vay trả hết nợ (`Repaid`), vỡ nợ (`Defaulted`) và còn nguy hiểm (`Still Unsafe`)
- Thâm hụt dự kiến (`Projected Deficit`) so với nợ xấu thực tế (`Realized Bad Debt`)
- Điều kiện hình thành vòng phản hồi thanh lý (Liquidation Spiral / Cascade)

---

## 📁 Cấu trúc dự án

```
defi-risk-lab/
├── model.py                  # Borrower dataclass, Health Factor, phân loại Repaid / Defaulted
├── liquidation.py            # Quy tắc thanh lý, gas accounting, ghi nhận Realized Bad Debt
├── simulation.py             # Vòng mô phỏng, sốc giá, Price Feedback & Market Depth
├── scenarios.py              # Tham số 5 nhóm kịch bản thực nghiệm
├── metrics.py                # Tính chỉ số đánh giá (trạng thái borrower & tài chính)
├── app.py                    # Streamlit interactive simulator
├── main.py                   # Entry point: chạy thực nghiệm, lưu kết quả ra CSV
├── defi_risk_lab_colab.ipynb # Google Colab interactive notebook
├── tests/
│   ├── test_model.py         # Test tính HF, ràng buộc số dư
│   └── test_liquidation.py   # Test quy tắc thanh lý, gas, bad debt (17 tests)
├── results/                  # CSV kết quả (results.csv)
├── model_spec.md             # Công thức, định nghĩa và giả định
├── scope.md                  # Phạm vi MUST / SHOULD / NOT NOW
└── examples.md               # 3 ví dụ tính tay
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

### 4. Chạy Unit Tests
```bash
pytest tests/ -v
```
*(Hiện có 17/17 tests kiểm tra toàn diện logic toán học và trạng thái).*

---

## 📊 Các nhóm kịch bản thí nghiệm

1. **A. Scenario Analysis (Sốc giá ETH):** Khảo sát các mức sốc từ 0% đến -40% giá ETH.
2. **B. Gas Sensitivity (Độ nhạy chi phí Gas):** Khảo sát gas từ $1 đến $100 khi sốc -20%.
3. **C. Cascade Analysis (Vòng phản hồi & Thanh khoản thị trường):** Bật `price_feedback` và thay đổi `market_depth` từ $500K đến $50M.
4. **D. Capital Sensitivity (Năng lực vốn Liquidator):** Thay đổi vốn từ $50K đến $1M USDC.
5. **E. Multi-seed Robustness Check:** Chạy qua 5 seed khác nhau (`42, 123, 7, 99, 2024`) để kiểm chứng tính ổn định của các kết luận.

---

## 🔢 Tham số mô hình cốt lõi

| Tham số | Ký hiệu | Giá trị | Ý nghĩa |
|---|---|---|---|
| Liquidation Threshold | $LT$ | 0.825 | Ngưỡng thanh lý (HF < 1) |
| Max Loan-to-Value | $LTV$ | 0.80 | Tỷ lệ nợ tối đa khi mở vị thế |
| Close Factor | $CF$ | 0.50 | Tối đa 50% nợ được thanh lý mỗi lần |
| Liquidation Bonus | $B$ | 0.05 | Thưởng 5% ETH cho liquidator |
| Giá ETH ban đầu | $P_0$ | $2,000 | Mốc định giá chuẩn |
| Vốn Liquidator cơ sở | $C_0$ | $500,000 | Vốn USDC sẵn có của Liquidator |

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
