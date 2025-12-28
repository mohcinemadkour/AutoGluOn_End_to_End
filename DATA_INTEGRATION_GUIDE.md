# ============================================================================
# SingleStore Data Integration - Setup & Usage Guide
# ============================================================================

## 📚 Overview

This data integration layer provides:
- SingleStore database connectivity
- Automated data extraction
- Data validation & quality monitoring
- Missing value handling
- Automated refresh jobs
- Data versioning

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pymysql sqlalchemy schedule great-expectations scipy
```

### 2. Configure Database Connection

Copy the template and fill in your credentials:

```bash
cp config/database.env.template .env
```

Edit `.env` with your SingleStore credentials:
```
SINGLESTORE_HOST=your-host.singlestore.com
SINGLESTORE_PORT=3306
SINGLESTORE_DATABASE=churn_db
SINGLESTORE_USER=admin
SINGLESTORE_PASSWORD=your-password
```

### 3. Test Connection

```python
from data import get_database

db = get_database()
if db.test_connection():
    print("✅ Connected to SingleStore!")
```

## 📊 Data Extraction

### Extract Customer Data

```python
from data import CustomerDataExtractor

extractor = CustomerDataExtractor()

# Extract all active customers
customers = extractor.extract_for_prediction()

# Extract specific customers
customers = extractor.extract_for_prediction(
    customer_ids=['C001', 'C002'],
    limit=1000
)

# Extract high-value customers
high_value = extractor.extract_high_value_customers(threshold=100.0)
```

### Extract Historical Data

```python
from datetime import datetime, timedelta

# Get churn history for training
start_date = datetime.now() - timedelta(days=365)
churn_data = extractor.extract_churn_history(start_date=start_date)
```

## ✅ Data Validation

### Validate Data Quality

```python
from data import DataValidator

validator = DataValidator()

# Validate data
result = validator.validate(customers)

print(f"Passed: {result.passed}")
print(f"Quality Score: {validator.get_data_quality_score(customers)}/100")

# Check errors
for error in result.errors:
    print(f"❌ {error['rule']}: {error['description']}")
```

### Handle Missing Values

```python
from data import MissingValueHandler

handler = MissingValueHandler()

# Detect missing values
missing_stats = handler.detect_missing(customers)
print(missing_stats)

# Impute missing values
customers_clean = handler.impute_missing(customers, strategy='median')

# Detect outliers
outliers = handler.detect_outliers(customers, 'monthly_charges', method='iqr')

# Handle outliers
customers_clean = handler.handle_outliers(customers, 'monthly_charges', method='clip')
```

## 📈 Data Quality Monitoring

### Monitor Data Quality

```python
from monitoring.data_quality import DataQualityMonitor

monitor = DataQualityMonitor()

# Collect metrics
metrics = monitor.collect_metrics(customers, 'customer_data')

# Generate report
report = monitor.generate_quality_report(customers, 'customer_data')
print(report)

# Monitor with alerts
is_ok = monitor.monitor_and_alert(
    customers, 
    'customer_data', 
    alert_threshold=70.0
)
```

### View Historical Metrics

```python
# Load metrics history
history = monitor.load_metrics_history('customer_data', days=30)

# Compare with previous
if len(history) >= 2:
    comparison = monitor.compare_metrics(
        current_metrics=metrics,
        previous_metrics=history[-2]
    )
    print(comparison)
```

## 🔄 Automated Data Refresh

### Run Once

```bash
python jobs/data_refresh.py --mode once --dataset customer_data
```

### Schedule Hourly Refresh

```bash
python jobs/data_refresh.py --mode hourly --dataset customer_data
```

### Schedule Daily Refresh

```bash
python jobs/data_refresh.py --mode daily --time 02:00 --dataset customer_data
```

### Custom Interval

```bash
python jobs/data_refresh.py --mode custom --interval 30 --dataset customer_data
```

### Python API

```python
from jobs.data_refresh import DataRefreshJob

job = DataRefreshJob(
    output_dir='./data/refreshed',
    enable_validation=True,
    enable_monitoring=True,
    quality_threshold=70.0
)

# Run once
success = job.run_refresh('customer_data')

# Or schedule
job.schedule_hourly('customer_data')
job.run_scheduler()  # Blocking
```

## 📁 Data Versioning

Every refresh creates:
- Timestamped file: `customer_data_20251228_120000.csv`
- Latest file: `customer_data_latest.csv`
- Version metadata: `customer_data_versions.json`

```python
import json

# Load version history
with open('data/refreshed/customer_data_versions.json') as f:
    versions = json.load(f)

# View latest versions
for v in versions[-5:]:
    print(f"{v['timestamp']}: {v['row_count']} rows, {v['file_size_mb']:.2f} MB")
```

## 🗄️ Database Schema

Expected SingleStore tables:

### customers
```sql
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(200),
    signup_date DATE,
    churn_date DATE NULL,
    status VARCHAR(20),
    senior_citizen FLOAT,
    last_contact_date DATE
);
```

### billing
```sql
CREATE TABLE billing (
    customer_id VARCHAR(50),
    monthly_charges DECIMAL(10,2),
    total_charges DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### service_calls
```sql
CREATE TABLE service_calls (
    call_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id VARCHAR(50),
    call_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### contracts
```sql
CREATE TABLE contracts (
    contract_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id VARCHAR(50),
    contract_type VARCHAR(20),
    contract_start_date DATE,
    contract_end_date DATE NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### customer_features
```sql
CREATE TABLE customer_features (
    customer_id VARCHAR(50) PRIMARY KEY,
    paperless_billing_score FLOAT,
    tech_support_score FLOAT,
    online_backup_score FLOAT,
    internet_service_score FLOAT,
    streaming_tv_score FLOAT,
    streaming_movies_score FLOAT,
    device_protection_score FLOAT,
    online_security_score FLOAT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### payment_methods
```sql
CREATE TABLE payment_methods (
    customer_id VARCHAR(50) PRIMARY KEY,
    payment_method VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

## 🔧 Integration with Dashboard

Update `dashboard.py` to use real data:

```python
from data import extract_customers

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_customer_data():
    """Load customer data from SingleStore."""
    try:
        # Extract from database
        df = extract_customers(limit=None)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        # Fallback to synthetic data
        return generate_synthetic_data()
```

## 📊 Production Recommendations

### 1. Security
- Use environment variables for credentials
- Enable SSL/TLS for database connection
- Implement role-based access control
- Rotate passwords regularly

### 2. Performance
- Use connection pooling (already implemented)
- Add database indexes on frequently queried columns
- Consider materialized views for complex queries
- Implement query result caching

### 3. Reliability
- Set up database replication
- Configure automatic failover
- Implement retry logic for transient failures
- Monitor connection pool health

### 4. Monitoring
- Set up alerts for data quality issues
- Monitor query performance
- Track data freshness
- Log all data operations

### 5. Data Governance
- Document data lineage
- Implement change data capture (CDC)
- Maintain audit logs
- Regular data quality reviews

## 🐛 Troubleshooting

### Connection Issues

```python
from data import get_database

db = get_database()

# Test connection
if not db.test_connection():
    print("❌ Connection failed")
    # Check credentials, network, firewall
```

### Query Timeouts

```python
# Increase timeout in connection string
db._engine = create_engine(
    connection_string,
    connect_args={'connect_timeout': 30}
)
```

### Memory Issues

```python
# Use chunking for large datasets
query = "SELECT * FROM customers"
for chunk in pd.read_sql(query, db.engine, chunksize=10000):
    process_chunk(chunk)
```

## 📚 Additional Resources

- [SingleStore Documentation](https://docs.singlestore.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Great Expectations](https://greatexpectations.io/)
- [Schedule Library](https://schedule.readthedocs.io/)

## 🎯 Next Steps

1. Set up database credentials
2. Test connection and data extraction
3. Configure automated refresh job
4. Set up monitoring and alerts
5. Integrate with dashboard
6. Deploy to production

For questions or issues, contact the data engineering team.
