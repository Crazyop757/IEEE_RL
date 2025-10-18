# Gymnasium Environment for Multi-Microgrid Energy Management
# Wrapper around your existing code_v7.py functions

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
import sys

# Import your existing code (adjust path as needed)
# sys.path.append(r'D:\IIITN\PhD\Reinforcement_Learning_implementation')
# Assuming code_v7.py functions are available

class MicrogridEnv(gym.Env):
    """Custom Gym Environment for 8-Microgrid Energy Management System"""
    
    metadata = {'render_modes': ['human']}
    
    def __init__(self, data_path, config):
        super(MicrogridEnv, self).__init__()
        
        self.config = config
        self.data_path = data_path
        
        # Load data
        self.data = pd.read_csv(data_path)
        self.max_steps = len(self.data)  # 24 hours typically
        
        # Define action and observation spaces
        # Actions: continuous charging/discharging rates for ESS/EV in [-1, 1]
        # [com1, com2, sd1, sd2, sd3, camp] = 6 actions
        self.action_space = spaces.Box(
            low=-1.0, 
            high=1.0, 
            shape=(config.ACTION_DIM,), 
            dtype=np.float32
        )
        
        # Observations: state vector (31 dimensions based on config)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(config.STATE_DIM,),
            dtype=np.float32
        )
        
        # Initialize microgrid states
        self.reset()
    
    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        # Reset to initial ESS/EV levels (50% charged)
        self.ESS_EV_status = {
            "com1": 50.0,  # 50% of ESS_MAX
            "com2": 50.0,
            "sd1": 8.0,    # 50% of EV_MAX
            "sd2": 8.0,
            "sd3": 8.0,
            "camp": 50.0
        }
        
        self.current_step = 0
        self.episode_cost = 0.0
        self.episode_energy_traded = 0.0
        
        # Get initial observation
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action):
        """Execute one time step within the environment"""
        # Clip actions to valid range
        action = np.clip(action, -1.0, 1.0)
        
        # Apply actions to ESS/EV (convert from [-1,1] to actual rates)
        self._apply_actions(action)
        
        # Calculate energy surplus/deficit with updated ESS/EV levels
        energy_data = self._calculate_energy_balance()
        
        # Calculate reward (negative cost)
        reward, cost_breakdown = self._calculate_reward(energy_data)
        
        # Update episode statistics
        self.episode_cost += cost_breakdown['total_cost']
        self.episode_energy_traded += energy_data['total_traded']
        
        # Move to next time step
        self.current_step += 1
        
        # Check if episode is done
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        # Get next observation
        observation = self._get_observation()
        
        # Additional info for logging
        info = {
            'cost_breakdown': cost_breakdown,
            'energy_data': energy_data,
            'ESS_EV_status': self.ESS_EV_status.copy(),
            'step': self.current_step
        }
        
        return observation, reward, terminated, truncated, info
    
    def _apply_actions(self, action):
        """Apply charging/discharging actions to ESS and EV"""
        # action shape: (6,) for [com1, com2, sd1, sd2, sd3, camp]
        # action value: -1 (full discharge) to +1 (full charge)
        
        # Get current prices to determine preferences
        i = self.current_step
        mbp = self.data.loc[i, "MBP"]
        
        p_c = (self.config.MBP_MAX - mbp) / (self.config.MBP_MAX - self.config.MBP_MIN)
        p_d = (mbp - self.config.MBP_MIN) / (self.config.MBP_MAX - self.config.MBP_MIN)
        
        # Apply actions with efficiency losses
        action_mapping = {
            0: "com1", 1: "com2", 2: "sd1", 
            3: "sd2", 4: "sd3", 5: "camp"
        }
        
        for idx, key in action_mapping.items():
            current_level = self.ESS_EV_status[key]
            action_val = action[idx]
            
            # Determine max capacity
            max_capacity = self.config.ESS_MAX if key in ["com1", "com2", "camp"] else self.config.EV_MAX
            
            if action_val > 0:  # Charging
                # Calculate charging amount with losses
                charge_amount = action_val * max_capacity * 0.1  # 10% of capacity per step
                charge_amount_with_loss = charge_amount * self.config.N_C
                
                new_level = min(current_level + charge_amount_with_loss, max_capacity)
                
            elif action_val < 0:  # Discharging
                # Calculate discharging amount with losses
                discharge_amount = abs(action_val) * max_capacity * 0.1
                discharge_amount_with_loss = discharge_amount / self.config.N_D
                
                new_level = max(current_level - discharge_amount_with_loss, 0.0)
            
            else:  # Idle
                new_level = current_level
            
            self.ESS_EV_status[key] = new_level
    
    def _calculate_energy_balance(self):
        """Calculate energy surplus/deficit for all microgrids"""
        i = self.current_step
        
        # Read prices and costs
        gbp = self.data.loc[i, "GBP"]
        mbp = self.data.loc[i, "MBP"]
        msp = self.data.loc[i, "MSP"]
        gsp = self.data.loc[i, "GSP"]
        chp_cost = self.data.loc[i, "CHP_Cost"]
        
        # Calculate for all 8 microgrids (using your existing logic from code_v7.py)
        # Here's simplified version - you should integrate your actual functions
        
        total_deficit = 0.0
        total_surplus = 0.0
        mg_data = {}
        
        # Industry MGs (1, 2) - use CHP optimization
        for mg_id in [1, 2]:
            load = self.data.loc[i, f"IL{mg_id}"]
            pv = self.data.loc[i, f"IP{mg_id}"]
            deficit = max(0, load - pv)
            surplus = max(0, pv - load)
            
            total_deficit += deficit
            total_surplus += surplus
            mg_data[f'ind{mg_id}'] = {'deficit': deficit, 'surplus': surplus}
        
        # Community MGs (3, 4) - with ESS
        for mg_id, key in [(3, 'com1'), (4, 'com2')]:
            load = self.data.loc[i, f"CL{mg_id}"]
            pv = self.data.loc[i, f"CP{mg_id}"]
            
            # Simplified: ESS already managed by actions
            deficit = max(0, load - pv)
            surplus = max(0, pv - load)
            
            total_deficit += deficit
            total_surplus += surplus
            mg_data[key] = {'deficit': deficit, 'surplus': surplus}
        
        # Single-Dwelling MGs (5, 6, 7) - with EV
        ev_available = self.data.loc[i, "EV_Avail"]
        for mg_id, key in [(5, 'sd1'), (6, 'sd2'), (7, 'sd3')]:
            load = self.data.loc[i, f"SL{mg_id}"]
            pv = self.data.loc[i, f"SP{mg_id}"]
            
            deficit = max(0, load - pv)
            surplus = max(0, pv - load)
            
            total_deficit += deficit
            total_surplus += surplus
            mg_data[key] = {'deficit': deficit, 'surplus': surplus}
        
        # Campus MG (8) - with ESS and CHP
        load = self.data.loc[i, "CPL8"]
        pv = self.data.loc[i, "CPP8"]
        
        deficit = max(0, load - pv)
        surplus = max(0, pv - load)
        
        total_deficit += deficit
        total_surplus += surplus
        mg_data['camp'] = {'deficit': deficit, 'surplus': surplus}
        
        return {
            'total_deficit': total_deficit,
            'total_surplus': total_surplus,
            'total_traded': min(total_deficit, total_surplus),
            'mg_data': mg_data,
            'prices': {'gbp': gbp, 'mbp': mbp, 'msp': msp, 'gsp': gsp},
            'chp_cost': chp_cost
        }
    
    def _calculate_reward(self, energy_data):
        """Calculate reward as negative cost"""
        total_deficit = energy_data['total_deficit']
        total_surplus = energy_data['total_surplus']
        prices = energy_data['prices']
        
        # Cost components
        grid_purchase_cost = 0.0
        grid_sale_revenue = 0.0
        unmet_demand_cost = 0.0
        constraint_penalty = 0.0
        
        # Trading cost
        if total_deficit > total_surplus:
            # Need to buy from grid
            unmet_deficit = total_deficit - total_surplus
            grid_purchase_cost = unmet_deficit * prices['mbp']
            
            # Revenue from internal trading
            grid_sale_revenue = total_surplus * prices['msp']
        
        else:
            # Surplus > deficit, sell excess to grid
            excess_surplus = total_surplus - total_deficit
            grid_sale_revenue = excess_surplus * prices['gsp']
            
            # Cost for internal procurement
            grid_purchase_cost = total_deficit * prices['mbp']
        
        # Penalty for ESS/EV constraint violations
        for key, level in self.ESS_EV_status.items():
            max_cap = self.config.ESS_MAX if key in ['com1', 'com2', 'camp'] else self.config.EV_MAX
            
            if level < 0 or level > max_cap:
                constraint_penalty += self.config.CONSTRAINT_PENALTY
        
        # Total cost (negative reward)
        total_cost = grid_purchase_cost - grid_sale_revenue + constraint_penalty
        
        # Reward is negative cost (we want to minimize cost = maximize reward)
        reward = -total_cost
        
        cost_breakdown = {
            'total_cost': total_cost,
            'grid_purchase': grid_purchase_cost,
            'grid_revenue': grid_sale_revenue,
            'constraint_penalty': constraint_penalty,
            'net_energy_cost': grid_purchase_cost - grid_sale_revenue
        }
        
        return reward, cost_breakdown
    
    def _get_observation(self):
        """Get current state observation"""
        i = min(self.current_step, len(self.data) - 1)
        
        # Build state dictionary
        state_dict = {
            # ESS/EV levels
            'com1_ess': self.ESS_EV_status['com1'],
            'com2_ess': self.ESS_EV_status['com2'],
            'camp_ess': self.ESS_EV_status['camp'],
            'sd1_ev': self.ESS_EV_status['sd1'],
            'sd2_ev': self.ESS_EV_status['sd2'],
            'sd3_ev': self.ESS_EV_status['sd3'],
            
            # Loads for all 8 MGs
            'load_mg1': self.data.loc[i, 'IL1'],
            'load_mg2': self.data.loc[i, 'IL2'],
            'load_mg3': self.data.loc[i, 'CL3'],
            'load_mg4': self.data.loc[i, 'CL4'],
            'load_mg5': self.data.loc[i, 'SL5'],
            'load_mg6': self.data.loc[i, 'SL6'],
            'load_mg7': self.data.loc[i, 'SL7'],
            'load_mg8': self.data.loc[i, 'CPL8'],
            
            # PV generation for all 8 MGs
            'pv_mg1': self.data.loc[i, 'IP1'],
            'pv_mg2': self.data.loc[i, 'IP2'],
            'pv_mg3': self.data.loc[i, 'CP3'],
            'pv_mg4': self.data.loc[i, 'CP4'],
            'pv_mg5': self.data.loc[i, 'SP5'],
            'pv_mg6': self.data.loc[i, 'SP6'],
            'pv_mg7': self.data.loc[i, 'SP7'],
            'pv_mg8': self.data.loc[i, 'CPP8'],
            
            # Prices
            'gbp': self.data.loc[i, 'GBP'],
            'mbp': self.data.loc[i, 'MBP'],
            'msp': self.data.loc[i, 'MSP'],
            'gsp': self.data.loc[i, 'GSP'],
            
            # Time features
            'time_of_day': i % 24,
            'day_of_week': (i // 24) % 7,
            
            # Energy balance (calculated on-the-fly)
            'total_deficit': 0.0,  # Will be updated
            'total_surplus': 0.0,  # Will be updated
            'stress': 0.5  # Default value
        }
        
        # Calculate current energy balance for state
        energy_data = self._calculate_energy_balance()
        state_dict['total_deficit'] = energy_data['total_deficit']
        state_dict['total_surplus'] = energy_data['total_surplus']
        state_dict['stress'] = energy_data['total_surplus'] / (energy_data['total_deficit'] + 1e-6)
        
        # Normalize state using config function
        observation = np.array(self.config.normalize_state(state_dict), dtype=np.float32)
        
        return observation
    
    def render(self):
        """Render the environment (optional)"""
        print(f"Step: {self.current_step}, Episode Cost: {self.episode_cost:.2f}")
        print(f"ESS/EV Status: {self.ESS_EV_status}")
