# Baseline Policy Comparison
# Compare SAC against simple baseline strategies

import numpy as np
import pandas as pd
from sac_config import SACConfig
from microgrid_env import MicrogridEnv

def test_no_action_baseline(env, num_episodes=10):
    """Baseline 1: Do nothing (all actions = 0)"""
    print("\n" + "="*80)
    print("BASELINE 1: No ESS/EV Actions (Do Nothing)")
    print("="*80)
    
    costs = []
    
    for ep in range(num_episodes):
        state, _ = env.reset()
        episode_cost = 0
        
        for step in range(env.max_steps):
            # Zero action = no charging/discharging
            action = np.zeros(env.action_space.shape)
            
            next_state, reward, terminated, truncated, info = env.step(action)
            episode_cost += info['cost_breakdown']['total_cost']
            
            state = next_state
            if terminated or truncated:
                break
        
        costs.append(episode_cost)
    
    mean_cost = np.mean(costs)
    std_cost = np.std(costs)
    
    print(f"Average Cost: ${mean_cost:.2f} ± ${std_cost:.2f}")
    print(f"Min Cost: ${min(costs):.2f}")
    print(f"Max Cost: ${max(costs):.2f}")
    
    return mean_cost, costs

def test_price_based_baseline(env, num_episodes=10):
    """Baseline 2: Simple rule-based charging"""
    print("\n" + "="*80)
    print("BASELINE 2: Price-Based Charging")
    print("Charge when price < $5/kWh, Discharge when price > $6/kWh")
    print("="*80)
    
    costs = []
    
    for ep in range(num_episodes):
        state, _ = env.reset()
        episode_cost = 0
        
        for step in range(env.max_steps):
            # Get current price
            i = min(step, len(env.data) - 1)
            mbp = env.data.loc[i, 'MBP']
            
            # Simple rule: charge when cheap, discharge when expensive
            if mbp < 5.0:
                # Charge at 50% rate when price is low
                action = np.ones(env.action_space.shape) * 0.5
            elif mbp > 6.0:
                # Discharge at 50% rate when price is high
                action = np.ones(env.action_space.shape) * -0.5
            else:
                # Idle when price is medium
                action = np.zeros(env.action_space.shape)
            
            next_state, reward, terminated, truncated, info = env.step(action)
            episode_cost += info['cost_breakdown']['total_cost']
            
            state = next_state
            if terminated or truncated:
                break
        
        costs.append(episode_cost)
    
    mean_cost = np.mean(costs)
    std_cost = np.std(costs)
    
    print(f"Average Cost: ${mean_cost:.2f} ± ${std_cost:.2f}")
    print(f"Min Cost: ${min(costs):.2f}")
    print(f"Max Cost: ${max(costs):.2f}")
    
    return mean_cost, costs

def test_optimal_threshold_baseline(env, num_episodes=10):
    """Baseline 3: Optimized threshold-based policy"""
    print("\n" + "="*80)
    print("BASELINE 3: Optimized Threshold Policy")
    print("Charge when price < median, Discharge when price > median")
    print("="*80)
    
    # Calculate median price from data
    median_price = env.data['MBP'].median()
    print(f"Median MBP: ${median_price:.2f}/kWh")
    
    costs = []
    
    for ep in range(num_episodes):
        state, _ = env.reset()
        episode_cost = 0
        
        for step in range(env.max_steps):
            # Get current price
            i = min(step, len(env.data) - 1)
            mbp = env.data.loc[i, 'MBP']
            
            # Optimized rule based on median
            if mbp < median_price - 0.5:
                # Strong charging when significantly below median
                action = np.ones(env.action_space.shape) * 0.8
            elif mbp < median_price:
                # Moderate charging when below median
                action = np.ones(env.action_space.shape) * 0.4
            elif mbp > median_price + 0.5:
                # Strong discharging when significantly above median
                action = np.ones(env.action_space.shape) * -0.8
            elif mbp > median_price:
                # Moderate discharging when above median
                action = np.ones(env.action_space.shape) * -0.4
            else:
                # Idle near median
                action = np.zeros(env.action_space.shape)
            
            next_state, reward, terminated, truncated, info = env.step(action)
            episode_cost += info['cost_breakdown']['total_cost']
            
            state = next_state
            if terminated or truncated:
                break
        
        costs.append(episode_cost)
    
    mean_cost = np.mean(costs)
    std_cost = np.std(costs)
    
    print(f"Average Cost: ${mean_cost:.2f} ± ${std_cost:.2f}")
    print(f"Min Cost: ${min(costs):.2f}")
    print(f"Max Cost: ${max(costs):.2f}")
    
    return mean_cost, costs

def main():
    """Run all baseline comparisons"""
    config = SACConfig()
    env = MicrogridEnv(config.DATA_PATH, config)
    
    print("="*80)
    print("BASELINE POLICY COMPARISON")
    print("="*80)
    print(f"Data file: {config.DATA_PATH}")
    print(f"Episodes per baseline: 10")
    print(f"Steps per episode: {env.max_steps}")
    
    # Calculate theoretical minimum
    total_load = env.data[['IL1', 'IL2', 'CL3', 'CL4', 'SL5', 'SL6', 'SL7', 'CPL8']].sum().sum()
    total_pv = env.data[['IP1', 'IP2', 'CP3', 'CP4', 'SP5', 'SP6', 'SP7', 'CPP8']].sum().sum()
    net_load = total_load - total_pv
    avg_price = env.data['MBP'].mean()
    theoretical_min = net_load * avg_price
    
    print(f"\nTheoretical Minimum Cost (no ESS/EV): ${theoretical_min:.2f}")
    print("="*80)
    
    # Test baselines
    no_action_cost, _ = test_no_action_baseline(env, num_episodes=10)
    price_based_cost, _ = test_price_based_baseline(env, num_episodes=10)
    optimal_cost, _ = test_optimal_threshold_baseline(env, num_episodes=10)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Theoretical Minimum:     ${theoretical_min:.2f}")
    print(f"Baseline 1 (No Action):  ${no_action_cost:.2f} ({(no_action_cost/theoretical_min - 1)*100:+.1f}%)")
    print(f"Baseline 2 (Price Rule): ${price_based_cost:.2f} ({(price_based_cost/theoretical_min - 1)*100:+.1f}%)")
    print(f"Baseline 3 (Optimal):    ${optimal_cost:.2f} ({(optimal_cost/theoretical_min - 1)*100:+.1f}%)")
    print("="*80)
    
    # Best baseline
    best_cost = min(no_action_cost, price_based_cost, optimal_cost)
    print(f"\n🎯 Best Baseline Cost: ${best_cost:.2f}")
    print(f"📊 SAC should achieve:  ${best_cost * 0.85:.2f} - ${best_cost * 0.95:.2f}")
    print(f"   (15-5% improvement over best baseline)")
    
    # Save results
    results_df = pd.DataFrame({
        'Baseline': ['Theoretical Min', 'No Action', 'Price-Based', 'Optimal Threshold'],
        'Cost': [theoretical_min, no_action_cost, price_based_cost, optimal_cost],
        'Improvement_vs_Theory': [0, 
                                   (no_action_cost/theoretical_min - 1)*100,
                                   (price_based_cost/theoretical_min - 1)*100,
                                   (optimal_cost/theoretical_min - 1)*100]
    })
    results_df.to_csv('./logs/baseline_comparison.csv', index=False)
    print(f"\n✓ Results saved to ./logs/baseline_comparison.csv")

if __name__ == "__main__":
    main()
