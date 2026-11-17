# -*- coding: utf-8 -*-
"""
main.py — Entry point: chạy 12 thực nghiệm E1–E12 theo thiết kế doc nghiên cứu

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
    generate_lenders,
    make_pool,
    get_scenario_params,
    EXPERIMENTS,
    ROBUSTNESS_SEEDS,
    ROBUSTNESS_SCENARIO,
    ROBUSTNESS_STRATEGY,
    INITIAL_ETH_PRICE,
    LIQUIDATOR_CAPITAL,
    PRICE_SHOCK_SCENARIOS,
    GAS_SENSITIVITY_SCENARIOS,
    CASCADE_SCENARIOS,
    CAPITAL_SENSITIVITY_SCENARIOS,
)


def print_metrics(label: str, m: dict):
    print(f"\n  [{label}]")
    print(f"    ETH Price: ${m['eth_price']:,.2f}")
    print(f"    Borrowers: {m['n_borrowers']} | "
          f"HF<1: {m['n_undercollateralized']} | "
          f"Touched: {m['n_touched']} | "
          f"Repaid: {m['n_repaid']} | "
          f"Defaulted: {m['n_defaulted']} | "
          f"Still Unsafe: {m['n_still_unsafe']}")
    print(f"    Collateral: ${m['total_collateral_value_usd']:,.0f} | "
          f"Debt: ${m['total_remaining_debt']:,.0f}")
    print(f"    Realized Bad Debt: ${m['total_realized_bad_debt']:,.2f} | "
          f"Projected Deficit: ${m['total_projected_deficit']:,.2f}")
    if m.get("utilization") is not None:
        print(f"    Utilization: {m['utilization']*100:.2f}% | "
              f"Available Liquidity: ${m['available_liquidity_usdc']:,.0f} | "
              f"Borrow Rate: {m['borrow_rate_annual']:.2f}%/yr | "
              f"Supply Rate: {m['supply_rate_annual']:.2f}%/yr")


def run_experiment(exp_id: str, scenario: str, strategy: str,
                   borrowers, lenders, pool,
                   all_results: list):
    """Chạy một thực nghiệm E1–E12."""
    params = get_scenario_params(scenario)
    print(f"\n{'='*70}")
    print(f"Thực nghiệm: {exp_id} | Kịch bản: {scenario} | Chiến lược: {strategy}")
    print(f"  Sốc giá: {params['price_shock_pct']*100:.0f}% | "
          f"Gas: ${params['gas_cost_usd']} | "
          f"Capital: ${params['liquidator_capital']:,.0f} | "
          f"Feedback: {params['price_feedback']} | "
          f"Liq.shock: {params['liquidity_shock_pct']*100:.0f}% | "
          f"Demand surge: ${params['demand_surge_usdc']:,.0f}")

    result = run_scenario(
        borrowers           = borrowers,
        initial_eth_price   = params["initial_eth_price"],
        price_shock_pct     = params["price_shock_pct"],
        liquidator_capital  = params["liquidator_capital"],
        gas_cost_usd        = params["gas_cost_usd"],
        lenders             = lenders,
        pool                = pool,
        liquidity_shock_pct = params["liquidity_shock_pct"],
        demand_surge_usdc   = params["demand_surge_usdc"],
        price_feedback      = params["price_feedback"],
        market_depth_usd    = params["market_depth_usd"],
        strategy            = strategy,
    )

    print_metrics("Trước thanh lý", result["before"])
    print_metrics("Sau thanh lý",   result["after"])

    ls = result["liquidator_stats"]
    print(f"\n  Liquidator: {ls['liquidation_count']} lần TL thành công | "
          f"Thất bại (gas): {ls['failed_no_profit']} | "
          f"Thất bại (vốn): {ls['failed_no_capital']} | "
          f"Lợi nhuận: ${ls['total_profit']:,.2f} | "
          f"Vốn còn lại: ${ls['final_capital_usdc']:,.2f}")
    print(f"  Rounds: {result['rounds_run']} | "
          f"Liq.Coverage: {result['liquidation_coverage']*100:.1f}% | "
          f"Withdrawal Fulfillment: {result.get('withdrawal_fulfillment')}")

    if params["price_feedback"] and len(result["price_history"]) > 1:
        print(f"  Price history: {result['price_history']}")

    row = {
        "experiment_id":    exp_id,
        "scenario":         scenario,
        "strategy":         strategy,
        "price_shock_pct":  params["price_shock_pct"],
        "gas_cost_usd":     params["gas_cost_usd"],
        "liquidator_capital": params["liquidator_capital"],
        "liquidity_shock_pct": params["liquidity_shock_pct"],
        "demand_surge_usdc": params["demand_surge_usdc"],
        "price_feedback":   params["price_feedback"],
        "market_depth_usd": params["market_depth_usd"] if params["price_feedback"] else "",
        "rounds_run":       result["rounds_run"],
        "liquidation_coverage": result["liquidation_coverage"],
        "withdrawal_fulfillment": result.get("withdrawal_fulfillment", ""),
        **{f"before_{k}": v for k, v in result["before"].items()},
        **{f"after_{k}": v  for k, v in result["after"].items()},
        "liquidation_count":        ls["liquidation_count"],
        "failed_no_profit":         ls["failed_no_profit"],
        "failed_no_capital":        ls["failed_no_capital"],
        "liquidator_profit":        ls["total_profit"],
        "liquidator_capital_final": ls["final_capital_usdc"],
        "final_eth_price":          result["params"]["final_eth_price"],
    }
    all_results.append(row)


def run_sensitivity_group(group_name: str, scenarios: list, borrowers, all_results):
    """Chạy nhóm sensitivity analysis (giữ tương thích bản cũ)."""
    for s in scenarios:
        feedback = s.get("price_feedback", False)
        depth    = s.get("market_depth_usd") or 10_000_000.0
        capital  = s.get("liquidator_capital", LIQUIDATOR_CAPITAL)
        print(f"\n{'='*70}")
        print(f"[{group_name}] {s['name']} | "
              f"Sốc: {s['price_shock_pct']*100:.0f}% | Gas: ${s['gas_cost_usd']} | "
              f"Capital: ${capital:,.0f}")
        result = run_scenario(
            borrowers          = borrowers,
            initial_eth_price  = INITIAL_ETH_PRICE,
            price_shock_pct    = s["price_shock_pct"],
            liquidator_capital = capital,
            gas_cost_usd       = s["gas_cost_usd"],
            price_feedback     = feedback,
            market_depth_usd   = depth,
        )
        after = result["after"]
        ls    = result["liquidator_stats"]
        print(f"  → Touched={after['n_touched']} | Repaid={after['n_repaid']} | "
              f"Defaulted={after['n_defaulted']} | StillUnsafe={after['n_still_unsafe']} | "
              f"BadDebt=${after['total_realized_bad_debt']:,.2f} | "
              f"Profit=${ls['total_profit']:,.2f}")
        all_results.append({
            "experiment_id": group_name,
            "scenario": s["name"],
            "strategy": "fixed",
            "price_shock_pct": s["price_shock_pct"],
            "gas_cost_usd": s["gas_cost_usd"],
            "liquidator_capital": capital,
            "liquidity_shock_pct": 0,
            "demand_surge_usdc": 0,
            "price_feedback": feedback,
            "market_depth_usd": depth if feedback else "",
            "rounds_run": result["rounds_run"],
            "liquidation_coverage": result.get("liquidation_coverage", ""),
            "withdrawal_fulfillment": "",
            **{f"before_{k}": v for k, v in result["before"].items()},
            **{f"after_{k}": v  for k, v in result["after"].items()},
            "liquidation_count": ls["liquidation_count"],
            "failed_no_profit": ls["failed_no_profit"],
            "failed_no_capital": ls["failed_no_capital"],
            "liquidator_profit": ls["total_profit"],
            "liquidator_capital_final": ls["final_capital_usdc"],
            "final_eth_price": result["params"]["final_eth_price"],
        })


def run_robustness(seeds, scenario, strategy, all_results):
    """Multi-seed robustness check."""
    print(f"\n\n📊 ROBUSTNESS CHECK — Kịch bản {scenario} | Strategy {strategy} | Seeds {seeds}")
    for seed in seeds:
        borrowers = generate_borrowers(n=50, eth_price=INITIAL_ETH_PRICE, seed=seed)
        lenders   = generate_lenders(n=20, seed=seed)
        pool      = make_pool(borrowers, lenders)
        params    = get_scenario_params(scenario)
        result = run_scenario(
            borrowers           = borrowers,
            initial_eth_price   = params["initial_eth_price"],
            price_shock_pct     = params["price_shock_pct"],
            liquidator_capital  = params["liquidator_capital"],
            gas_cost_usd        = params["gas_cost_usd"],
            lenders             = lenders,
            pool                = pool,
            liquidity_shock_pct = params["liquidity_shock_pct"],
            demand_surge_usdc   = params["demand_surge_usdc"],
            price_feedback      = params["price_feedback"],
            market_depth_usd    = params["market_depth_usd"],
            strategy            = strategy,
        )
        after = result["after"]
        ls    = result["liquidator_stats"]
        print(f"  seed={seed}: Touched={after['n_touched']} | "
              f"Repaid={after['n_repaid']} | Defaulted={after['n_defaulted']} | "
              f"StillUnsafe={after['n_still_unsafe']} | "
              f"BadDebt=${after['total_realized_bad_debt']:,.2f} | "
              f"Coverage={result['liquidation_coverage']*100:.1f}%")
        all_results.append({
            "experiment_id": f"robustness_seed{seed}",
            "scenario": scenario, "strategy": strategy,
            **{f"before_{k}": v for k, v in result["before"].items()},
            **{f"after_{k}": v  for k, v in result["after"].items()},
            "liquidation_count": ls["liquidation_count"],
            "liquidator_profit": ls["total_profit"],
            "liquidation_coverage": result["liquidation_coverage"],
        })


def main():
    all_results = []

    # Sinh tác nhân chung (seed=42)
    borrowers = generate_borrowers(n=50, eth_price=INITIAL_ETH_PRICE)
    lenders   = generate_lenders(n=20)
    pool      = make_pool(borrowers, lenders)

    # ── 12 thực nghiệm E1–E12 ─────────────────────────────────────────────────
    print("\n\n📊 12 THỰC NGHIỆM E1–E12 (theo thiết kế doc nghiên cứu)")
    for exp_id, scenario, strategy in EXPERIMENTS:
        run_experiment(exp_id, scenario, strategy,
                       borrowers, lenders, pool, all_results)

    # ── Sensitivity Analysis (giữ tương thích) ───────────────────────────────
    print("\n\n📊 SENSITIVITY ANALYSIS — Sốc giá ETH")
    run_sensitivity_group("price_shock", PRICE_SHOCK_SCENARIOS, borrowers, all_results)

    print("\n\n📊 SENSITIVITY ANALYSIS — Gas")
    run_sensitivity_group("gas_sensitivity", GAS_SENSITIVITY_SCENARIOS, borrowers, all_results)

    print("\n\n📊 SENSITIVITY ANALYSIS — Cascade")
    run_sensitivity_group("cascade", CASCADE_SCENARIOS, borrowers, all_results)

    print("\n\n📊 SENSITIVITY ANALYSIS — Vốn Liquidator")
    run_sensitivity_group("capital", CAPITAL_SENSITIVITY_SCENARIOS, borrowers, all_results)

    # ── Multi-seed Robustness Check ───────────────────────────────────────────
    run_robustness(ROBUSTNESS_SEEDS, ROBUSTNESS_SCENARIO, ROBUSTNESS_STRATEGY, all_results)

    # ── Lưu CSV ───────────────────────────────────────────────────────────────
    csv_path = "results/results.csv"
    if all_results:
        fieldnames = list(all_results[0].keys())
        for r in all_results:
            for k in fieldnames:
                if k not in r:
                    r[k] = ""
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_results)
    print(f"\n\n✓ Kết quả đã lưu tại {csv_path}")


if __name__ == "__main__":
    main()
