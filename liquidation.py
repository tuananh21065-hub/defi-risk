"""
liquidation.py — Quy tắc thanh lý rút gọn

Liquidator quyết định thanh lý khi:
1. HF < 1 (đủ điều kiện)
2. Lợi nhuận dự kiến > chi phí gas
3. Liquidator có đủ vốn

Thanh lý: Trả tối đa CLOSE_FACTOR * debt; nhận ETH collateral + LIQUIDATION_BONUS
"""
from model import Borrower, CLOSE_FACTOR, LIQUIDATION_BONUS

DEFAULT_GAS_COST_USD = 5.0      # Chi phí gas mỗi lần thanh lý (giả định)

class Liquidator:
    def __init__(self, capital_usdc: float, gas_cost_usd: float = DEFAULT_GAS_COST_USD):
        self.capital_usdc = capital_usdc
        self.gas_cost_usd = gas_cost_usd
        self.total_profit = 0.0
        self.liquidation_count = 0
        self.failed_count = 0  # thiếu vốn hoặc không lợi

    def attempt_liquidation(self, borrower: Borrower, eth_price: float) -> dict:
        """
        Thực hiện thanh lý nếu có lợi và đủ vốn.
        Trả về dict kết quả: success, debt_repaid, eth_received, profit, reason
        """
        result = {
            "borrower_id": borrower.borrower_id,
            "success": False,
            "debt_repaid": 0.0,
            "eth_received": 0.0,
            "profit_usd": 0.0,
            "reason": "",
        }

        if not borrower.is_undercollateralized(eth_price):
            result["reason"] = "HF >= 1, không đủ điều kiện"
            return result

        # Tính toán tối đa có thể trả nợ
        max_repay = borrower.debt_usdc * CLOSE_FACTOR
        actual_repay = min(max_repay, self.capital_usdc)

        # ETH nhận được (giá trị USDC đã trả + bonus, quy về ETH)
        eth_to_receive = (actual_repay * (1 + LIQUIDATION_BONUS)) / eth_price

        # Giới hạn không nhận quá collateral hiện có
        eth_to_receive = min(eth_to_receive, borrower.collateral_eth)

        # Giá trị ETH nhận được
        eth_value_usd = eth_to_receive * eth_price
        gross_profit = eth_value_usd - actual_repay
        net_profit = gross_profit - self.gas_cost_usd

        if net_profit <= 0:
            result["reason"] = f"Net profit {net_profit:.2f} USD <= 0 sau gas"
            self.failed_count += 1
            return result

        if self.capital_usdc < actual_repay:
            result["reason"] = "Không đủ vốn"
            self.failed_count += 1
            return result

        # Thực hiện thanh lý
        self.capital_usdc -= actual_repay
        self.capital_usdc += eth_to_receive * eth_price  # bán ETH ngay (giả định)
        self.total_profit += net_profit
        self.liquidation_count += 1

        # Cập nhật trạng thái Borrower
        borrower.debt_usdc -= actual_repay
        borrower.collateral_eth -= eth_to_receive

        # Tính shortfall
        remaining_value = borrower.collateral_eth * eth_price * (1 / (1 + LIQUIDATION_BONUS))
        if borrower.debt_usdc > 0 and remaining_value < borrower.debt_usdc:
            borrower.shortfall = borrower.debt_usdc - remaining_value

        if borrower.debt_usdc <= 0:
            borrower.is_liquidated = True

        result.update({
            "success": True,
            "debt_repaid": actual_repay,
            "eth_received": eth_to_receive,
            "profit_usd": net_profit,
            "reason": "OK",
        })
        return result
