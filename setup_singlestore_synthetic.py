"""
SingleStore Setup and Synthetic Data Generator
===============================================

This script helps you:
1. Configure SingleStore connection with test credentials
2. Generate synthetic customer data that matches the expected schema
3. Create the required database tables
4. Populate tables with realistic test data

Usage:
    # Generate synthetic data only
    python setup_singlestore_synthetic.py --generate-data

    # Create tables (requires SingleStore connection)
    python setup_singlestore_synthetic.py --create-tables

    # Full setup (create tables and insert data)
    python setup_singlestore_synthetic.py --full-setup
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import argparse
import json
from pathlib import Path


def generate_synthetic_customers(n_customers: int = 1000) -> dict:
    """
    Generate synthetic customer data that matches SingleStore schema.
    
    Returns a dictionary with DataFrames for each table:
    - customers
    - billing
    - service_calls
    - contracts
    - customer_features
    - payment_methods
    """
    
    print(f"Generating {n_customers} synthetic customers...")
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Base date
    base_date = datetime.now() - timedelta(days=365*3)  # 3 years ago
    
    # ==========================================
    # 1. CUSTOMERS TABLE
    # ==========================================
    customers = pd.DataFrame({
        'customer_id': [f'C{i:06d}' for i in range(1, n_customers + 1)],
        'customer_name': [f'Customer {i}' for i in range(1, n_customers + 1)],
        'signup_date': [
            base_date + timedelta(days=random.randint(0, 1095))
            for _ in range(n_customers)
        ],
        'status': np.random.choice(['active', 'inactive'], n_customers, p=[0.85, 0.15]),
        'senior_citizen': np.random.choice([0, 1], n_customers, p=[0.84, 0.16]),
        'last_contact_date': [
            datetime.now() - timedelta(days=random.randint(0, 90))
            for _ in range(n_customers)
        ],
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    
    # ==========================================
    # 2. BILLING TABLE
    # ==========================================
    billing = pd.DataFrame({
        'billing_id': range(1, n_customers + 1),
        'customer_id': customers['customer_id'],
        'monthly_charges': np.random.uniform(20, 120, n_customers).round(2),
    })
    
    # Calculate tenure for total charges
    today = datetime.now()
    tenure_months = [(today - signup).days / 30 for signup in customers['signup_date']]
    billing['total_charges'] = (billing['monthly_charges'] * tenure_months).round(2)
    
    billing['billing_cycle'] = np.random.choice(
        ['monthly', 'quarterly', 'annual'], 
        n_customers, 
        p=[0.7, 0.2, 0.1]
    )
    billing['last_payment_date'] = customers['last_contact_date']
    billing['created_at'] = datetime.now()
    billing['updated_at'] = datetime.now()
    
    # ==========================================
    # 3. SERVICE CALLS TABLE
    # ==========================================
    # Not all customers have service calls
    n_with_calls = int(n_customers * 0.4)  # 40% have calls
    service_call_customers = np.random.choice(
        customers['customer_id'], 
        n_with_calls, 
        replace=False
    )
    
    service_calls_list = []
    for cust_id in service_call_customers:
        n_calls = np.random.poisson(2) + 1  # Average 2-3 calls
        for _ in range(n_calls):
            service_calls_list.append({
                'customer_id': cust_id,
                'call_date': datetime.now() - timedelta(days=random.randint(0, 90)),
                'issue_type': random.choice([
                    'technical', 'billing', 'service', 'cancellation', 'upgrade'
                ]),
                'resolution_time_hours': np.random.exponential(2),
                'created_at': datetime.now()
            })
    
    service_calls = pd.DataFrame(service_calls_list)
    if not service_calls.empty:
        service_calls['service_call_id'] = range(1, len(service_calls) + 1)
    
    # Aggregate to 30-day window
    service_calls_30d = service_calls[
        service_calls['call_date'] >= (datetime.now() - timedelta(days=30))
    ].groupby('customer_id').size().reset_index(name='service_calls_30d')
    
    # ==========================================
    # 4. CONTRACTS TABLE
    # ==========================================
    contracts = pd.DataFrame({
        'contract_id': range(1, n_customers + 1),
        'customer_id': customers['customer_id'],
        'contract_type': np.random.choice(
            ['month-to-month', 'one year', 'two year'], 
            n_customers, 
            p=[0.55, 0.30, 0.15]
        ),
        'start_date': customers['signup_date'],
    })
    
    # End date based on contract type
    def get_end_date(row):
        if row['contract_type'] == 'month-to-month':
            return None
        elif row['contract_type'] == 'one year':
            return row['start_date'] + timedelta(days=365)
        else:  # two year
            return row['start_date'] + timedelta(days=730)
    
    contracts['end_date'] = contracts.apply(get_end_date, axis=1)
    contracts['auto_renew'] = np.random.choice([0, 1], n_customers, p=[0.3, 0.7])
    contracts['created_at'] = datetime.now()
    contracts['updated_at'] = datetime.now()
    
    # ==========================================
    # 5. CUSTOMER FEATURES TABLE
    # ==========================================
    customer_features = pd.DataFrame({
        'feature_id': range(1, n_customers + 1),
        'customer_id': customers['customer_id'],
        
        # Binary features (0 or 1)
        'paperless_billing_score': np.random.choice([0, 1], n_customers, p=[0.4, 0.6]),
        'tech_support_score': np.random.choice([0, 1], n_customers, p=[0.5, 0.5]),
        'online_backup_score': np.random.choice([0, 1], n_customers, p=[0.55, 0.45]),
        'streaming_tv_score': np.random.choice([0, 1], n_customers, p=[0.5, 0.5]),
        'streaming_movies_score': np.random.choice([0, 1], n_customers, p=[0.5, 0.5]),
        'device_protection_score': np.random.choice([0, 1], n_customers, p=[0.6, 0.4]),
        'online_security_score': np.random.choice([0, 1], n_customers, p=[0.55, 0.45]),
        
        # Internet service (0=no, 1=DSL, 2=Fiber)
        'internet_service_score': np.random.choice([0, 1, 2], n_customers, p=[0.2, 0.35, 0.45]),
        
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    
    # ==========================================
    # 6. PAYMENT METHODS TABLE
    # ==========================================
    payment_methods = pd.DataFrame({
        'payment_id': range(1, n_customers + 1),
        'customer_id': customers['customer_id'],
        'payment_method': np.random.choice(
            ['electronic check', 'mailed check', 'bank transfer', 'credit card'],
            n_customers,
            p=[0.35, 0.15, 0.20, 0.30]
        ),
        'is_auto_pay': np.random.choice([0, 1], n_customers, p=[0.4, 0.6]),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    
    # ==========================================
    # 7. CHURN HISTORY (for training)
    # ==========================================
    # Generate some churned customers
    n_churned = int(n_customers * 0.15)  # 15% churn rate
    churned_indices = np.random.choice(
        range(n_customers), 
        n_churned, 
        replace=False
    )
    
    churn_history = []
    for idx in churned_indices:
        churn_history.append({
            'churn_id': len(churn_history) + 1,
            'customer_id': customers.loc[idx, 'customer_id'],
            'churn_date': customers.loc[idx, 'signup_date'] + timedelta(
                days=random.randint(90, 1095)
            ),
            'churn_reason': random.choice([
                'price', 'service', 'competitor', 'moved', 'other'
            ]),
            'created_at': datetime.now()
        })
    
    churn_history = pd.DataFrame(churn_history)
    
    return {
        'customers': customers,
        'billing': billing,
        'service_calls': service_calls,
        'service_calls_30d': service_calls_30d,
        'contracts': contracts,
        'customer_features': customer_features,
        'payment_methods': payment_methods,
        'churn_history': churn_history
    }


def save_synthetic_data(data_dict: dict, output_dir: str = './synthetic_data'):
    """Save synthetic data to CSV and JSON files."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\nSaving synthetic data to {output_path}...")
    
    for table_name, df in data_dict.items():
        if not df.empty:
            # Save as CSV
            csv_file = output_path / f'{table_name}.csv'
            df.to_csv(csv_file, index=False)
            print(f"  ✅ Saved {table_name}.csv ({len(df)} rows)")
            
            # Save sample as JSON for inspection
            json_file = output_path / f'{table_name}_sample.json'
            df.head(5).to_json(json_file, orient='records', indent=2, date_format='iso')
    
    # Save summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'tables': {
            name: {
                'rows': len(df),
                'columns': list(df.columns)
            }
            for name, df in data_dict.items()
        }
    }
    
    summary_file = output_path / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ All data saved to {output_path}/")
    print(f"📊 Summary saved to {summary_file}")


def generate_sql_schema():
    """Generate SQL schema for SingleStore tables."""
    
    schema_sql = """
-- ============================================================================
-- SingleStore Database Schema for Churn Prediction
-- ============================================================================

-- Use database
USE churn_db;

-- ==========================================
-- 1. CUSTOMERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    signup_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    senior_citizen TINYINT DEFAULT 0,
    last_contact_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_status (status),
    KEY idx_signup_date (signup_date)
);

-- ==========================================
-- 2. BILLING TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS billing (
    billing_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    monthly_charges DECIMAL(10, 2) NOT NULL,
    total_charges DECIMAL(10, 2) NOT NULL,
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    last_payment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id)
);

-- ==========================================
-- 3. SERVICE CALLS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS service_calls (
    service_call_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    call_date DATE NOT NULL,
    issue_type VARCHAR(50),
    resolution_time_hours DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id),
    KEY idx_call_date (call_date)
);

-- ==========================================
-- 4. CONTRACTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS contracts (
    contract_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    contract_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    auto_renew TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id),
    KEY idx_contract_type (contract_type)
);

-- ==========================================
-- 5. CUSTOMER FEATURES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS customer_features (
    feature_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    paperless_billing_score TINYINT DEFAULT 0,
    tech_support_score TINYINT DEFAULT 0,
    online_backup_score TINYINT DEFAULT 0,
    streaming_tv_score TINYINT DEFAULT 0,
    streaming_movies_score TINYINT DEFAULT 0,
    device_protection_score TINYINT DEFAULT 0,
    online_security_score TINYINT DEFAULT 0,
    internet_service_score TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id)
);

-- ==========================================
-- 6. PAYMENT METHODS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS payment_methods (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    is_auto_pay TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id)
);

-- ==========================================
-- 7. CHURN HISTORY TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS churn_history (
    churn_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    churn_date DATE NOT NULL,
    churn_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id),
    KEY idx_churn_date (churn_date)
);

-- ==========================================
-- Create View for 30-day Service Calls
-- ==========================================
CREATE OR REPLACE VIEW service_calls_summary AS
SELECT 
    customer_id,
    COUNT(*) as service_calls_30d
FROM service_calls
WHERE call_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY customer_id;

-- ==========================================
-- Verify Tables Created
-- ==========================================
SHOW TABLES;
"""
    
    return schema_sql


def save_sql_schema(output_file: str = './schema.sql'):
    """Save SQL schema to file."""
    schema = generate_sql_schema()
    
    with open(output_file, 'w') as f:
        f.write(schema)
    
    print(f"✅ SQL schema saved to {output_file}")


def generate_insert_sql(data_dict: dict, output_file: str = './insert_data.sql'):
    """Generate SQL INSERT statements for synthetic data."""
    
    with open(output_file, 'w') as f:
        f.write("-- ============================================================================\n")
        f.write("-- Insert Synthetic Data into SingleStore\n")
        f.write("-- ============================================================================\n\n")
        f.write("USE churn_db;\n\n")
        
        # Insert customers
        df = data_dict['customers']
        f.write("-- Insert Customers\n")
        for _, row in df.iterrows():
            f.write(
                f"INSERT INTO customers (customer_id, customer_name, signup_date, "
                f"status, senior_citizen, last_contact_date) VALUES "
                f"('{row['customer_id']}', '{row['customer_name']}', "
                f"'{row['signup_date'].date()}', '{row['status']}', "
                f"{row['senior_citizen']}, '{row['last_contact_date'].date()}');\n"
            )
        f.write("\n")
        
        # Insert billing
        df = data_dict['billing']
        f.write("-- Insert Billing\n")
        for _, row in df.iterrows():
            f.write(
                f"INSERT INTO billing (customer_id, monthly_charges, total_charges, "
                f"billing_cycle, last_payment_date) VALUES "
                f"('{row['customer_id']}', {row['monthly_charges']}, "
                f"{row['total_charges']}, '{row['billing_cycle']}', "
                f"'{row['last_payment_date'].date()}');\n"
            )
        f.write("\n")
        
        # Insert contracts
        df = data_dict['contracts']
        f.write("-- Insert Contracts\n")
        for _, row in df.iterrows():
            end_date = f"'{row['end_date'].date()}'" if pd.notna(row['end_date']) else 'NULL'
            f.write(
                f"INSERT INTO contracts (customer_id, contract_type, start_date, "
                f"end_date, auto_renew) VALUES "
                f"('{row['customer_id']}', '{row['contract_type']}', "
                f"'{row['start_date'].date()}', {end_date}, {row['auto_renew']});\n"
            )
        f.write("\n")
        
        # Insert customer features
        df = data_dict['customer_features']
        f.write("-- Insert Customer Features\n")
        for _, row in df.iterrows():
            f.write(
                f"INSERT INTO customer_features (customer_id, paperless_billing_score, "
                f"tech_support_score, online_backup_score, streaming_tv_score, "
                f"streaming_movies_score, device_protection_score, online_security_score, "
                f"internet_service_score) VALUES "
                f"('{row['customer_id']}', {row['paperless_billing_score']}, "
                f"{row['tech_support_score']}, {row['online_backup_score']}, "
                f"{row['streaming_tv_score']}, {row['streaming_movies_score']}, "
                f"{row['device_protection_score']}, {row['online_security_score']}, "
                f"{row['internet_service_score']});\n"
            )
        f.write("\n")
        
        # Insert payment methods
        df = data_dict['payment_methods']
        f.write("-- Insert Payment Methods\n")
        for _, row in df.iterrows():
            f.write(
                f"INSERT INTO payment_methods (customer_id, payment_method, is_auto_pay) "
                f"VALUES ('{row['customer_id']}', '{row['payment_method']}', "
                f"{row['is_auto_pay']});\n"
            )
        f.write("\n")
        
        # Insert service calls (only if exists)
        if not data_dict['service_calls'].empty:
            df = data_dict['service_calls']
            f.write("-- Insert Service Calls\n")
            for _, row in df.iterrows():
                f.write(
                    f"INSERT INTO service_calls (customer_id, call_date, issue_type, "
                    f"resolution_time_hours) VALUES "
                    f"('{row['customer_id']}', '{row['call_date'].date()}', "
                    f"'{row['issue_type']}', {row['resolution_time_hours']:.2f});\n"
                )
            f.write("\n")
        
        # Insert churn history
        if not data_dict['churn_history'].empty:
            df = data_dict['churn_history']
            f.write("-- Insert Churn History\n")
            for _, row in df.iterrows():
                f.write(
                    f"INSERT INTO churn_history (customer_id, churn_date, churn_reason) "
                    f"VALUES ('{row['customer_id']}', '{row['churn_date'].date()}', "
                    f"'{row['churn_reason']}');\n"
                )
            f.write("\n")
        
        f.write("-- Verify Data\n")
        f.write("SELECT COUNT(*) as total_customers FROM customers;\n")
        f.write("SELECT COUNT(*) as total_billing FROM billing;\n")
        f.write("SELECT COUNT(*) as total_contracts FROM contracts;\n")
        f.write("SELECT COUNT(*) as total_features FROM customer_features;\n")
        f.write("SELECT COUNT(*) as total_payments FROM payment_methods;\n")
        f.write("SELECT COUNT(*) as total_service_calls FROM service_calls;\n")
        f.write("SELECT COUNT(*) as total_churned FROM churn_history;\n")
    
    print(f"✅ SQL insert statements saved to {output_file}")


def print_configuration_guide():
    """Print guide for configuring SingleStore connection."""
    
    print("\n" + "="*70)
    print("📚 SINGLESTORE CONFIGURATION GUIDE")
    print("="*70)
    
    print("\n1️⃣  GET SINGLESTORE CREDENTIALS")
    print("-" * 70)
    print("""
If you don't have SingleStore yet:
  • Sign up for free at: https://www.singlestore.com/cloud-trial/
  • Create a new workspace
  • Create a database called 'churn_db'
  • Get your connection credentials from the Cloud Portal

Your credentials will look like:
  Host: svc-xxxxx-xxxx.aws-region.svc.singlestore.com
  Port: 3306
  Database: churn_db
  User: admin
  Password: your-password
""")
    
    print("\n2️⃣  CONFIGURE .ENV FILE")
    print("-" * 70)
    print("""
Edit your .env file with real credentials:

SINGLESTORE_HOST=svc-xxxxx-xxxx.aws-region.svc.singlestore.com
SINGLESTORE_PORT=3306
SINGLESTORE_DATABASE=churn_db
SINGLESTORE_USER=admin
SINGLESTORE_PASSWORD=your-actual-password

Keep other settings as-is for now.
""")
    
    print("\n3️⃣  CREATE DATABASE SCHEMA")
    print("-" * 70)
    print("""
Option A - Using SQL File:
  1. Run: python setup_singlestore_synthetic.py --generate-data
  2. This creates schema.sql
  3. Connect to SingleStore and run: source schema.sql

Option B - Using SingleStore Studio:
  1. Open SingleStore Studio in your browser
  2. Copy contents of schema.sql
  3. Paste and execute in SQL editor
""")
    
    print("\n4️⃣  INSERT SYNTHETIC DATA")
    print("-" * 70)
    print("""
Option A - Using SQL File:
  1. Run: python setup_singlestore_synthetic.py --generate-data
  2. This creates insert_data.sql
  3. Connect to SingleStore and run: source insert_data.sql
  4. Warning: This file is large! Better to use Python script below.

Option B - Using Python (RECOMMENDED):
  1. Ensure .env is configured
  2. Run: python setup_singlestore_synthetic.py --full-setup
  3. This will create tables and insert data automatically
""")
    
    print("\n5️⃣  TEST CONNECTION")
    print("-" * 70)
    print("""
Test your connection:

  python -c "from data import get_database; db = get_database(); db.test_connection()"

Should print: ✅ Connected to SingleStore successfully!
""")
    
    print("\n6️⃣  EXTRACT DATA")
    print("-" * 70)
    print("""
Try extracting data:

  python -c "from data import extract_customers; df = extract_customers(limit=10); print(df)"

Should show 10 customers with all features.
""")
    
    print("\n" + "="*70)
    print("✅ READY TO GO!")
    print("="*70)
    print("\nNext steps:")
    print("  • Run data validation: python -c \"from data import DataValidator, extract_customers; v = DataValidator(); print(v.validate(extract_customers()))\"")
    print("  • Start data refresh job: python jobs/data_refresh.py --mode once")
    print("  • Launch dashboard: streamlit run dashboard.py")
    print("\n")


def main():
    parser = argparse.ArgumentParser(
        description='Setup SingleStore and generate synthetic data'
    )
    parser.add_argument(
        '--generate-data',
        action='store_true',
        help='Generate synthetic data and save to files'
    )
    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Create tables in SingleStore (requires connection)'
    )
    parser.add_argument(
        '--full-setup',
        action='store_true',
        help='Full setup: create tables and insert data'
    )
    parser.add_argument(
        '--n-customers',
        type=int,
        default=1000,
        help='Number of synthetic customers to generate (default: 1000)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./synthetic_data',
        help='Output directory for generated files'
    )
    
    args = parser.parse_args()
    
    if not any([args.generate_data, args.create_tables, args.full_setup]):
        # No arguments provided, show configuration guide
        print_configuration_guide()
        return
    
    if args.generate_data or args.full_setup:
        # Generate synthetic data
        data_dict = generate_synthetic_customers(args.n_customers)
        save_synthetic_data(data_dict, args.output_dir)
        save_sql_schema('./schema.sql')
        generate_insert_sql(data_dict, './insert_data.sql')
        
        print("\n" + "="*70)
        print("✅ SYNTHETIC DATA GENERATED")
        print("="*70)
        print(f"\nFiles created:")
        print(f"  📁 {args.output_dir}/")
        print(f"  📄 schema.sql - Database schema")
        print(f"  📄 insert_data.sql - Insert statements")
        print("\nNext: Configure .env and run --full-setup to load into SingleStore")
    
    if args.create_tables or args.full_setup:
        try:
            from data import get_database
            
            print("\n" + "="*70)
            print("🔄 CREATING TABLES IN SINGLESTORE")
            print("="*70)
            
            db = get_database()
            if not db.test_connection():
                print("\n❌ Cannot connect to SingleStore. Check your .env configuration.")
                print("Run without arguments to see configuration guide.")
                return
            
            # Read and execute schema
            with open('./schema.sql') as f:
                schema = f.read()
            
            # Execute each statement
            for statement in schema.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        db.execute_query(statement)
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            print(f"⚠️  Warning: {e}")
            
            print("\n✅ Tables created successfully!")
            
        except ImportError:
            print("\n❌ Cannot import data modules. Make sure dependencies are installed:")
            print("   pip install -r requirements.txt")
            return
    
    if args.full_setup:
        try:
            print("\n" + "="*70)
            print("📥 INSERTING SYNTHETIC DATA")
            print("="*70)
            
            # Load generated data
            output_path = Path(args.output_dir)
            
            # Read CSVs and insert
            for table in ['customers', 'billing', 'contracts', 'customer_features', 
                         'payment_methods', 'service_calls', 'churn_history']:
                csv_file = output_path / f'{table}.csv'
                if csv_file.exists():
                    df = pd.read_csv(csv_file)
                    
                    # Use pandas to_sql for bulk insert
                    from sqlalchemy import create_engine
                    import os
                    
                    # Create connection string
                    conn_str = (
                        f"mysql+pymysql://{os.getenv('SINGLESTORE_USER')}:"
                        f"{os.getenv('SINGLESTORE_PASSWORD')}@"
                        f"{os.getenv('SINGLESTORE_HOST')}:"
                        f"{os.getenv('SINGLESTORE_PORT')}/"
                        f"{os.getenv('SINGLESTORE_DATABASE')}"
                    )
                    
                    engine = create_engine(conn_str)
                    
                    # Drop timestamp columns that have defaults
                    cols_to_drop = ['created_at', 'updated_at']
                    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')
                    
                    # Insert data
                    df.to_sql(table, engine, if_exists='append', index=False)
                    print(f"  ✅ Inserted {len(df)} rows into {table}")
            
            print("\n✅ All data inserted successfully!")
            print("\n" + "="*70)
            print("🎉 SETUP COMPLETE!")
            print("="*70)
            print("\nYou can now:")
            print("  • Extract data: python -c \"from data import extract_customers; print(extract_customers(limit=10))\"")
            print("  • Run validation: python -c \"from data import DataValidator, extract_customers; print(DataValidator().validate(extract_customers()))\"")
            print("  • Start dashboard: streamlit run dashboard.py")
            
        except Exception as e:
            print(f"\n❌ Error inserting data: {e}")
            print("\nYou can manually insert using: mysql < insert_data.sql")


if __name__ == '__main__':
    main()
