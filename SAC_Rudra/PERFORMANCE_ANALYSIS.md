# SAC Performance Issues and Fixes

## Problem Summary
The SAC agent is performing very poorly with costs around $80,000-90,000 per day when the theoretical minimum should be around $77,966 (just buying net load from grid).

## Root Causes Identified

### 1. **Poor Reward Shaping** ❌
- Current: `reward = -total_cost`
- Problem: No guidance for LEARNING, just final outcome
- The agent gets -$80,000 whether it does slightly bad or terribly bad
  
**Fix**: Add shaped rewards that guide learning:
```python
reward = (
    -net_energy_cost          # Main objective
    + ess_utilization_bonus   # Reward for using ESS wisely  
    - constraint_penalty       # Punish violations
    + self_sufficiency_bonus  # Reward for reducing grid dependency
)
```

### 2. **No Baseline Comparison** ❌
- We don't know if -$80,000 is good or bad without a baseline
- Need to compare against "do nothing" strategy (no ESS/EV actions)

**Fix**: Implement baseline policies:
- **Baseline 1**: No ESS/EV (all actions = 0)
- **Baseline 2**: Simple rule-based (charge when cheap, discharge when expensive)

### 3. **Excessive Action Impact** ❌  
- ESS/EV actions in `[-1, 1]` are scaled to 10% of capacity per step
- With 6 batteries, this can swing ±60 kWh per hour
- Random actions are creating huge deficit spikes

**Fix**: Reduce action scale or add action smoothing
```python
# Current: 10% per step
charge_amount = action_val * max_capacity * 0.1

# Proposed: 5% per step with smoothing
charge_amount = action_val * max_capacity * 0.05
```

### 4. **Wrong Cost Accounting** ⚠️
- The environment calculates deficit/surplus AFTER ESS/EV actions
- But doesn't properly account for:
  - Internal trading between microgrids
  - ESS efficiency losses being double-counted
  - Market clearing price vs grid prices

**Current flow**:
```
Load - PV → Base deficit/surplus
+ ESS charge/discharge → Modified deficit/surplus
→ All deficit bought at MBP, all surplus sold at GSP
```

**Issue**: ESS charging adds to deficit (needs grid power), but this is CORRECT!
The problem is the agent isn't learning WHEN to charge (low price) vs discharge (high price)

### 5. **State Normalization Issues** ⚠️
- States are normalized to [0, 1] but reward is in [-100000, 0]
- This massive scale mismatch makes learning unstable
- Alpha (entropy) is diverging (1.0 → 7.8) showing instability

**Fix**: Normalize rewards:
```python
# Option 1: Divide by expected max cost
reward_normalized = reward / 100000.0

# Option 2: Use reward scaling
reward_scaled = reward / 1000.0  # Now in [-100, 0] range
```

### 6. **No Exploration Strategy** ❌
- 1000 warmup steps with random actions
- Then pure exploitation
- Agent might get stuck in local minimum

**Fix**: Use epsilon-greedy or better exploration
```python
if np.random.random() < epsilon:
    action = explore_action()
else:
    action = policy_action()
```

## Recommended Action Plan

### Immediate Fixes (High Priority):
1. ✅ **Fix PV data** - Done! Now have realistic solar generation
2. ⚠️ **Implement baseline comparison** - See how bad "do nothing" is
3. ⚠️ **Add reward shaping** - Guide the agent toward good behavior
4. ⚠️ **Normalize rewards** - Scale to reasonable range

### Medium Priority:
5. **Reduce action scale** - Make actions less disruptive
6. **Add action penalties** - Penalize frequent charge/discharge
7. **Improve state representation** - Add price trends, time-of-day encoding

### Low Priority:
8. **Tune hyperparameters** - Learning rates, batch size, etc.
9. **Add curriculum learning** - Start with easier scenarios
10. **Ensemble policies** - Combine rule-based + learned

## Expected Performance After Fixes

**Baseline (No ESS/EV)**:
- Cost: ~$77,966/day (net load × avg price)
- This is the WORST acceptable performance

**Simple Rule-Based**:
- Charge ESS when price < $5/kWh
- Discharge ESS when price > $6/kWh
- Expected savings: 5-10% → Cost: ~$70,000-74,000/day

**Good SAC Performance**:
- Learn optimal charge/discharge timing
- Coordinate multiple ESS/EV
- Expected savings: 10-20% → Cost: ~$62,000-70,000/day

**Current SAC**: 
- Cost: ~$80,000-90,000/day
- WORSE than doing nothing! 💀
- Actions are ADDING cost instead of reducing it

## Next Steps

1. Run baseline comparison script (create this)
2. Implement reward shaping
3. Add reward normalization  
4. Reduce training episodes but increase evaluation
5. Plot learning curves to see if ANY learning is happening

The agent CAN'T POSSIBLY be learning if it's doing worse than random!
