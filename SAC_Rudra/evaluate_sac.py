# Evaluation and Comparison Script for SAC vs Q-Learning

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sac_config import SACConfig
from sac_agent import SACAgent
from microgrid_env import MicrogridEnv

def evaluate_sac_agent(model_path, num_episodes=10):
    """Evaluate trained SAC agent"""
    config = SACConfig()
    env = MicrogridEnv(config.DATA_PATH, config)
    agent = SACAgent(config)
    
    # Load trained model
    agent.load(model_path)
    print(f"Loaded model from {model_path}")
    
    # Evaluation metrics
    episode_rewards = []
    episode_costs = []
    ess_utilization = []
    ev_utilization = []
    constraint_violations = []
    
    print("\n" + "="*60)
    print("Evaluating SAC Agent")
    print("="*60)
    
    for episode in range(num_episodes):
        state, _ = env.reset()
        episode_reward = 0
        episode_cost = 0
        violations = 0
        
        ess_levels = []
        ev_levels = []
        
        for step in range(24):  # 24 hourly time steps
            # Get action from policy
            action = agent.select_action(state, deterministic=True)
            
            # Execute action
            next_state, reward, terminated, truncated, info = env.step(action)
            
            # Track metrics
            episode_reward += reward
            episode_cost += info['cost_breakdown']['total_cost']
            
            # Track ESS/EV utilization
            ess_status = info['ESS_EV_status']
            ess_avg = np.mean([ess_status['com1'], ess_status['com2'], ess_status['camp']]) / config.ESS_MAX
            ev_avg = np.mean([ess_status['sd1'], ess_status['sd2'], ess_status['sd3']]) / config.EV_MAX
            
            ess_levels.append(ess_avg)
            ev_levels.append(ev_avg)
            
            # Check constraints
            if info['cost_breakdown']['constraint_penalty'] != 0:
                violations += 1
            
            state = next_state
            
            if terminated or truncated:
                break
        
        # Store episode metrics
        episode_rewards.append(episode_reward)
        episode_costs.append(episode_cost)
        ess_utilization.append(np.mean(ess_levels))
        ev_utilization.append(np.mean(ev_levels))
        constraint_violations.append(violations)
        
        print(f"Episode {episode+1}: Reward={episode_reward:.2f}, Cost=${episode_cost:.2f}, Violations={violations}")
    
    # Compute statistics
    results = {
        'mean_reward': np.mean(episode_rewards),
        'std_reward': np.std(episode_rewards),
        'mean_cost': np.mean(episode_costs),
        'std_cost': np.std(episode_costs),
        'mean_ess_util': np.mean(ess_utilization) * 100,
        'mean_ev_util': np.mean(ev_utilization) * 100,
        'total_violations': np.sum(constraint_violations),
        'violation_rate': np.sum(constraint_violations) / (num_episodes * 24) * 100
    }
    
    print("\n" + "="*60)
    print("SAC Evaluation Results")
    print("="*60)
    print(f"Average Reward: {results['mean_reward']:.2f} ± {results['std_reward']:.2f}")
    print(f"Average Cost: ${results['mean_cost']:.2f} ± {results['std_cost']:.2f}")
    print(f"ESS Utilization: {results['mean_ess_util']:.1f}%")
    print(f"EV Utilization: {results['mean_ev_util']:.1f}%")
    print(f"Constraint Violations: {results['total_violations']} ({results['violation_rate']:.2f}%)")
    print("="*60)
    
    return results, episode_rewards, episode_costs

def load_qlearning_results(qlearning_csv_path):
    """Load Q-Learning baseline results from CSV"""
    try:
        # Handle relative paths
        import os
        if not os.path.isabs(qlearning_csv_path):
            qlearning_csv_path = os.path.join(os.path.dirname(__file__), qlearning_csv_path)
        
        df = pd.read_csv(qlearning_csv_path)
        
        # Extract relevant columns (adjust based on your CSV structure)
        # Assuming your AnalysisOfImplementation_v7.csv has cost information
        
        results = {
            'mean_cost': df['total_cost'].mean() if 'total_cost' in df.columns else None,
            'std_cost': df['total_cost'].std() if 'total_cost' in df.columns else None,
        }
        
        print("\n" + "="*60)
        print("Q-Learning Baseline Results (from CSV)")
        print("="*60)
        print(f"Average Cost: ${results['mean_cost']:.2f} ± {results['std_cost']:.2f}")
        print("="*60)
        
        return results
    
    except Exception as e:
        print(f"Could not load Q-Learning results: {e}")
        return None

def compare_algorithms(sac_results, qlearning_results):
    """Compare SAC vs Q-Learning performance"""
    print("\n" + "="*80)
    print("SAC vs Q-Learning Comparison")
    print("="*80)
    
    if qlearning_results and qlearning_results['mean_cost'] is not None:
        sac_cost = sac_results['mean_cost']
        ql_cost = qlearning_results['mean_cost']
        
        cost_improvement = ((ql_cost - sac_cost) / ql_cost) * 100
        
        print(f"{'Metric':<30} {'Q-Learning':<20} {'SAC':<20} {'Improvement':<15}")
        print("-"*80)
        print(f"{'Average Cost ($)':<30} {ql_cost:<20.2f} {sac_cost:<20.2f} {cost_improvement:>12.2f}%")
        print(f"{'ESS Utilization (%)':<30} {'N/A':<20} {sac_results['mean_ess_util']:<20.1f} {'N/A':<15}")
        print(f"{'EV Utilization (%)':<30} {'N/A':<20} {sac_results['mean_ev_util']:<20.1f} {'N/A':<15}")
        print(f"{'Constraint Violations':<30} {'N/A':<20} {sac_results['total_violations']:<20} {'N/A':<15}")
        
        print("\n" + "="*80)
        print(f"SAC achieves {cost_improvement:.2f}% cost reduction compared to Q-Learning!")
        print("="*80)
    else:
        print("Q-Learning results not available for comparison.")
        print("\nSAC Standalone Results:")
        print(f"  Average Cost: ${sac_results['mean_cost']:.2f}")
        print(f"  ESS Utilization: {sac_results['mean_ess_util']:.1f}%")
        print(f"  EV Utilization: {sac_results['mean_ev_util']:.1f}%")

def plot_comparison(sac_costs, qlearning_costs=None, save_path='./comparison.png'):
    """Plot cost comparison between algorithms"""
    plt.figure(figsize=(12, 6))
    
    if qlearning_costs is not None:
        plt.subplot(1, 2, 1)
        plt.plot(qlearning_costs, label='Q-Learning', color='red', alpha=0.7)
        plt.plot(sac_costs, label='SAC', color='blue', alpha=0.7)
        plt.xlabel('Episode')
        plt.ylabel('Total Cost ($)')
        plt.title('Cost Comparison: SAC vs Q-Learning')
        plt.legend()
        plt.grid(True)
        
        plt.subplot(1, 2, 2)
    else:
        plt.subplot(1, 1, 1)
    
    # Plot SAC cost distribution
    plt.hist(sac_costs, bins=20, alpha=0.7, color='blue', edgecolor='black')
    plt.xlabel('Total Cost ($)')
    plt.ylabel('Frequency')
    plt.title('SAC Cost Distribution')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"\nComparison plot saved to {save_path}")
    plt.close()

def main():
    """Main evaluation pipeline"""
    # Paths (use relative paths)
    sac_model_path = './models/sac_microgrid/sac_final.pt'
    qlearning_results_path = r'..\Code_QLearning\AnalysisOfImplementation_v7.csv'  # Relative path
    
    # Evaluate SAC
    print("Starting evaluation...")
    sac_results, sac_rewards, sac_costs = evaluate_sac_agent(sac_model_path, num_episodes=20)
    
    # Load Q-Learning baseline
    qlearning_results = load_qlearning_results(qlearning_results_path)
    
    # Compare
    compare_algorithms(sac_results, qlearning_results)
    
    # Plot
    plot_comparison(sac_costs, save_path='./logs/sac_vs_qlearning.png')
    
    # Save results to CSV
    results_df = pd.DataFrame({
        'Episode': range(1, len(sac_costs) + 1),
        'SAC_Cost': sac_costs,
        'SAC_Reward': sac_rewards
    })
    results_df.to_csv('./logs/sac_evaluation_results.csv', index=False)
    print("\nResults saved to ./logs/sac_evaluation_results.csv")

if __name__ == "__main__":
    main()
