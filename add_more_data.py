"""
Add More Synthetic Data to SingleStore
========================================

This script adds additional customers to the existing database
without dropping or recreating tables.
"""

import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

def add_synthetic_data(data_dir: str = './synthetic_data_new'):
    """Insert additional synthetic data into SingleStore."""
    
    print("\n" + "="*70)
    print("📥 ADDING MORE SYNTHETIC DATA TO SINGLESTORE")
    print("="*70)
    
    # Create connection string
    conn_str = (
        f"mysql+pymysql://{os.getenv('SINGLESTORE_USER')}:"
        f"{os.getenv('SINGLESTORE_PASSWORD')}@"
        f"{os.getenv('SINGLESTORE_HOST')}:"
        f"{os.getenv('SINGLESTORE_PORT')}/"
        f"{os.getenv('SINGLESTORE_DATABASE')}"
    )
    
    try:
        engine = create_engine(conn_str)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connected to SingleStore successfully!\n")
        
        output_path = Path(data_dir)
        
        # Get current max customer_id to generate new IDs
        with engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(customer_id) as max_id FROM customers"))
            max_id = result.fetchone()[0]
            
            if max_id:
                # Extract numeric part (e.g., 'C001000' -> 1000)
                current_max = int(max_id[1:])
                print(f"📊 Current max customer_id: {max_id} ({current_max})")
            else:
                current_max = 0
                print(f"📊 No existing customers, starting from C000001")
        
        # Insert data for each table
        tables = ['customers', 'billing', 'contracts', 'customer_features', 
                  'payment_methods', 'service_calls', 'churn_history']
        
        for table in tables:
            csv_file = output_path / f'{table}.csv'
            
            if not csv_file.exists():
                print(f"  ⚠️  Skipping {table} - file not found")
                continue
            
            df = pd.read_csv(csv_file)
            
            # Update customer_ids to avoid conflicts
            if 'customer_id' in df.columns:
                # Create new customer IDs
                old_to_new_id = {}
                for idx, old_id in enumerate(df['customer_id'].unique()):
                    new_numeric_id = current_max + idx + 1
                    new_id = f'C{new_numeric_id:06d}'
                    old_to_new_id[old_id] = new_id
                
                # Replace IDs
                df['customer_id'] = df['customer_id'].map(old_to_new_id)
            
            # Drop timestamp columns that have defaults
            cols_to_drop = ['created_at', 'updated_at']
            df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')
            
            # Drop auto-increment IDs
            if table == 'billing' and 'billing_id' in df.columns:
                df = df.drop(columns=['billing_id'])
            elif table == 'service_calls' and 'service_call_id' in df.columns:
                df = df.drop(columns=['service_call_id'])
            elif table == 'contracts' and 'contract_id' in df.columns:
                df = df.drop(columns=['contract_id'])
            elif table == 'customer_features' and 'feature_id' in df.columns:
                df = df.drop(columns=['feature_id'])
            elif table == 'payment_methods' and 'payment_id' in df.columns:
                df = df.drop(columns=['payment_id'])
            elif table == 'churn_history' and 'churn_id' in df.columns:
                df = df.drop(columns=['churn_id'])
            
            # Insert data
            try:
                df.to_sql(table, engine, if_exists='append', index=False)
                print(f"  ✅ Inserted {len(df)} rows into {table}")
            except Exception as e:
                print(f"  ❌ Error inserting into {table}: {e}")
        
        # Show updated counts
        print("\n📊 Updated Database Statistics:")
        print("-" * 70)
        
        with engine.connect() as conn:
            tables_to_count = [
                'customers', 'billing', 'contracts', 'customer_features',
                'payment_methods', 'service_calls', 'churn_history'
            ]
            
            for table in tables_to_count:
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                count = result.fetchone()[0]
                print(f"  {table:25s}: {count:6,} rows")
        
        print("\n" + "="*70)
        print("🎉 DATA ADDED SUCCESSFULLY!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Clear dashboard cache: Delete browser cache or wait 1 hour")
        print("  2. Or manually refresh: Click 'Refresh Data' button in dashboard")
        print("  3. Or restart Streamlit: Ctrl+C and run 'streamlit run dashboard.py'")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    add_synthetic_data()
