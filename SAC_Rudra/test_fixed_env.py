# Debug script to test the FIXED environment
# Run this to see if actions now affect rewards

import numpy as np
import torch
from sac_config import SACConfig

# Import FIXED environment
from microgrid_env import MicrogridEnv

def test_environment():
    """Test if actions actually affect rewards"""
    
    config = SACConfig()
    env = MicrogridEnv(config.DATA_PATH, config)
    
    print("="*70)
    print("TESTING: Does action affect reward?")
    print("="*70)
    
    # Test 1: All idle actions (no charging/discharging)
    print("\nTest 1: ALL IDLE (actions = 0)")
    print("-"*70)
    state, _ = env.reset()
    total_cost_idle = 0
    
    for step in range(24):
        action = np.zeros(6)  # All idle
        next_state, reward, done, _, info = env.step(action)
        total_cost_idle += info['cost_breakdown']['total_cost']
        
        if step == 0:  # Print first step details
            print(f"Step 0:")
            print(f"  Action: {action}")
            print(f"  Reward: {reward:.2f}")
            print(f"  Cost: {info['cost_breakdown']['total_cost']:.2f}")
            print(f"  Grid Purchase: {info['cost_breakdown']['grid_purchase']:.2f}")
            print(f"  Grid Revenue: {info['cost_breakdown']['grid_revenue']:.2f}")
            print(f"  ESS/EV Power: {info['ess_ev_power']}")
    
    print(f"\nTotal Cost (Idle): ${total_cost_idle:.2f}")
    
    # Test 2: Always charge (positive actions)
    print("\n" + "="*70)
    print("Test 2: ALWAYS CHARGE (actions = +0.5)")
    print("-"*70)
    state, _ = env.reset()
    total_cost_charge = 0
    
    for step in range(24):
        action = np.ones(6) * 0.5  # Always charge at 50%
        next_state, reward, done, _, info = env.step(action)
        total_cost_charge += info['cost_breakdown']['total_cost']
        
        if step == 0:
            print(f"Step 0:")
            print(f"  Action: {action}")
            print(f"  Reward: {reward:.2f}")
            print(f"  Cost: {info['cost_breakdown']['total_cost']:.2f}")
            print(f"  Grid Purchase: {info['cost_breakdown']['grid_purchase']:.2f}")
            print(f"  Grid Revenue: {info['cost_breakdown']['grid_revenue']:.2f}")
            print(f"  ESS/EV Power: {info['ess_ev_power']}")
    
    print(f"\nTotal Cost (Always Charge): ${total_cost_charge:.2f}")
    
    # Test 3: Always discharge (negative actions)
    print("\n" + "="*70)
    print("Test 3: ALWAYS DISCHARGE (actions = -0.5)")
    print("-"*70)
    state, _ = env.reset()
    total_cost_discharge = 0
    
    for step in range(24):
        action = np.ones(6) * -0.5  # Always discharge at 50%
        next_state, reward, done, _, info = env.step(action)
        total_cost_discharge += info['cost_breakdown']['total_cost']
        
        if step == 0:
            print(f"Step 0:")
            print(f"  Action: {action}")
            print(f"  Reward: {reward:.2f}")
            print(f"  Cost: {info['cost_breakdown']['total_cost']:.2f}")
            print(f"  Grid Purchase: {info['cost_breakdown']['grid_purchase']:.2f}")
            print(f"  Grid Revenue: {info['cost_breakdown']['grid_revenue']:.2f}")
            print(f"  ESS/EV Power: {info['ess_ev_power']}")
    
    print(f"\nTotal Cost (Always Discharge): ${total_cost_discharge:.2f}")
    
    # Test 4: Smart strategy (charge at low price, discharge at high price)
    print("\n" + "="*70)
    print("Test 4: SMART STRATEGY (charge when price low, discharge when high)")
    print("-"*70)
    state, _ = env.reset()
    total_cost_smart = 0
    
    for step in range(24):
        # Get current price
        price = env.data.loc[step, 'MBP']
        
        # Simple strategy: charge if price < 6, discharge if price > 7
        if price < 6.0:
            action = np.ones(6) * 0.7  # Charge aggressively
        elif price > 7.0:
            action = np.ones(6) * -0.7  # Discharge aggressively
        else:
            action = np.zeros(6)  # Idle
        
        next_state, reward, done, _, info = env.step(action)
        total_cost_smart += info['cost_breakdown']['total_cost']
        
        if step == 0:
            print(f"Step 0 (Price={price:.2f}):")
            print(f"  Action: {action}")
            print(f"  Reward: {reward:.2f}")
            print(f"  Cost: {info['cost_breakdown']['total_cost']:.2f}")
            print(f"  Grid Purchase: {info['cost_breakdown']['grid_purchase']:.2f}")
            print(f"  Grid Revenue: {info['cost_breakdown']['grid_revenue']:.2f}")
            print(f"  ESS/EV Power: {info['ess_ev_power']}")
    
    print(f"\nTotal Cost (Smart Strategy): ${total_cost_smart:.2f}")
    
    # Compare all strategies
    print("\n" + "="*70)
    print("COMPARISON OF ALL STRATEGIES")
    print("="*70)
    print(f"1. Idle Strategy:      ${total_cost_idle:.2f}")
    print(f"2. Always Charge:      ${total_cost_charge:.2f}")
    print(f"3. Always Discharge:   ${total_cost_discharge:.2f}")
    print(f"4. Smart Strategy:     ${total_cost_smart:.2f}")
    print()
    
    if total_cost_idle == total_cost_charge == total_cost_discharge:
        print("❌ ERROR: All costs are the same! Actions don't affect rewards!")
        print("   The environment is BROKEN.")
        return False
    else:
        print("✅ SUCCESS: Different actions lead to different costs!")
        print("   The environment is working correctly.")
        
        # Calculate savings
        baseline = total_cost_idle
        best = min(total_cost_idle, total_cost_charge, total_cost_discharge, total_cost_smart)
        savings_percent = ((baseline - best) / baseline) * 100
        
        print(f"\n   Best strategy saves: ${baseline - best:.2f} ({savings_percent:.1f}%)")
        print("   SAC agent should be able to learn this!")
        return True

if __name__ == "__main__":
    success = test_environment()
    
    if success:
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Replace 'microgrid_env.py' with 'microgrid_env_FIXED.py'")
        print("2. Rename: mv microgrid_env_FIXED.py microgrid_env.py")
        print("3. Re-run training: python sac_main.py")
        print("4. You should now see rewards INCREASING over episodes!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("PROBLEM DETECTED:")
        print("="*70)
        print("The environment still doesn't work. Check:")
        print("1. Data file has correct columns")
        print("2. Actions are being applied correctly")
        print("3. Energy balance includes ESS/EV power flow")
        print("="*70)
