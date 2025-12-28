# 📊 Churn Prediction Dashboard - User Guide

Interactive business dashboard for monitoring customer churn risk and managing retention campaigns.

---

## 🚀 Quick Start

### Installation

```bash
# Install Streamlit and visualization libraries
pip install streamlit plotly
```

### Run the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open automatically in your browser at: **http://localhost:8501**

---

## 📋 Dashboard Features

### 1. **Overview Tab**
- **Key Metrics**: Total customers, high/medium/low risk counts, average churn probability
- **Risk Distribution**: Pie chart showing customer risk breakdown
- **Probability Distribution**: Histogram of churn probabilities across all customers
- **Segment Analysis**: Risk levels by contract type and customer tenure

### 2. **High-Risk Customers Tab**
- **Priority List**: Customers sorted by churn probability (highest first)
- **Personalized Recommendations**: Specific retention actions for each customer
- **Campaign Cost Estimator**: Budget and ROI calculations for retention campaigns
- **CSV Export**: Download high-risk customer list for action

### 3. **Analytics Tab**
- **Payment Method Analysis**: Churn risk by payment type
- **Service Quality Impact**: Correlation between service calls and churn
- **Revenue at Risk**: Total monthly/annual revenue endangered by churn
- **Segment Performance**: Deep dive into customer segments

### 4. **Campaign Planning Tab**
- **Strategy Recommendations**: Tailored campaigns for each risk level
- **Budget Planning**: Cost estimates for different intervention types
- **Priority Action List**: Top 20 customers requiring immediate attention
- **ROI Projections**: Expected return on retention investment

---

## 🎯 How to Use

### Daily Workflow

1. **Morning Review** (5 minutes):
   - Check Key Metrics for overnight changes
   - Review High-Risk Customers tab for new urgent cases
   - Export high-risk list for team action

2. **Weekly Planning** (15 minutes):
   - Analyze trends in Analytics tab
   - Review Campaign Planning recommendations
   - Adjust retention budgets based on risk distribution

3. **Monthly Analysis** (30 minutes):
   - Compare period-over-period metrics
   - Validate model performance
   - Update retention strategies

### Sidebar Controls

- **📅 Date Range**: Filter predictions by date (not yet connected to database)
- **🎚️ Risk Level Filter**: Show only specific risk categories
- **Threshold Adjuster**: Change sensitivity of churn classification (0.5 default)
- **🔄 Refresh Button**: Reload data and recompute predictions

---

## 🎨 Understanding Risk Levels

| Risk Level | Churn Probability | Icon | Action Required |
|------------|------------------|------|-----------------|
| **HIGH** 🔴 | ≥ 70% | Red | Immediate (24-48 hours) |
| **MEDIUM** 🟡 | 40-69% | Yellow | This week |
| **LOW** 🟢 | < 40% | Green | Standard engagement |

---

## 💡 Retention Recommendations

The dashboard provides personalized recommendations based on customer characteristics:

### High-Risk Actions:
- **High Service Calls**: Address service issues + 20% discount
- **New Customers** (<12 months): Onboarding support + loyalty bonus
- **High-Value** (>$80/month): VIP treatment + account manager
- **Default**: 15% discount + service upgrade

### Medium-Risk Actions:
- **Multiple Service Calls**: Proactive service quality check
- **Very New** (<6 months): Welcome call + tips
- **Default**: Satisfaction survey + small incentive

### Low-Risk Engagement:
- Newsletter campaigns
- Loyalty program updates
- Referral incentives

---

## 📊 Key Metrics Explained

### Business Metrics:
- **Total Customers**: Active customer base size
- **High/Medium/Low Risk Counts**: Distribution across risk categories
- **Average Churn Risk**: Mean probability across all customers
- **Revenue at Risk**: Potential lost annual revenue from high-risk customers

### Campaign Metrics:
- **Campaign Cost**: Total budget needed for retention offers
- **Expected Revenue Saved**: Projected revenue retained (assuming 60% success)
- **ROI**: Return on investment for retention campaign

### Model Metrics:
- **Validation Score**: PR-AUC on validation set (higher = better)
- **Best Model**: Top-performing model in the ensemble
- **Total Models**: Number of models in the AutoGluon ensemble

---

## 🔧 Customization

### Connecting Your Data

Replace the sample data generation in `load_customer_data()` with your database connection:

```python
@st.cache_data
def load_customer_data():
    """Load from your database"""
    import sqlalchemy as sa
    
    engine = sa.create_engine('your_database_url')
    query = """
        SELECT 
            customer_id,
            customer_name,
            tenure_months,
            monthly_charges,
            -- ... other features
        FROM customers
        WHERE status = 'active'
    """
    df = pd.read_sql(query, engine)
    return df
```

### Adjusting Cost Assumptions

Update these variables in the "High-Risk Customers" tab:

```python
avg_retention_cost = 50      # Average cost per offer
avg_customer_ltv = 500       # Customer lifetime value
estimated_retention_rate = 0.6  # Success rate assumption
```

### Adding Custom Charts

Add new visualizations in any tab:

```python
# Example: Add a new chart
fig = px.bar(
    your_data,
    x='category',
    y='value',
    title='Your Custom Chart'
)
st.plotly_chart(fig, use_container_width=True)
```

---

## 🚨 Troubleshooting

### Dashboard won't start:
```bash
# Check Streamlit is installed
pip install streamlit

# Verify model path exists
ls ./autogluon_churn_model_hpo/
```

### No data showing:
- Check `customer_data.csv` exists, or
- Dashboard will generate sample data automatically

### Predictions taking too long:
- Reduce number of customers in dataset
- Use batch prediction optimization
- Consider caching more aggressively

### Model not loading:
```python
# Verify model path in dashboard.py
model_path = "./autogluon_churn_model_hpo"  # Update this
```

---

## 📈 Performance Tips

1. **Caching**: Dashboard uses `@st.cache_data` and `@st.cache_resource` for speed
2. **Batch Predictions**: All customers predicted at once (not one-by-one)
3. **Data Sampling**: Large visualizations sample data for performance
4. **Lazy Loading**: Charts only compute when tab is clicked

---

## 🔐 Production Deployment

### Deploy to Streamlit Cloud (Free):

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your repository
4. Deploy!

### Deploy to Your Server:

```bash
# Run with production settings
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

# Or use Docker
docker build -f Dockerfile.streamlit -t churn-dashboard .
docker run -p 8501:8501 churn-dashboard
```

### Add Authentication:

```python
# Add to top of dashboard.py
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Show dashboard
    pass
```

---

## 📞 Support

For questions or issues:
- **Technical Issues**: Check logs with `streamlit run dashboard.py --logger.level=debug`
- **Feature Requests**: Open an issue or contact Data Science team
- **Urgent Support**: Use refresh button or restart dashboard

---

## 🎓 Next Steps

1. ✅ **Connect Real Data**: Replace sample data with your database
2. ✅ **Schedule Updates**: Set up daily data refresh (cron job)
3. ✅ **Track Actions**: Log retention campaign outcomes
4. ✅ **Monitor Success**: Track actual churn vs predictions
5. ✅ **Iterate**: Use feedback to improve recommendations

---

**Happy Monitoring!** 📊🚀
