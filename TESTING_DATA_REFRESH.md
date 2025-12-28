# Testing Dashboard Data Refresh

## What We Did

### 1. **Generated Additional Synthetic Data**
- Created 500 new customer records using `setup_singlestore_synthetic.py`
- Saved to `./synthetic_data_new/` directory
- Generated CSV files for all tables (customers, billing, contracts, etc.)

### 2. **Created Data Addition Script**
Created `add_more_data.py` to:
- Insert new customers without recreating tables
- Automatically assign non-conflicting customer IDs
- Update all related tables (billing, contracts, features, etc.)

**Note**: Direct SingleStore insertion failed due to network connectivity issues (getaddrinfo failed). This could be:
- IP address not allowlisted in SingleStore firewall
- SingleStore workspace paused
- Network/DNS connectivity issues

### 3. **Created Local Data Refresh Simulation**
Created `simulate_data_refresh.py` to test the refresh mechanism without SingleStore:
- Loads existing customer data from `data/refreshed/customer_data_latest.csv`
- Generates 100 new synthetic customers
- Merges with existing data (avoiding ID conflicts)
- Saves timestamped version + updates latest
- Updates version metadata in `customer_data_versions.json`

### 4. **Successfully Added 200 New Customers**
Ran the simulation twice:
- **First run**: Added 100 customers (847 → 947)
- **Second run**: Added 100 more customers (947 → 1,047)
- New customers have IDs: C001001 through C001200

## Current Data Status

```
📊 Dataset Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Customers:       1,047
Active Customers:        171 (16.3%)
Inactive Customers:      876 (83.7%)

New Customers Added:     200
Customer ID Range:  C000001 - C001200
```

## How Dashboard Refresh Works

### **Automatic Refresh** (Production Mode)
```
┌─────────────────┐
│ SingleStore DB  │
└────────┬────────┘
         │ 1. Extract (every hour)
         ↓
┌─────────────────────────┐
│ jobs/data_refresh.py    │
│ - Extracts customers    │
│ - Validates quality     │
│ - Saves to refreshed/   │
└────────┬────────────────┘
         │ 2. Save
         ↓
┌─────────────────────────────────┐
│ data/refreshed/                 │
│ - customer_data_latest.csv      │
│ - customer_data_[timestamp].csv │
│ - customer_data_versions.json   │
└────────┬────────────────────────┘
         │ 3. Load (cached 1 hour)
         ↓
┌─────────────────────────┐
│ dashboard.py            │
│ @st.cache_data(ttl=3600)│
└─────────────────────────┘
```

### **Manual Refresh Options**

#### Option 1: Click "Refresh Data" Button
- Clears Streamlit cache
- Forces reload from `customer_data_latest.csv`
- Takes effect immediately

#### Option 2: Restart Streamlit
```bash
# Stop current session (Ctrl+C)
streamlit run dashboard.py
```

#### Option 3: Wait for Cache Expiration
- Cache expires after 1 hour automatically
- Dashboard reloads data from latest file

## Testing the Refresh

### Step 1: Check Current Count
Open dashboard at http://localhost:8501 and note the "Total Customers" metric.

### Step 2: Add More Data
```bash
# Run simulation to add 100 customers
python simulate_data_refresh.py
```

### Step 3: Refresh Dashboard
Choose one method:
1. Click **"🔄 Refresh Data"** button in sidebar
2. Press **Ctrl+C** in terminal, then run `streamlit run dashboard.py`
3. Wait 1 hour for automatic cache expiration

### Step 4: Verify New Count
- Total Customers should increase by 100
- Check customer_id range includes new IDs
- Verify prediction scores are generated for new customers

## Files Created

```
📁 Project Structure
├── add_more_data.py              # Insert data into SingleStore (needs connection)
├── simulate_data_refresh.py      # Local refresh simulation (no DB needed)
├── synthetic_data_new/           # Additional synthetic data files
│   ├── customers.csv
│   ├── billing.csv
│   ├── contracts.csv
│   └── ... (other tables)
└── data/refreshed/
    ├── customer_data_latest.csv          # Latest data (1,047 customers)
    ├── customer_data_20251228_124852.csv # Timestamped backup
    ├── customer_data_20251228_124926.csv # Timestamped backup
    └── customer_data_versions.json       # Version metadata
```

## Next Steps

### For Production Use:
1. **Fix SingleStore Connection**
   - Check IP allowlist in SingleStore Cloud Portal
   - Verify workspace is active (not paused)
   - Test connection: `python -c "from data import get_database; get_database().test_connection()"`

2. **Use Real Data Pipeline**
   ```bash
   # Once connection is fixed, use the real refresh job
   python jobs/data_refresh.py --mode once
   ```

3. **Schedule Automated Refresh**
   ```bash
   # Run hourly in background
   python jobs/data_refresh.py --mode hourly
   ```

### For Testing:
1. **Continue Using Simulation**
   ```bash
   # Add more customers anytime
   python simulate_data_refresh.py
   ```

2. **Monitor Dashboard Behavior**
   - Test cache expiration (1 hour)
   - Test manual refresh button
   - Verify predictions update correctly

## Troubleshooting

### Dashboard Not Showing New Data
1. Clear browser cache (Ctrl+Shift+R)
2. Click "Refresh Data" button in sidebar
3. Check file timestamp: `Get-Content data/refreshed/customer_data_latest.csv | Select-Object -First 1`

### "No customer data available" Error
1. Check file exists: `Test-Path data/refreshed/customer_data_latest.csv`
2. Check file size: `Get-Item data/refreshed/customer_data_latest.csv | Select-Object Length`
3. Try regenerating: `python simulate_data_refresh.py`

### Predictions Not Updating
1. Model loads once at startup - restart Streamlit
2. Check model path in dashboard.py (line ~82)
3. Verify model supports new feature ranges

## Summary

✅ **Successfully added 200 new customers** to the dataset  
✅ **Created simulation tool** for testing without database  
✅ **Demonstrated refresh mechanism** with local data  
✅ **Total dataset now: 1,047 customers** (171 active)  

⚠️ **SingleStore connection issue** - needs IP allowlisting or workspace activation  
💡 **Dashboard will auto-refresh** every 1 hour or on manual trigger  
🎯 **Ready for testing** - open dashboard and click "Refresh Data" button
