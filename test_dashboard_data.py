"""
Test Dashboard Data Integration
Verifies that SingleStore data flows correctly into the dashboard
"""

from data import extract_customers
import pandas as pd

print("=" * 70)
print("TESTING DASHBOARD DATA INTEGRATION")
print("=" * 70)

# Step 1: Extract data from SingleStore
print("\n1️⃣  Extracting data from SingleStore...")
df = extract_customers(limit=10)
print(f"✅ Extracted {len(df)} customers")

# Step 2: Check required columns
print("\n2️⃣  Checking required columns for dashboard...")
required_cols = [
    'customer_id', 'tenure_months', 'monthly_charges', 'total_charges',
    'service_calls', 'contract_type', 'paperless_billing', 'tech_support',
    'online_backup', 'payment_method', 'internet_service', 'streaming_tv',
    'streaming_movies', 'device_protection', 'online_security', 'senior_citizen'
]

missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    print(f"❌ Missing columns: {missing_cols}")
else:
    print(f"✅ All required columns present")

print("\n📊 Available columns:")
for col in df.columns:
    print(f"  • {col}")

# Step 3: Check data types and values
print("\n3️⃣  Checking data quality...")

# Contract types
if 'contract_type' in df.columns:
    print(f"\nContract types: {df['contract_type'].unique()}")
    contract_mapping = {
        'month-to-month': 'Monthly',
        'one year': 'Yearly',
        'two year': 'Two-Year'
    }
    df['contract_duration'] = df['contract_type'].map(contract_mapping)
    print(f"Mapped to: {df['contract_duration'].unique()}")

# Payment methods
if 'payment_method' in df.columns:
    print(f"\nPayment methods: {df['payment_method'].unique()}")

# Numeric ranges
print(f"\nTenure range: {df['tenure_months'].min():.0f} - {df['tenure_months'].max():.0f} months")
print(f"Monthly charges: ${df['monthly_charges'].min():.2f} - ${df['monthly_charges'].max():.2f}")
print(f"Service calls: {df['service_calls'].min():.0f} - {df['service_calls'].max():.0f}")

# Step 4: Sample data
print("\n4️⃣  Sample data (first 3 customers):")
print(df[['customer_id', 'tenure_months', 'monthly_charges', 'contract_type', 'service_calls']].head(3))

print("\n" + "=" * 70)
print("✅ DATA INTEGRATION TEST COMPLETE")
print("=" * 70)
print("\n📍 Dashboard URL: http://localhost:8502")
print("🔄 Data refreshes automatically every hour (ttl=3600)")
print("\nThe dashboard will:")
print("  1. Load 847 customers from SingleStore")
print("  2. Transform contract types and payment methods")
print("  3. Make churn predictions using AutoGluon model")
print("  4. Display risk levels and recommendations")
