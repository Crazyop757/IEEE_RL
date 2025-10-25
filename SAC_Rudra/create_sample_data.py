# Script to create sample input data for SAC training
# This creates a Data_for_Qcode.csv file with 24 hours of sample data

import pandas as pd
import numpy as np

def create_sample_data(output_file='Data_for_Qcode.csv'):
    """Create sample input data for microgrid energy management"""
    
    np.random.seed(42)
    hours = 24
    
    # Create time-based patterns
    hours_array = np.arange(1, hours + 1)
    
    # Load patterns (higher during day, lower at night) - FIXED for realistic daily pattern
    # Peak loads during morning (8-10am) and evening (6-9pm)
    load_pattern = np.zeros(hours)
    for h in range(hours):
        hour_of_day = hours_array[h]
        if 6 <= hour_of_day <= 9:  # Morning peak
            load_pattern[h] = 120 + 30 * (hour_of_day - 6) / 3
        elif 9 <= hour_of_day <= 17:  # Daytime
            load_pattern[h] = 150
        elif 17 <= hour_of_day <= 21:  # Evening peak
            load_pattern[h] = 140 + 20 * np.sin((hour_of_day - 17) * np.pi / 4)
        else:  # Night
            load_pattern[h] = 60 + 20 * np.random.random()
    load_pattern = load_pattern + np.random.normal(0, 10, hours)
    load_pattern = np.clip(load_pattern, 40, 200)
    
    # PV generation (peak at noon, zero at night) - FIXED to actually generate during day
    # PV active from 6am (hour 6) to 6pm (hour 18)
    pv_pattern = np.zeros(hours)
    for h in range(hours):
        hour_of_day = hours_array[h]
        if 6 <= hour_of_day <= 18:  # Daytime hours
            # Peak at noon (hour 12)
            solar_intensity = np.sin((hour_of_day - 6) * np.pi / 12)
            pv_pattern[h] = 120 * solar_intensity + np.random.normal(0, 10)
        else:
            pv_pattern[h] = 0  # No solar at night
    pv_pattern = np.clip(pv_pattern, 0, 200)
    
    # Price patterns (higher during peak hours)
    price_pattern = 6.0 + 2.0 * np.sin((hours_array - 8) * np.pi / 12)
    
    data = {
        'Hour': hours_array,
        
        # Industrial loads and PV (2 microgrids)
        'IL1': (load_pattern * 1.2).astype(int),
        'IP1': (pv_pattern * 0.4).astype(int),
        'IL2': (load_pattern * 1.3).astype(int),
        'IP2': (pv_pattern * 0.5).astype(int),
        
        # Community loads and PV (2 microgrids)
        'CL3': (load_pattern * 0.8).astype(int),
        'CP3': (pv_pattern * 0.7).astype(int),
        'CL4': (load_pattern * 0.9).astype(int),
        'CP4': (pv_pattern * 0.8).astype(int),
        
        # Single-Dwelling loads and PV (3 microgrids)
        'SL5': (load_pattern * 0.3).astype(int),
        'SP5': (pv_pattern * 0.3).astype(int),
        'SL6': (load_pattern * 0.35).astype(int),
        'SP6': (pv_pattern * 0.35).astype(int),
        'SL7': (load_pattern * 0.4).astype(int),
        'SP7': (pv_pattern * 0.4).astype(int),
        
        # Campus load and PV (1 microgrid)
        'CPL8': (load_pattern * 1.5).astype(int),
        'CPP8': (pv_pattern * 1.2).astype(int),
        
        # Prices (Rs/kWh)
        'GBP': np.round(price_pattern + 1.0, 2),  # Grid Buy Price
        'MBP': np.round(price_pattern, 2),         # Market Buy Price
        'MSP': np.round(price_pattern - 1.5, 2),   # Market Sell Price
        'GSP': np.round(price_pattern - 2.0, 2),   # Grid Sell Price
        
        # CHP Cost (Rs/kWh)
        'CHP_Cost': np.round(5.5 + 0.5 * np.random.random(hours), 2),
        
        # EV Availability (1 if at home, 0 if away)
        # Typically at home during night and evening
        'EV_Avail': [1 if (h < 8 or h > 17) else 0 for h in hours_array]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Sample data created: {output_file}")
    print(f"Shape: {df.shape}")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nColumns: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    # Create sample data in both directories
    import os
    
    # Create in SAC_Rudra directory
    sac_file = os.path.join(os.path.dirname(__file__), 'Data_for_Qcode.csv')
    df = create_sample_data(sac_file)
    
    # Also create in Code_QLearning directory
    qlearning_dir = os.path.join(os.path.dirname(__file__), '..', 'Code_QLearning')
    if os.path.exists(qlearning_dir):
        qlearning_file = os.path.join(qlearning_dir, 'Data_for_Qcode.csv')
        df.to_csv(qlearning_file, index=False)
        print(f"\nAlso created: {qlearning_file}")
    
    print("\n✓ Sample data files created successfully!")
