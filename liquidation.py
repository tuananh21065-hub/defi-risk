"""
liquidation.py — Quy tắc thanh lý rút gọn

Liquidator quyết định thanh lý khi:
1. HF < 1 (đủ điều kiện)
2. Net profit > 0 sau gas (gross_profit - gas_cost > 0)
3. Liquidator có đủ vốn (kể cả gas)

Thanh lý: Trả tối đa CLOSE_FACTOR * debt_usdc;
          Nhận ETH collateral tương đương + LIQUIDATION_BONUS.

Gas accounting:
  - Gas cost được trừ trực tiếp từ capital_usdc của liquidator.
  - capital_usdc tăng khi nhận ETH (bán tại eth_price sau price impact).
  - Nếu collateral không đủ trả bonus → ETH thực nhận bị giới hạn
    → actual_repay điều chỉnh lại tương ứng → ghi nhận bad debt nếu collateral = 0.

Lợi nhuận liquidator:
  - gross_profit = eth_received * sell_price - actual_repay
    Trong đó sell_price = eth_price tại thời điểm thanh lý.
    Trượt giá (slippage) do bán ETH được xử lý ở tầng simulation (price_feedback),
    không xử lý trong hàm này, để tách biệt rõ hai cơ chế.
  - net_profit = gross_profit - gas_cost_usd

Trạng thái borrower sau thanh lý:
  - Nếu collateral cạn và còn nợ → đánh dấu _defaulted=True → ghi realized_bad_debt
  - Borrower DEFAULTED ≠ REPAID (debt_usdc đều = 0 nhưng ngữ nghĩa khác nhau)
"""
from model import Borrower, CLOSE_FACTOR, LIQUIDATION_BONUS

DEFAULT_GAS_COST_USD = 5.0


class Liquidator:
    def __init__(self, capital_usdc: float, gas_cost_usd: float = DEFAULT_GAS_COST_USD):
        self.capital_usdc = capital_usdc
        self.gas_cost_usd = gas_cost_usd
        self.total_profit = 0.0
        self.liquidation_count = 0      # số lần thực hiện thành công
        self.failed_no_profit = 0       # thất bại vì không có lợi sau gas
        self.failed_no_capital = 0      # thất bại vì không đủ vốn
        self.eth_received_total = 0.0   # tổng ETH nhận được (trước khi bán)

    @property
    def failed_count(self) -> int:
        return self.failed_no_profit + self.failed_no_capital

    def attempt_liquidation(self, borrower: Borrower, eth_price: float,
                            sell_price: float | None = None) -> dict:
        """
        Thực hiện thanh lý nếu có lợi và đủ vốn.

        Args:
            borrower: vị thế cần thanh lý
            eth_price: giá ETH hiện tại (dùng để tính HF và ETH nhận)
            sell_price: giá bán ETH thực tế (mặc định = eth_price;
                        truyền vào giá trị thấp hơn để mô phỏng slippage cục bộ)

        Returns dict:
          success, debt_repaid, eth_received, sell_price_used,
          gross_profit_usd, net_profit_usd, gas_cost_usd,
          bad_debt_created, reason
        """
        if sell_price is None:
            sell_price = eth_price  # mặc định: bán ngay tại giá hiện tại

        result = {
            "borrower_id": borrower.borrower_id,
            "success": False,
            "debt_repaid": 0.0,
            "eth_received": 0.0,
            "sell_price_used": sell_price,
            "gross_profit_usd": 0.0,
            "net_profit_usd": 0.0,
            "gas_cost_usd": self.gas_cost_usd,
            "bad_debt_created": 0.0,
            "reason": "",
        }

        if not borrower.is_undercollateralized(eth_price):
            result["reason"] = "HF >= 1, không đủ điều kiện"
            return result

        # --- Tính lượng nợ có thể trả ---
        max_repay = borrower.debt_usdc * CLOSE_FACTOR
        actual_repay = min(max_repay, self.capital_usdc)

        # Cần đủ vốn để trả nợ VÀ trả gas
        if actual_repay <= 0 or self.capital_usdc < self.gas_cost_usd:
            result["reason"] = "Không đủ vốn (kể cả gas)"
            self.failed_no_capital += 1
            return result

        # --- Tính ETH liquidator sẽ nhận (lý thuyết) ---
        eth_to_receive_ideal = (actual_repay * (1 + LIQUIDATION_BONUS)) / eth_price

        # Giới hạn không nhận quá collateral hiện có
        eth_to_receive = min(eth_to_receive_ideal, borrower.collateral_eth)

        # Điều chỉnh actual_repay nếu collateral bị giới hạn
        if eth_to_receive < eth_to_receive_ideal:
            actual_repay = eth_to_receive * eth_price / (1 + LIQUIDATION_BONUS)

        # --- Tính lợi nhuận ---
        # gross_profit tính theo sell_price (có thể có slippage từ caller)
        eth_value_at_sell = eth_to_receive * sell_price
        gross_profit = eth_value_at_sell - actual_repay
        net_profit = gross_profit - self.gas_cost_usd

        if net_profit <= 0:
            result["reason"] = f"Net profit {net_profit:.2f} USD <= 0 sau gas ${self.gas_cost_usd}"
            self.failed_no_profit += 1
            return result

        if self.capital_usdc < actual_repay + self.gas_cost_usd:
            result["reason"] = "Không đủ vốn sau tính gas (kiểm tra cuối)"
            self.failed_no_capital += 1
            return result

        # --- Thực hiện thanh lý ---
        # Trừ nợ trả + gas, cộng lại tiền bán ETH (tại sell_price)
        self.capital_usdc -= actual_repay
        self.capital_usdc -= self.gas_cost_usd
        self.capital_usdc += eth_to_receive * sell_price
        self.total_profit += net_profit
        self.liquidation_count += 1
        self.eth_received_total += eth_to_receive

        # --- Cập nhật trạng thái Borrower ---
        borrower.debt_usdc = max(0.0, borrower.debt_usdc - actual_repay)
        borrower.collateral_eth = max(0.0, borrower.collateral_eth - eth_to_receive)
        borrower.times_liquidated += 1

        # --- Ghi nhận bad debt khi collateral cạn kiệt ---
        # Phân biệt rõ DEFAULTED vs REPAID
        bad_debt = 0.0
        if borrower.collateral_eth <= 0 and borrower.debt_usdc > 0:
            bad_debt = borrower.debt_usdc
            borrower.realized_bad_debt += bad_debt
            borrower.debt_usdc = 0.0
            borrower._defaulted = True   # đánh dấu vỡ nợ — KHÁC với REPAID

        result.update({
            "success": True,
            "debt_repaid": round(actual_repay, 4),
            "eth_received": round(eth_to_receive, 6),
            "sell_price_used": round(sell_price, 2),
            "gross_profit_usd": round(gross_profit, 4),
            "net_profit_usd": round(net_profit, 4),
            "bad_debt_created": round(bad_debt, 4),
            "reason": "OK",
        })
        return result
