# Diagnostic script to understand what's happening in the environment

import pandas as pd
import numpy as np
from sac_config import SACConfig
from microgrid_env import MicrogridEnv

def diagnose_environment():
    """Run diagnostic to understand costs and energy flows"""
    
    config = SACConfig()
    env = MicrogridEnv(config.DATA_PATH, config)
    
    print("="*80)
    print("ENVIRONMENT DIAGNOSTIC")
    print("="*80)
    
    # Check data
    print(f"\nData shape: {env.data.shape}")
    print(f"Max steps: {env.max_steps}")
    print(f"\nSample data (first 3 hours):")
    print(env.data.head(3))
    
    # Run one episode with random actions
    state, info = env.reset()
    print(f"\n{'='*80}")
    print("RUNNING ONE EPISODE WITH RANDOM ACTIONS")
    print(f"{'='*80}")
    
    total_cost = 0
    total_grid_purchase = 0
    total_grid_revenue = 0
    total_load = 0
    total_pv = 0
    total_deficit = 0
    total_surplus = 0
    
    step_details = []
    
    for step in range(min(24, env.max_steps)):
        # Random action
        action = env.action_space.sample()
        
        # Step
        next_state, reward, terminated, truncated, info = env.step(action)
        
        # Extract info
        cost_bd = info['cost_breakdown']
        energy_data = info['energy_data']
        
        # Accumulate totals
        total_cost += cost_bd['total_cost']
        total_grid_purchase += cost_bd['grid_purchase']
        total_grid_revenue += cost_bd['grid_revenue']
        total_deficit += energy_data['total_deficit']
        total_surplus += energy_data['total_surplus']
        
        # Calculate loads and PV
        i = step
        loads = [
            env.data.loc[i, 'IL1'], env.data.loc[i, 'IL2'],
            env.data.loc[i, 'CL3'], env.data.loc[i, 'CL4'],
            env.data.loc[i, 'SL5'], env.data.loc[i, 'SL6'],
            env.data.loc[i, 'SL7'], env.data.loc[i, 'CPL8']
        ]
        pvs = [
            env.data.loc[i, 'IP1'], env.data.loc[i, 'IP2'],
            env.data.loc[i, 'CP3'], env.data.loc[i, 'CP4'],
            env.data.loc[i, 'SP5'], env.data.loc[i, 'SP6'],
            env.data.loc[i, 'SP7'], env.data.loc[i, 'CPP8']
        ]
        
        step_load = sum(loads)
        step_pv = sum(pvs)
        total_load += step_load
        total_pv += step_pv
        
        step_details.append({
            'step': step + 1,
            'load': step_load,
            'pv': step_pv,
            'deficit': energy_data['total_deficit'],
            'surplus': energy_data['total_surplus'],
            'mbp': energy_data['prices']['mbp'],
            'gsp': energy_data['prices']['gsp'],
            'cost': cost_bd['total_cost'],
            'reward': reward
        })
        
        if step < 3:  # Print first 3 steps in detail
            print(f"\n--- STEP {step + 1} ---")
            print(f"Total Load: {step_load:.2f} kWh")
            print(f"Total PV:   {step_pv:.2f} kWh")
            print(f"Net (Load-PV): {step_load - step_pv:.2f} kWh")
            print(f"Deficit: {energy_data['total_deficit']:.2f} kWh")
            print(f"Surplus: {energy_data['total_surplus']:.2f} kWh")
            print(f"MBP: ${energy_data['prices']['mbp']:.2f}/kWh")
            print(f"GSP: ${energy_data['prices']['gsp']:.2f}/kWh")
            print(f"Grid Purchase: ${cost_bd['grid_purchase']:.2f}")
            print(f"Grid Revenue: ${cost_bd['grid_revenue']:.2f}")
            print(f"Net Cost: ${cost_bd['total_cost']:.2f}")
            print(f"Reward: {reward:.2f}")
        
        state = next_state
        
        if terminated or truncated:
            break
    
    print(f"\n{'='*80}")
    print("EPISODE SUMMARY")
    print(f"{'='*80}")
    print(f"Total Load:          {total_load:.2f} kWh")
    print(f"Total PV:            {total_pv:.2f} kWh")
    print(f"Net Load:            {total_load - total_pv:.2f} kWh")
    print(f"Total Deficit:       {total_deficit:.2f} kWh")
    print(f"Total Surplus:       {total_surplus:.2f} kWh")
    print(f"Total Grid Purchase: ${total_grid_purchase:.2f}")
    print(f"Total Grid Revenue:  ${total_grid_revenue:.2f}")
    print(f"TOTAL COST:          ${total_cost:.2f}")
    print(f"TOTAL REWARD:        {-total_cost:.2f}")
    print(f"\nAverage cost per hour: ${total_cost/24:.2f}")
    print(f"Average cost per kWh:  ${total_cost/total_load:.4f}")
    
    # Create detailed DataFrame
    df = pd.DataFrame(step_details)
    print(f"\n{'='*80}")
    print("HOURLY BREAKDOWN")
    print(f"{'='*80}")
    print(df.to_string(index=False))
    
    # Analyze the problem
    print(f"\n{'='*80}")
    print("PROBLEM ANALYSIS")
    print(f"{'='*80}")
    
    avg_deficit = df['deficit'].mean()
    avg_surplus = df['surplus'].mean()
    avg_cost = df['cost'].mean()
    
    print(f"Average hourly deficit: {avg_deficit:.2f} kWh")
    print(f"Average hourly surplus: {avg_surplus:.2f} kWh")
    print(f"Average hourly cost: ${avg_cost:.2f}")
    
    if avg_deficit > total_pv / 24:
        print(f"\n⚠️  ISSUE: Deficit ({avg_deficit:.0f} kWh/h) >> PV ({total_pv/24:.0f} kWh/h)")
        print("   The agent is creating MORE deficit than available PV!")
        print("   This suggests ESS/EV actions are making things WORSE, not better.")
    
    if avg_cost > 3000:
        print(f"\n⚠️  ISSUE: Hourly cost (${avg_cost:.0f}) is EXTREMELY high!")
        print(f"   Expected cost should be closer to ${(total_load-total_pv)/24 * 5:.0f}/hour")
        print("   (i.e., net load * average price)")

if __name__ == "__main__":
    diagnose_environment()
