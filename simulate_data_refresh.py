"""
Simulate Data Refresh for Dashboard Testing
============================================

This script simulates new data arriving by:
1. Loading existing extracted data
2. Adding new synthetic customers
3. Saving to the refreshed data location
4. Updating version metadata

This lets you test dashboard refresh without SingleStore connection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from pathlib import Path

def generate_new_customers(n_customers: int = 100) -> pd.DataFrame:
    """Generate additional synthetic customers."""
    
    print(f"\n🔄 Generating {n_customers} new customers...")
    
    # Set random seed based on time for variety
    np.random.seed(int(datetime.now().timestamp()) % 10000)
    random.seed(int(datetime.now().timestamp()) % 10000)
    
    # Base date
    base_date = datetime.now() - timedelta(days=365)
    
    customers = []
    
    for i in range(n_customers):
        # Generate random customer data matching expected schema
        customer = {
            # Customer info
            'customer_id': f'CTEST{i+1000:06d}',
            'customer_name': f'Test Customer {i+1000}',
            'senior_citizen': random.choice([0, 1]),
            
            # Tenure
            'tenure_months': random.randint(1, 72),
            
            # Contract
            'contract_type': random.choice(['Monthly', 'Yearly', 'Two-Year']),
            
            # Services
            'internet_service': random.choice(['DSL', 'Fiber Optic', 'No']),
            'online_security': random.choice([0, 1]),
            'online_backup': random.choice([0, 1]),
            'device_protection': random.choice([0, 1]),
            'tech_support': random.choice([0, 1]),
            'streaming_tv': random.choice([0, 1]),
            'streaming_movies': random.choice([0, 1]),
            
            # Billing
            'monthly_charges': round(random.uniform(20, 120), 2),
            'paperless_billing': random.choice([0, 1]),
            'payment_method': random.choice(['Electronic', 'Mailed Check', 'Bank Transfer', 'Credit Card']),
            
            # Support
            'service_calls_30d': random.choice([0, 0, 0, 1, 1, 2, 3]),  # Most have 0-1
            
            # Status
            'status': random.choice(['active', 'active', 'active', 'active', 'inactive']),  # 80% active
        }
        
        # Calculate total charges based on tenure
        customer['total_charges'] = round(
            customer['monthly_charges'] * customer['tenure_months'],
            2
        )
        
        customers.append(customer)
    
    df = pd.DataFrame(customers)
    print(f"✅ Generated {len(df)} new customers")
    
    return df


def simulate_refresh():
    """Simulate data refresh by adding new customers to existing data."""
    
    print("\n" + "="*70)
    print("🔄 SIMULATING DATA REFRESH")
    print("="*70)
    
    # Check if we have existing data
    data_dir = Path('./data/refreshed')
    latest_file = data_dir / 'customer_data_latest.csv'
    versions_file = data_dir / 'customer_data_versions.json'
    
    if latest_file.exists():
        print(f"\n📂 Loading existing data from: {latest_file}")
        existing_df = pd.read_csv(latest_file)
        print(f"   Current customers: {len(existing_df)}")
        
        # Find max customer_id to avoid conflicts
        existing_ids = existing_df['customer_id'].astype(str)
        numeric_ids = [int(cid[1:]) for cid in existing_ids if cid.startswith('C') and cid[1:].isdigit()]
        max_id = max(numeric_ids) if numeric_ids else 0
        print(f"   Max customer_id: C{max_id:06d}")
    else:
        print(f"\n⚠️  No existing data found at: {latest_file}")
        print("   Creating new dataset from scratch...")
        existing_df = pd.DataFrame()
        max_id = 0
    
    # Generate new customers
    new_df = generate_new_customers(n_customers=100)
    
    # Update customer IDs to avoid conflicts
    old_to_new_id = {}
    for idx, old_id in enumerate(new_df['customer_id']):
        new_numeric_id = max_id + idx + 1
        new_id = f'C{new_numeric_id:06d}'
        old_to_new_id[old_id] = new_id
    
    new_df['customer_id'] = new_df['customer_id'].map(old_to_new_id)
    
    # Combine with existing data
    if not existing_df.empty:
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"\n✅ Combined data: {len(existing_df)} existing + {len(new_df)} new = {len(combined_df)} total")
    else:
        combined_df = new_df
        print(f"\n✅ Created new dataset: {len(combined_df)} customers")
    
    # Save timestamped version
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_file = data_dir / f'customer_data_{timestamp}.csv'
    combined_df.to_csv(timestamped_file, index=False)
    print(f"\n💾 Saved timestamped version: {timestamped_file.name}")
    
    # Save as latest
    combined_df.to_csv(latest_file, index=False)
    print(f"💾 Updated latest file: {latest_file.name}")
    
    # Update version metadata
    version_info = {
        'version': timestamp,
        'timestamp': datetime.now().isoformat(),
        'total_customers': len(combined_df),
        'new_customers_added': len(new_df),
        'active_customers': len(combined_df[combined_df['status'] == 'active']),
        'file_path': str(timestamped_file),
        'quality_score': None  # Will be filled by data validation
    }
    
    # Load existing versions or create new
    if versions_file.exists():
        with open(versions_file, 'r') as f:
            versions_data = json.load(f)
            # Handle both list and dict formats
            if isinstance(versions_data, list):
                versions = versions_data
            elif isinstance(versions_data, dict) and 'versions' in versions_data:
                versions = versions_data['versions']
            else:
                versions = []
    else:
        versions = []
    
    # Add new version
    versions.append(version_info)
    
    # Keep only last 100 versions
    versions = versions[-100:]
    
    # Save versions
    with open(versions_file, 'w') as f:
        json.dump(versions, f, indent=2)
    
    print(f"📋 Updated version metadata (Total versions: {len(versions)})")
    
    # Display summary
    print("\n" + "="*70)
    print("📊 DATA REFRESH SUMMARY")
    print("="*70)
    print(f"  Total Customers:    {len(combined_df):6,}")
    print(f"  Active Customers:   {len(combined_df[combined_df['status'] == 'active']):6,}")
    print(f"  New Customers:      {len(new_df):6,}")
    print(f"  Timestamp:          {timestamp}")
    print(f"  File:               {latest_file.name}")
    
    # Show sample of new customers
    print("\n📋 Sample of New Customers:")
    print("-" * 70)
    sample = new_df.head(5)[['customer_id', 'customer_name', 'tenure_months', 
                              'monthly_charges', 'contract_type', 'status']]
    print(sample.to_string(index=False))
    
    print("\n" + "="*70)
    print("🎉 REFRESH COMPLETE!")
    print("="*70)
    print("\nTo see the new data in the dashboard:")
    print("  1. Clear cache: Click 'Refresh Data' button in sidebar")
    print("  2. Or restart Streamlit: Ctrl+C then 'streamlit run dashboard.py'")
    print("  3. The dashboard cache expires after 1 hour automatically")
    print("\n💡 Note: This simulates a refresh without connecting to SingleStore.")
    print("   In production, the data_refresh.py job pulls from the database.\n")


if __name__ == '__main__':
    simulate_refresh()
