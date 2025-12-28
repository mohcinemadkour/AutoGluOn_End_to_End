# SingleStore Data Integration - Usage Examples

This document provides practical examples for using the SingleStore data integration pipeline.

## 📋 Table of Contents

- [Setup](#setup)
- [Database Connection](#database-connection)
- [Data Extraction](#data-extraction)
- [Data Validation](#data-validation)
- [Data Quality Monitoring](#data-quality-monitoring)
- [Automated Refresh Jobs](#automated-refresh-jobs)
- [Dashboard Integration](#dashboard-integration)
- [Production Scenarios](#production-scenarios)

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

```bash
# Copy template
cp config/database.env.template .env

# Edit .env with your credentials
# SINGLESTORE_HOST=your-host.singlestore.com
# SINGLESTORE_PORT=3306
# SINGLESTORE_DATABASE=churn_db
# SINGLESTORE_USER=admin
# SINGLESTORE_PASSWORD=your-password
```

### 3. Verify Installation

```python
import pandas as pd
from data import get_database

print("✅ Imports successful")
```

---

## Database Connection

### Basic Connection Test

```python
from data import get_database

# Get database connection
db = get_database()

# Test connection
if db.test_connection():
    print("✅ Connected to SingleStore successfully!")
else:
    print("❌ Connection failed")
```

### Custom Connection Parameters

```python
from data import init_database

# Initialize with custom parameters
db = init_database(
    host='my-singlestore-host.com',
    port=3306,
    database='production_db',
    user='data_scientist',
    password='secure_password'
)

# Test connection
db.test_connection()
```

### Execute Simple Query

```python
from data import get_database

db = get_database()

# Run a simple query
result = db.execute_query("SELECT COUNT(*) as total FROM customers")
print(f"Total customers: {result['total'].iloc[0]}")
```

### Get Table Information

```python
from data import get_database

db = get_database()

# Get table schema
table_info = db.get_table_info('customers')
print(table_info)

# Get row count
count = db.get_table_count('customers')
print(f"Customer count: {count}")
```

---

## Data Extraction

### Extract All Active Customers

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Extract all active customers
customers = extractor.extract_for_prediction()
print(f"Extracted {len(customers)} customers")
print(customers.head())
```

### Extract Limited Number of Customers

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Extract only 100 customers
customers = extractor.extract_for_prediction(limit=100)
print(f"Extracted {len(customers)} customers")
```

### Extract Specific Customers by ID

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Extract specific customer IDs
customer_ids = ['C001', 'C002', 'C003']
customers = extractor.extract_for_prediction(customer_ids=customer_ids)
print(customers)
```

### Extract High-Value Customers

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Extract customers with monthly charges > $100
high_value = extractor.extract_high_value_customers(threshold=100.0)
print(f"Found {len(high_value)} high-value customers")
print(high_value[['customer_id', 'monthly_charges', 'tenure_months']].head())
```

### Extract Recent Signups

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Extract customers who signed up in last 30 days
recent = extractor.extract_recent_signups(days=30)
print(f"Found {len(recent)} recent signups")
```

### Extract Historical Churn Data

```python
from data import CustomerDataExtractor
from datetime import datetime, timedelta

extractor = CustomerDataExtractor()

# Extract churn data for last year
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

churn_data = extractor.extract_churn_history(
    start_date=start_date,
    end_date=end_date
)
print(f"Extracted {len(churn_data)} churned customers")
```

### Get Extraction Statistics

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Get data statistics
stats = extractor.get_extraction_stats()
print("Data Statistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")
```

### Convenience Function

```python
from data import extract_customers

# Quick extraction
customers = extract_customers(limit=500)
print(f"Extracted {len(customers)} customers")
```

---

## Data Validation

### Basic Validation

```python
from data import DataValidator, extract_customers

# Extract data
customers = extract_customers(limit=100)

# Validate
validator = DataValidator()
result = validator.validate(customers)

print(f"Validation passed: {result.passed}")
print(f"Total checks: {result.total_checks}")
print(f"Failed checks: {result.failed_checks}")
```

### Check Validation Results

```python
from data import DataValidator, extract_customers

customers = extract_customers(limit=100)
validator = DataValidator()
result = validator.validate(customers)

# Check errors
if result.errors:
    print("\n❌ Validation Errors:")
    for error in result.errors:
        print(f"  Rule: {error['rule']}")
        print(f"  Column: {error['column']}")
        print(f"  Description: {error['description']}")
        print(f"  Failed: {error['failed_count']} rows ({error['failed_percentage']:.1f}%)")
        print()

# Check warnings
if result.warnings:
    print("\n⚠️  Validation Warnings:")
    for warning in result.warnings:
        print(f"  Rule: {warning['rule']}")
        print(f"  Description: {warning['description']}")
```

### Get Data Quality Score

```python
from data import DataValidator, extract_customers

customers = extract_customers()
validator = DataValidator()

# Get quality score (0-100)
score = validator.get_data_quality_score(customers)
print(f"Data Quality Score: {score}/100")

# Interpret score
if score >= 90:
    print("✅ Excellent quality")
elif score >= 70:
    print("⚠️  Acceptable quality")
else:
    print("❌ Poor quality - action required")
```

### Detect Missing Values

```python
from data import MissingValueHandler, extract_customers

customers = extract_customers()
handler = MissingValueHandler()

# Detect missing values
missing_stats = handler.detect_missing(customers)

if not missing_stats.empty:
    print("Missing Values Found:")
    print(missing_stats)
else:
    print("✅ No missing values")
```

### Impute Missing Values

```python
from data import MissingValueHandler, extract_customers

customers = extract_customers()
handler = MissingValueHandler()

# Impute using median
customers_clean = handler.impute_missing(customers, strategy='median')

# Or use mean
customers_clean = handler.impute_missing(customers, strategy='mean')

# Or use mode for categorical
customers_clean = handler.impute_missing(customers, strategy='mode')

print("✅ Missing values imputed")
```

### Detect and Handle Outliers

```python
from data import MissingValueHandler, extract_customers

customers = extract_customers()
handler = MissingValueHandler()

# Detect outliers in monthly_charges
outliers = handler.detect_outliers(
    customers, 
    'monthly_charges', 
    method='iqr',
    threshold=1.5
)
print(f"Found {outliers.sum()} outliers")

# Handle outliers by clipping
customers_clean = handler.handle_outliers(
    customers, 
    'monthly_charges', 
    method='clip'
)

# Or remove outliers
customers_no_outliers = handler.handle_outliers(
    customers,
    'monthly_charges',
    method='remove'
)

# Or log transform
customers_transformed = handler.handle_outliers(
    customers,
    'monthly_charges',
    method='log_transform'
)
```

---

## Data Quality Monitoring

### Collect Quality Metrics

```python
from monitoring.data_quality import DataQualityMonitor
from data import extract_customers

customers = extract_customers()
monitor = DataQualityMonitor()

# Collect comprehensive metrics
metrics = monitor.collect_metrics(customers, 'customer_data')

# View specific metrics
print(f"Row count: {metrics['row_count']}")
print(f"Quality score: {metrics['validation']['quality_score']}")
print(f"Missing cells: {metrics['missing_values']['total_missing_cells']}")
```

### Generate Quality Report

```python
from monitoring.data_quality import DataQualityMonitor
from data import extract_customers

customers = extract_customers()
monitor = DataQualityMonitor()

# Generate and print report
report = monitor.generate_quality_report(customers, 'customer_data')
print(report)
```

### Save Quality Metrics

```python
from monitoring.data_quality import DataQualityMonitor
from data import extract_customers

customers = extract_customers()
monitor = DataQualityMonitor()

# Collect and save metrics
metrics = monitor.collect_metrics(customers, 'customer_data')
monitor.save_metrics(metrics, 'customer_data')
print("✅ Metrics saved")
```

### View Historical Metrics

```python
from monitoring.data_quality import DataQualityMonitor

monitor = DataQualityMonitor()

# Load last 30 days of metrics
history = monitor.load_metrics_history('customer_data', days=30)

print(f"Found {len(history)} historical records")

# View quality score trend
for h in history[-5:]:
    timestamp = h['timestamp']
    score = h['validation']['quality_score']
    print(f"{timestamp}: Quality Score = {score}")
```

### Compare Current vs Previous

```python
from monitoring.data_quality import DataQualityMonitor
from data import extract_customers

customers = extract_customers()
monitor = DataQualityMonitor()

# Get current metrics
current = monitor.collect_metrics(customers, 'customer_data')

# Load history
history = monitor.load_metrics_history('customer_data', days=7)

if history:
    previous = history[-1]
    comparison = monitor.compare_metrics(current, previous)
    
    print("Changes since last check:")
    print(f"  Row count: {comparison['changes']['row_count']['change']:+d}")
    print(f"  Quality score: {comparison['changes']['quality_score']['change']:+.1f}")
    
    if comparison['alerts']:
        print("\n⚠️  Alerts:")
        for alert in comparison['alerts']:
            print(f"  • {alert}")
```

### Monitor with Alerting

```python
from monitoring.data_quality import DataQualityMonitor
from data import extract_customers

customers = extract_customers()
monitor = DataQualityMonitor()

# Monitor and alert if quality < 70
is_acceptable = monitor.monitor_and_alert(
    customers,
    'customer_data',
    alert_threshold=70.0
)

if is_acceptable:
    print("✅ Data quality is acceptable")
else:
    print("🚨 Data quality alert triggered!")
```

---

## Automated Refresh Jobs

### Run Once (Command Line)

```bash
# Basic run
python jobs/data_refresh.py --mode once

# With custom dataset name
python jobs/data_refresh.py --mode once --dataset customer_data

# With custom output directory
python jobs/data_refresh.py --mode once --output-dir ./my_data

# With custom quality threshold
python jobs/data_refresh.py --mode once --quality-threshold 80.0
```

### Schedule Hourly (Command Line)

```bash
# Run every hour
python jobs/data_refresh.py --mode hourly --dataset customer_data
```

### Schedule Daily (Command Line)

```bash
# Run daily at 2 AM
python jobs/data_refresh.py --mode daily --time 02:00

# Run daily at 6 PM
python jobs/data_refresh.py --mode daily --time 18:00
```

### Schedule Custom Interval (Command Line)

```bash
# Run every 30 minutes
python jobs/data_refresh.py --mode custom --interval 30

# Run every 2 hours (120 minutes)
python jobs/data_refresh.py --mode custom --interval 120
```

### Run Once (Python)

```python
from jobs.data_refresh import DataRefreshJob

# Initialize job
job = DataRefreshJob(
    output_dir='./data/refreshed',
    enable_validation=True,
    enable_monitoring=True,
    quality_threshold=70.0
)

# Run refresh
success = job.run_refresh('customer_data')

if success:
    print("✅ Data refresh successful")
else:
    print("❌ Data refresh failed")
```

### Schedule Hourly (Python)

```python
from jobs.data_refresh import DataRefreshJob

job = DataRefreshJob()

# Schedule hourly refresh
job.schedule_hourly('customer_data')

# Start scheduler (blocking)
job.run_scheduler()
```

### Schedule Daily (Python)

```python
from jobs.data_refresh import DataRefreshJob

job = DataRefreshJob()

# Schedule daily at 2:00 AM
job.schedule_daily('02:00', 'customer_data')

# Start scheduler
job.run_scheduler()
```

### Schedule Custom Interval (Python)

```python
from jobs.data_refresh import DataRefreshJob

job = DataRefreshJob()

# Schedule every 30 minutes
job.schedule_custom(30, 'customer_data')

# Start scheduler
job.run_scheduler()
```

### View Refresh History

```python
import json
from pathlib import Path

# Load version history
version_file = Path('data/refreshed/customer_data_versions.json')

if version_file.exists():
    with open(version_file) as f:
        versions = json.load(f)
    
    print(f"Total versions: {len(versions)}")
    print("\nRecent refreshes:")
    for v in versions[-5:]:
        print(f"  {v['timestamp']}: {v['row_count']} rows, {v['file_size_mb']:.2f} MB")
```

---

## Dashboard Integration

### Update Dashboard to Use Real Data

```python
# In dashboard.py

from data import extract_customers, DataValidator

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_customer_data():
    """Load customer data from SingleStore."""
    try:
        # Extract from database
        df = extract_customers(limit=None)
        
        # Validate data
        validator = DataValidator()
        result = validator.validate(df)
        
        if not result.passed:
            st.warning(f"⚠️  Data validation found {result.failed_checks} issues")
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        # Fallback to synthetic data
        return generate_synthetic_data()
```

### Add Data Freshness Indicator

```python
# In dashboard.py

import streamlit as st
from datetime import datetime
import pandas as pd

# Load data
df = load_customer_data()

# Check freshness
if 'extracted_at' in df.columns:
    latest = pd.to_datetime(df['extracted_at']).max()
    hours_old = (datetime.now() - latest).total_seconds() / 3600
    
    if hours_old < 1:
        st.success(f"✅ Data is fresh (updated {hours_old:.0f} minutes ago)")
    elif hours_old < 24:
        st.info(f"ℹ️  Data is {hours_old:.1f} hours old")
    else:
        st.warning(f"⚠️  Data is {hours_old/24:.1f} days old")
```

### Add Quality Metrics to Sidebar

```python
# In dashboard.py

import streamlit as st
from data import DataValidator

# Load data
df = load_customer_data()

# Show quality in sidebar
validator = DataValidator()
quality_score = validator.get_data_quality_score(df)

st.sidebar.metric(
    "Data Quality",
    f"{quality_score:.0f}/100",
    help="Overall data quality score"
)

# Color coding
if quality_score >= 90:
    st.sidebar.success("Excellent quality")
elif quality_score >= 70:
    st.sidebar.info("Good quality")
else:
    st.sidebar.warning("Quality issues detected")
```

---

## Production Scenarios

### Daily Production Refresh

```python
# production_refresh.py

from jobs.data_refresh import DataRefreshJob
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_refresh.log'),
        logging.StreamHandler()
    ]
)

# Initialize job with production settings
job = DataRefreshJob(
    output_dir='/data/production/refreshed',
    enable_validation=True,
    enable_monitoring=True,
    quality_threshold=85.0  # Higher threshold for production
)

# Schedule daily at 2 AM
job.schedule_daily('02:00', 'customer_data')

# Start scheduler
print("🚀 Starting production data refresh scheduler...")
job.run_scheduler()
```

### Data Quality Monitoring Dashboard

```python
# monitoring_dashboard.py

import streamlit as st
from monitoring.data_quality import DataQualityMonitor
import pandas as pd

st.title("📊 Data Quality Monitoring")

monitor = DataQualityMonitor()

# Load history
history = monitor.load_metrics_history('customer_data', days=30)

if history:
    # Extract quality scores
    scores_df = pd.DataFrame([
        {
            'timestamp': h['timestamp'],
            'quality_score': h['validation']['quality_score'],
            'row_count': h['row_count'],
            'missing_cells': h['missing_values']['total_missing_cells']
        }
        for h in history
    ])
    
    # Plot quality trend
    st.line_chart(scores_df.set_index('timestamp')['quality_score'])
    
    # Show current metrics
    latest = history[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Quality Score", f"{latest['validation']['quality_score']:.0f}/100")
    col2.metric("Row Count", f"{latest['row_count']:,}")
    col3.metric("Missing Cells", latest['missing_values']['total_missing_cells'])
```

### Error Handling and Retry

```python
from jobs.data_refresh import DataRefreshJob
import time

def run_with_retry(max_retries=3):
    job = DataRefreshJob()
    
    for attempt in range(max_retries):
        try:
            success = job.run_refresh('customer_data')
            if success:
                print(f"✅ Refresh succeeded on attempt {attempt + 1}")
                return True
            else:
                print(f"⚠️  Refresh failed on attempt {attempt + 1}")
        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 60  # Exponential backoff
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    print("❌ All retry attempts failed")
    return False

# Run with retry
run_with_retry()
```

### Custom Validation Rules

```python
from data import DataValidator
from data.validators import ValidationRule

# Create custom validator
validator = DataValidator()

# Add custom rule
custom_rule = ValidationRule(
    name='high_value_valid',
    column='monthly_charges',
    rule_type='range',
    params={'min': 0, 'max': 1000},
    severity='error',
    description='Monthly charges must be under $1000'
)

validator.rules.append(custom_rule)

# Use custom validator
result = validator.validate(df)
```

---

## Troubleshooting Examples

### Debug Connection Issues

```python
from data import get_database
import os

# Check environment variables
print("Environment Variables:")
print(f"  SINGLESTORE_HOST: {os.getenv('SINGLESTORE_HOST')}")
print(f"  SINGLESTORE_PORT: {os.getenv('SINGLESTORE_PORT')}")
print(f"  SINGLESTORE_DATABASE: {os.getenv('SINGLESTORE_DATABASE')}")
print(f"  SINGLESTORE_USER: {os.getenv('SINGLESTORE_USER')}")

# Test connection
db = get_database()
if db.test_connection():
    print("✅ Connection successful")
    
    # Get database version
    result = db.execute_query("SELECT VERSION() as version")
    print(f"Database version: {result['version'].iloc[0]}")
else:
    print("❌ Connection failed")
```

### Debug Query Issues

```python
from data import get_database

db = get_database()

# Test simple query
try:
    result = db.execute_query("SELECT 1 as test")
    print("✅ Basic query works")
except Exception as e:
    print(f"❌ Query failed: {e}")

# Check table exists
try:
    result = db.execute_query("SHOW TABLES")
    print("Available tables:")
    print(result)
except Exception as e:
    print(f"❌ Cannot list tables: {e}")
```

### Debug Data Issues

```python
from data import extract_customers, DataValidator

# Extract sample
customers = extract_customers(limit=10)
print(f"Extracted {len(customers)} rows")
print(f"Columns: {list(customers.columns)}")
print(f"\nSample data:")
print(customers.head())

# Validate
validator = DataValidator()
result = validator.validate(customers)

# Show all issues
print(f"\n❌ Errors: {len(result.errors)}")
for error in result.errors:
    print(f"  {error['rule']}: {error['description']}")

print(f"\n⚠️  Warnings: {len(result.warnings)}")
for warning in result.warnings:
    print(f"  {warning['rule']}: {warning['description']}")
```

---

## Additional Resources

- [DATA_INTEGRATION_GUIDE.md](DATA_INTEGRATION_GUIDE.md) - Complete integration guide
- [SingleStore Documentation](https://docs.singlestore.com/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

**Last Updated:** December 28, 2025  
**Version:** 1.0
