"""
main.py -- Entry point: chay tat ca kich ban va xuat ket qua

Chay: python main.py
Ket qua: in bang ra console + luu results/results.csv
"""
import csv
import os
import sys

# Fix Unicode output on Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from simulation import run_scenario
from scenarios import (
    generate_borrowers,
    INITIAL_ETH_PRICE,
    LIQUIDATOR_CAPITAL,
    PRICE_SHOCK_SCENARIOS,
    GAS_SENSITIVITY_SCENARIOS,
)

os.makedirs("results", exist_ok=True)

def print_metrics(label: str, m: dict):
    print(f"\n  [{label}]")
    print(f"    ETH Price: ${m['eth_price']:.0f}")
    print(f"    Borrowers: {m['n_borrowers']} | Undercollateralized: {m['n_undercollateralized']} | Liquidated: {m['n_liquidated']}")
    print(f"    Total Collateral: ${m['total_collateral_value_usd']:,.0f} | Total Debt: ${m['total_debt_usdc']:,.0f}")
    print(f"    Total Shortfall: ${m['total_shortfall']:,.2f} | Liquidation Rate: {m['liquidation_rate_pct']:.1f}%")


def run_all_scenarios():
    borrowers = generate_borrowers(n=50, eth_price=INITIAL_ETH_PRICE)
    all_results = []

    all_scenarios = [
        ("price_shock", s) for s in PRICE_SHOCK_SCENARIOS
    ] + [
        ("gas_sensitivity", s) for s in GAS_SENSITIVITY_SCENARIOS
    ]

    for group, s in all_scenarios:
        print(f"\n{'='*60}")
        print(f"Kịch bản: {s['name']} ({group})")
        print(f"  Sốc giá: {s['price_shock_pct']*100:.0f}% | Gas: ${s['gas_cost_usd']}")

        result = run_scenario(
            borrowers=borrowers,
            initial_eth_price=INITIAL_ETH_PRICE,
            price_shock_pct=s["price_shock_pct"],
            liquidator_capital=LIQUIDATOR_CAPITAL,
            gas_cost_usd=s["gas_cost_usd"],
        )
        print_metrics("Trước thanh lý", result["before"])
        print_metrics("Sau thanh lý", result["after"])

        ls = result["liquidator_stats"]
        print(f"\n  Liquidator: {ls['liquidation_count']} lần thành công | {ls['failed_count']} lần thất bại | Lợi nhuận: ${ls['total_profit']:,.2f}")

        all_results.append({
            "group": group,
            "scenario": s["name"],
            "price_shock_pct": s["price_shock_pct"],
            "gas_cost_usd": s["gas_cost_usd"],
            **{f"before_{k}": v for k, v in result["before"].items()},
            **{f"after_{k}": v for k, v in result["after"].items()},
            "liquidation_count": ls["liquidation_count"],
            "failed_count": ls["failed_count"],
            "liquidator_profit": ls["total_profit"],
        })

    # Lưu CSV
    csv_path = "results/results.csv"
    if all_results:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
    print(f"\n✓ Kết quả đã lưu tại {csv_path}")


if __name__ == "__main__":
    run_all_scenarios()
