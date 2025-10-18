# SAC Agent Implementation for Multi-Microgrid Energy Management
# This replaces the Q-Learning algorithm

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Normal
import numpy as np

class ReplayBuffer:
    """Experience replay buffer for off-policy learning"""
    def __init__(self, state_dim, action_dim, max_size=200000):
        self.max_size = max_size
        self.ptr = 0
        self.size = 0
        
        self.states = np.zeros((max_size, state_dim), dtype=np.float32)
        self.actions = np.zeros((max_size, action_dim), dtype=np.float32)
        self.rewards = np.zeros((max_size, 1), dtype=np.float32)
        self.next_states = np.zeros((max_size, state_dim), dtype=np.float32)
        self.dones = np.zeros((max_size, 1), dtype=np.float32)
    
    def add(self, state, action, reward, next_state, done):
        self.states[self.ptr] = state
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.next_states[self.ptr] = next_state
        self.dones[self.ptr] = done
        
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)
    
    def sample(self, batch_size):
        idx = np.random.randint(0, self.size, size=batch_size)
        
        return (
            torch.FloatTensor(self.states[idx]),
            torch.FloatTensor(self.actions[idx]),
            torch.FloatTensor(self.rewards[idx]),
            torch.FloatTensor(self.next_states[idx]),
            torch.FloatTensor(self.dones[idx])
        )

class Actor(nn.Module):
    """Gaussian policy network (stochastic actor)"""
    def __init__(self, state_dim, action_dim, hidden_dim=256, log_std_min=-20, log_std_max=2):
        super(Actor, self).__init__()
        
        self.log_std_min = log_std_min
        self.log_std_max = log_std_max
        
        # Shared feature extraction layers
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Separate heads for mean and log_std
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std_head = nn.Linear(hidden_dim, action_dim)
    
    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        
        mean = self.mean_head(x)
        log_std = self.log_std_head(x)
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        
        return mean, log_std
    
    def sample(self, state):
        """Sample action with reparameterization trick"""
        mean, log_std = self.forward(state)
        std = log_std.exp()
        
        # Reparameterization trick
        normal = Normal(mean, std)
        x_t = normal.rsample()  # Sample with gradients
        
        # Apply tanh squashing to bound actions to [-1, 1]
        action = torch.tanh(x_t)
        
        # Calculate log probability with correction for tanh
        log_prob = normal.log_prob(x_t)
        log_prob -= torch.log(1 - action.pow(2) + 1e-6)
        log_prob = log_prob.sum(1, keepdim=True)
        
        return action, log_prob
    
    def get_action(self, state, deterministic=False):
        """Get action for deployment (no gradient)"""
        with torch.no_grad():
            mean, log_std = self.forward(state)
            
            if deterministic:
                action = torch.tanh(mean)
            else:
                std = log_std.exp()
                normal = Normal(mean, std)
                x_t = normal.sample()
                action = torch.tanh(x_t)
            
            return action.cpu().numpy()

class Critic(nn.Module):
    """Q-network (critic) for estimating Q-values"""
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(Critic, self).__init__()
        
        # Q1 network
        self.q1_fc1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.q1_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.q1_out = nn.Linear(hidden_dim, 1)
        
        # Q2 network (twin critic)
        self.q2_fc1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.q2_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.q2_out = nn.Linear(hidden_dim, 1)
    
    def forward(self, state, action):
        """Forward pass for both Q-networks"""
        x = torch.cat([state, action], dim=1)
        
        # Q1
        q1 = F.relu(self.q1_fc1(x))
        q1 = F.relu(self.q1_fc2(q1))
        q1 = self.q1_out(q1)
        
        # Q2
        q2 = F.relu(self.q2_fc1(x))
        q2 = F.relu(self.q2_fc2(q2))
        q2 = self.q2_out(q2)
        
        return q1, q2

class SACAgent:
    """Soft Actor-Critic Agent for Microgrid Energy Management"""
    def __init__(self, config):
        self.config = config
        self.device = config.DEVICE
        
        # Initialize networks
        self.actor = Actor(config.STATE_DIM, config.ACTION_DIM, config.HIDDEN_DIM).to(self.device)
        self.critic = Critic(config.STATE_DIM, config.ACTION_DIM, config.HIDDEN_DIM).to(self.device)
        self.critic_target = Critic(config.STATE_DIM, config.ACTION_DIM, config.HIDDEN_DIM).to(self.device)
        
        # Copy parameters to target network
        self.critic_target.load_state_dict(self.critic.state_dict())
        
        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=config.ACTOR_LR)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=config.CRITIC_LR)
        
        # Entropy temperature (alpha)
        if config.AUTO_ENTROPY:
            self.target_entropy = config.TARGET_ENTROPY
            self.log_alpha = torch.zeros(1, requires_grad=True, device=self.device)
            self.alpha_optimizer = optim.Adam([self.log_alpha], lr=config.ALPHA_LR)
            self.alpha = self.log_alpha.exp()
        else:
            self.alpha = torch.tensor(config.INITIAL_ALPHA).to(self.device)
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(config.STATE_DIM, config.ACTION_DIM, config.BUFFER_SIZE)
        
        # Training statistics
        self.total_steps = 0
        self.actor_losses = []
        self.critic_losses = []
        self.alpha_values = []
    
    def select_action(self, state, deterministic=False):
        """Select action using current policy"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        action = self.actor.get_action(state_tensor, deterministic)
        return action[0]
    
    def update(self, batch_size):
        """Update SAC networks using a batch from replay buffer"""
        if self.replay_buffer.size < batch_size:
            return None, None, None
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        
        # ========== Update Critic ==========
        with torch.no_grad():
            # Sample actions for next states
            next_actions, next_log_probs = self.actor.sample(next_states)
            
            # Compute target Q-values (minimum of two critics)
            q1_next, q2_next = self.critic_target(next_states, next_actions)
            q_next = torch.min(q1_next, q2_next)
            
            # Compute target with entropy term
            target_q = rewards + (1 - dones) * self.config.GAMMA * (q_next - self.alpha * next_log_probs)
        
        # Current Q-values
        q1, q2 = self.critic(states, actions)
        
        # Critic loss (MSE)
        critic_loss = F.mse_loss(q1, target_q) + F.mse_loss(q2, target_q)
        
        # Update critic
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()
        
        # ========== Update Actor ==========
        # Sample new actions
        new_actions, log_probs = self.actor.sample(states)
        
        # Compute Q-values for new actions
        q1_new, q2_new = self.critic(states, new_actions)
        q_new = torch.min(q1_new, q2_new)
        
        # Actor loss (maximize Q - alpha * log_prob)
        actor_loss = (self.alpha * log_probs - q_new).mean()
        
        # Update actor
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()
        
        # ========== Update Alpha (Entropy Temperature) ==========
        if self.config.AUTO_ENTROPY:
            alpha_loss = -(self.log_alpha * (log_probs + self.target_entropy).detach()).mean()
            
            self.alpha_optimizer.zero_grad()
            alpha_loss.backward()
            self.alpha_optimizer.step()
            
            self.alpha = self.log_alpha.exp()
        
        # ========== Soft Update Target Network ==========
        for target_param, param in zip(self.critic_target.parameters(), self.critic.parameters()):
            target_param.data.copy_(self.config.TAU * param.data + (1 - self.config.TAU) * target_param.data)
        
        # Store statistics
        self.actor_losses.append(actor_loss.item())
        self.critic_losses.append(critic_loss.item())
        self.alpha_values.append(self.alpha.item())
        
        return actor_loss.item(), critic_loss.item(), self.alpha.item()
    
    def save(self, filepath):
        """Save model checkpoints"""
        torch.save({
            'actor_state_dict': self.actor.state_dict(),
            'critic_state_dict': self.critic.state_dict(),
            'critic_target_state_dict': self.critic_target.state_dict(),
            'actor_optimizer_state_dict': self.actor_optimizer.state_dict(),
            'critic_optimizer_state_dict': self.critic_optimizer.state_dict(),
            'log_alpha': self.log_alpha if self.config.AUTO_ENTROPY else None,
            'total_steps': self.total_steps
        }, filepath)
    
    def load(self, filepath):
        """Load model checkpoints"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.actor.load_state_dict(checkpoint['actor_state_dict'])
        self.critic.load_state_dict(checkpoint['critic_state_dict'])
        self.critic_target.load_state_dict(checkpoint['critic_target_state_dict'])
        self.actor_optimizer.load_state_dict(checkpoint['actor_optimizer_state_dict'])
        self.critic_optimizer.load_state_dict(checkpoint['critic_optimizer_state_dict'])
        
        if self.config.AUTO_ENTROPY and checkpoint['log_alpha'] is not None:
            self.log_alpha.data = checkpoint['log_alpha'].data
            self.alpha = self.log_alpha.exp()
        
        self.total_steps = checkpoint['total_steps']
