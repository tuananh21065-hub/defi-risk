# Phạm vi dự án — DeFi Risk Lab

## Câu hỏi nghiên cứu chính

> Khi ETH giảm giá, chi phí thanh lý và thanh khoản thị trường ảnh hưởng ra sao đến số vị thế đủ điều kiện thanh lý, số vị thế được thanh lý thực tế và khoản thiếu hụt tài sản bảo đảm (shortfall)? Khi nào có nguy cơ hình thành vòng phản hồi thanh lý?

---

## MUST — Phải có

- [x] Mô hình `Borrower` với Health Factor
- [x] `Liquidator` với logic thanh lý: HF < 1, profit > gas, đủ vốn
- [x] `run_scenario()`: sốc giá, nhiều round thanh lý, ghi log
- [x] Chỉ số: `n_undercollateralized`, `n_liquidated`, `shortfall`, `liquidation_rate`
- [x] 4 kịch bản sốc giá: 0%, -10%, -20%, -30%
- [x] 4 kịch bản nhạy cảm gas: $1, $5, $20, $50
- [x] Seed cố định (42) để tái lập kết quả
- [x] Xuất CSV kết quả
- [x] Unit tests: HF, liquidation rules, không có số dư âm
- [x] Streamlit dashboard tối giản
- [x] README với hướng dẫn cài đặt và chạy

---

## SHOULD — Nên có (giai đoạn 2)

- [ ] **Price feedback loop**: Khi ETH bị bán ra hàng loạt → giá giảm thêm → kích hoạt thêm thanh lý (`price_feedback=True`, `feedback_coefficient`)
- [ ] **Nhiều liquidator**: Cạnh tranh vốn, ưu tiên vị thế lớn nhất
- [ ] **Biểu đồ trực quan**: Phân phối HF, timeline thanh lý, shortfall heatmap
- [ ] **Phân tích độ nhạy**: Grid search trên `price_shock × gas_cost`
- [ ] **Lãi suất đơn giản**: Dư nợ tăng theo thời gian

---

## NOT NOW — Ngoài phạm vi hiện tại

- ❌ Dữ liệu on-chain thực (Aave subgraph, The Graph)
- ❌ Nhiều loại tài sản thế chấp (WBTC, stETH, v.v.)
- ❌ Flash loan mechanics
- ❌ MEV / front-running simulation
- ❌ Governance token dynamics
- ❌ Cross-protocol contagion (Compound, MakerDAO)
- ❌ Mô hình AMM thực (Uniswap V3 price impact)
- ❌ Smart contract integration / on-chain execution

---

## Giới hạn và cảnh báo mô hình

> [!WARNING]
> Mô hình này là **công cụ nghiên cứu giáo dục**, không phải công cụ đánh giá rủi ro production. Các tham số được đơn giản hóa và không phản ánh Aave mainnet thực tế.

- Giá ETH là ngoại sinh, không có price impact từ AMM
- Không có độ trễ oracle (oracle latency)
- Bỏ qua gas dynamics thực tế (EIP-1559, congestion)
- Không có bad debt socialization mechanism
