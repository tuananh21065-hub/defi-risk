# DeFi Market Risk Monitor

> Mô phỏng rủi ro thanh lý dây chuyền trong giao thức cho vay phi tập trung (DeFi Lending) — mô hình rút gọn tương tự Aave V3.

## 🎯 Câu hỏi nghiên cứu

Khi ETH giảm giá, chi phí thanh lý và thanh khoản thị trường ảnh hưởng ra sao đến:
- Số vị thế đủ điều kiện thanh lý (HF < 1)
- Số vị thế được thanh lý thực tế
- Khoản thiếu hụt tài sản bảo đảm (shortfall)
- Khi nào có nguy cơ hình thành vòng phản hồi thanh lý?

---

## 📁 Cấu trúc dự án

```
defi-risk-lab/
├── model.py           # Borrower dataclass, Health Factor
├── liquidation.py     # Quy tắc thanh lý (Liquidator)
├── simulation.py      # Vòng mô phỏng, sốc giá, ghi log
├── scenarios.py       # Tham số thí nghiệm, seed cố định
├── metrics.py         # Tính chỉ số: HF < 1, shortfall, tỷ lệ thanh lý
├── app.py             # Streamlit dashboard
├── main.py            # Entry point: chạy simulation, xuất CSV
├── tests/
│   ├── test_model.py
│   └── test_liquidation.py
├── results/           # CSV kết quả
├── model_spec.md      # Công thức và định nghĩa
├── scope.md           # Phạm vi MUST/SHOULD/NOT NOW
└── examples.md        # 3 ví dụ tính tay
```

---

## ⚙️ Cài đặt

```bash
pip install streamlit pandas pytest
```

> Python 3.8+ được khuyến nghị. Không cần thư viện đặc biệt ngoài standard library cho `main.py`.

---

## 🚀 Chạy dự án

### Chạy toàn bộ kịch bản và xuất CSV
```bash
cd defi-risk-lab
python main.py
```
Kết quả lưu tại `results/results.csv`.

### Chạy Streamlit Dashboard
```bash
streamlit run app.py
```
Mở trình duyệt tại `http://localhost:8501`.

### Chạy Unit Tests
```bash
pytest tests/ -v
```

---

## 📊 Các kịch bản thí nghiệm

| Nhóm | Kịch bản | Sốc giá ETH | Gas (USD) |
|---|---|---|---|
| Price Shock | baseline | 0% | $5 |
| Price Shock | shock_10 | -10% | $5 |
| Price Shock | shock_20 | -20% | $5 |
| Price Shock | shock_30 | -30% | $5 |
| Gas Sensitivity | gas_1 | -20% | $1 |
| Gas Sensitivity | gas_5 | -20% | $5 |
| Gas Sensitivity | gas_20 | -20% | $20 |
| Gas Sensitivity | gas_50 | -20% | $50 |

---

## 🔢 Tham số mô hình

| Tham số | Giá trị | Mô tả |
|---|---|---|
| Liquidation Threshold | 0.825 | Ngưỡng thanh lý |
| LTV tối đa | 0.80 | Loan-to-Value tại thời điểm vay |
| Close Factor | 0.50 | Tối đa 50% nợ/lần thanh lý |
| Liquidation Bonus | 0.05 | 5% thưởng ETH cho liquidator |
| Seed | 42 | Seed cố định để tái lập |
| Borrowers | 50 | Số người vay mặc định |
| ETH giá ban đầu | $2,000 | Giá ETH trước sốc |
| Vốn Liquidator | $500,000 USDC | Vốn tổng của liquidator |

---

## ⚠️ Giả định và giới hạn

> **Mô hình này là công cụ nghiên cứu giáo dục, không phải công cụ đánh giá rủi ro production.**

- 1 USDC = 1 USD (không có depeg risk)
- Giá ETH là ngoại sinh, không có price impact từ AMM
- Không có lãi suất động (static debt)
- Không có độ trễ oracle
- Liquidator bán ETH nhận được ngay tại giá hiện tại (atomic)
- Tham số lấy cảm hứng từ Aave V3 nhưng được đơn giản hóa

---

## 📚 Nguồn tham khảo

- [Aave V3 Documentation](https://docs.aave.com/)
- [Aave V3 Risk Parameters](https://docs.aave.com/risk/asset-risk/risk-parameters)
- Gauntlet Network — DeFi Risk Research
- Chaos Labs — Protocol Risk Simulations
- [Euler Finance — Understanding Liquidations](https://docs.euler.finance/)
