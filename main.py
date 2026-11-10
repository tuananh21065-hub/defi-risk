"""
main.py — Entry point: chạy tất cả kịch bản và xuất kết quả

Chạy: python -X utf8 main.py
Kết quả: in bảng ra console + lưu results/results.csv
"""
import sys
import csv
import os

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

os.makedirs("results", exist_ok=True)

from simulation import run_scenario
from scenarios import (
    generate_borrowers,
    INITIAL_ETH_PRICE,
    LIQUIDATOR_CAPITAL,
    PRICE_SHOCK_SCENARIOS,
    GAS_SENSITIVITY_SCENARIOS,
    CASCADE_SCENARIOS,
)


def print_metrics(label: str, m: dict):
    print(f"\n  [{label}]")
    print(f"    ETH Price: ${m['eth_price']:,.0f}")
    print(f"    Borrowers: {m['n_borrowers']} | "
          f"HF<1: {m['n_undercollateralized']} | "
          f"Touched: {m['n_touched']} | "
          f"Fully Repaid: {m['n_fully_repaid']} | "
          f"Still Unsafe: {m['n_still_unsafe']}")
    print(f"    Collateral Value: ${m['total_collateral_value_usd']:,.0f} | "
          f"Remaining Debt: ${m['total_remaining_debt']:,.0f}")
    print(f"    Realized Bad Debt: ${m['total_realized_bad_debt']:,.2f} | "
          f"Projected Deficit: ${m['total_projected_deficit']:,.2f}")
    print(f"    Touched Rate: {m['touched_rate_pct']:.1f}% | "
          f"Fully Repaid Rate: {m['fully_repaid_rate_pct']:.1f}%")


def run_group(group_name: str, scenarios: list, borrowers: list, all_results: list):
    for s in scenarios:
        feedback = s.get("price_feedback", False)
        depth = s.get("market_depth_usd") or 10_000_000.0

        print(f"\n{'='*65}")
        print(f"Kịch bản: {s['name']} [{group_name}]")
        print(f"  Sốc giá: {s['price_shock_pct']*100:.0f}% | "
              f"Gas: ${s['gas_cost_usd']} | "
              f"Feedback: {feedback}"
              + (f" | Market Depth: ${depth:,.0f}" if feedback else ""))

        result = run_scenario(
            borrowers=borrowers,
            initial_eth_price=INITIAL_ETH_PRICE,
            price_shock_pct=s["price_shock_pct"],
            liquidator_capital=LIQUIDATOR_CAPITAL,
            gas_cost_usd=s["gas_cost_usd"],
            price_feedback=feedback,
            market_depth_usd=depth,
        )

        print_metrics("Trước thanh lý", result["before"])
        print_metrics("Sau thanh lý", result["after"])

        ls = result["liquidator_stats"]
        print(f"\n  Liquidator: {ls['liquidation_count']} lần TL thành công | "
              f"Thất bại (gas): {ls['failed_no_profit']} | "
              f"Thất bại (vốn): {ls['failed_no_capital']} | "
              f"Lợi nhuận: ${ls['total_profit']:,.2f}")

        if feedback:
            print(f"  Giá ETH: {result['price_history']}")

        all_results.append({
            "group": group_name,
            "scenario": s["name"],
            "price_shock_pct": s["price_shock_pct"],
            "gas_cost_usd": s["gas_cost_usd"],
            "price_feedback": feedback,
            "market_depth_usd": depth if feedback else "",
            **{f"before_{k}": v for k, v in result["before"].items()},
            **{f"after_{k}": v for k, v in result["after"].items()},
            "liquidation_count": ls["liquidation_count"],
            "failed_no_profit": ls["failed_no_profit"],
            "failed_no_capital": ls["failed_no_capital"],
            "liquidator_profit": ls["total_profit"],
            "final_eth_price": result["params"]["final_eth_price"],
        })


def main():
    borrowers = generate_borrowers(n=50, eth_price=INITIAL_ETH_PRICE)
    all_results = []

    print("\n📊 A. SCENARIO ANALYSIS — Sốc giá ETH")
    run_group("price_shock", PRICE_SHOCK_SCENARIOS, borrowers, all_results)

    print("\n\n📊 B. GAS SENSITIVITY — Gas thay đổi, sốc -20%")
    run_group("gas_sensitivity", GAS_SENSITIVITY_SCENARIOS, borrowers, all_results)

    print("\n\n📊 C. CASCADE ANALYSIS — Price feedback & Market Depth")
    run_group("cascade", CASCADE_SCENARIOS, borrowers, all_results)

    # Lưu CSV
    csv_path = "results/results.csv"
    if all_results:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)
    print(f"\n\n✓ Kết quả đã lưu tại {csv_path}")


if __name__ == "__main__":
    main()
