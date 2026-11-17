from scenarios import generate_borrowers, generate_lenders, make_pool, get_scenario_params, INITIAL_ETH_PRICE
from simulation import run_scenario

for scenario in ['S0','S1','S2','S3','S4','S5']:
    for strategy in ['fixed', 'adaptive']:
        b = generate_borrowers(20, INITIAL_ETH_PRICE)
        l = generate_lenders(10)
        p = make_pool(b, l)
        params = get_scenario_params(scenario)
        r = run_scenario(
            borrowers=b, initial_eth_price=params['initial_eth_price'],
            price_shock_pct=params['price_shock_pct'],
            liquidator_capital=params['liquidator_capital'],
            gas_cost_usd=params['gas_cost_usd'],
            lenders=l, pool=p,
            liquidity_shock_pct=params['liquidity_shock_pct'],
            demand_surge_usdc=params['demand_surge_usdc'],
            price_feedback=params['price_feedback'],
            market_depth_usd=params['market_depth_usd'],
            strategy=strategy,
        )
        after = r['after']
        util = after.get('utilization')
        util_str = f"{util*100:.1f}%" if util is not None else "N/A"
        cov = r['liquidation_coverage'] * 100
        print(f"{scenario}/{strategy}: touched={after['n_touched']} repaid={after['n_repaid']} defaulted={after['n_defaulted']} bad_debt={after['total_realized_bad_debt']:.0f} util={util_str} coverage={cov:.0f}%")
print("ALL OK")
