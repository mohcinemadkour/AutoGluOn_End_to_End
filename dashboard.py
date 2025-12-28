# ============================================================================
# CHURN PREDICTION DASHBOARD - Streamlit App
# ============================================================================
# Business-facing dashboard for churn prediction monitoring and actions
# Run with: streamlit run dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from autogluon.tabular import TabularPredictor
from autogluon.core.metrics import make_scorer
from sklearn.metrics import precision_score, recall_score
import json
from pathlib import Path

# ============================================================================
# CUSTOM METRIC FUNCTION (Must be defined before loading model)
# ============================================================================
def calculate_business_f1(y_true, y_pred, **kwargs):
    """
    Custom business F1 score function used during model training.
    This function must be defined before loading the model.
    """
    p = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    r = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    beta = 0.5  # Recall is beta-times more important
    if (beta**2 * p) + r == 0:
        return 0.0
    return (1 + beta**2) * (p * r) / ((beta**2 * p) + r)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Churn Prediction Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .high-risk {
        color: #ff4b4b;
        font-weight: bold;
    }
    .medium-risk {
        color: #ffa500;
        font-weight: bold;
    }
    .low-risk {
        color: #00cc00;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# LOAD MODEL
# ============================================================================
@st.cache_resource
def load_model():
    """Load the trained AutoGluon model"""
    try:
        model_path = "./autogluon_churn_model_hpo"
        # Allow loading model trained on different Python version
        # This is generally safe for minor version differences
        predictor = TabularPredictor.load(model_path, require_py_version_match=False)
        return predictor
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

# ============================================================================
# LOAD OR GENERATE SAMPLE DATA
# ============================================================================
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_customer_data():
    """
    Load customer data from SingleStore database.
    Falls back to synthetic data if database is unavailable.
    """
    try:
        # Try to load from SingleStore
        from data import extract_customers, DataValidator
        
        st.info("📥 Loading data from SingleStore database...")
        df = extract_customers(limit=None)  # Load all customers
        
        # Validate data quality
        validator = DataValidator()
        quality_score = validator.get_data_quality_score(df)
        
        # Show data freshness in sidebar
        if 'extracted_at' in df.columns:
            latest = pd.to_datetime(df['extracted_at']).max()
            hours_old = (datetime.now() - latest).total_seconds() / 3600
            
            if hours_old < 1:
                st.sidebar.success(f"✅ Data is fresh (updated {hours_old*60:.0f} minutes ago)")
            elif hours_old < 24:
                st.sidebar.info(f"ℹ️  Data is {hours_old:.1f} hours old")
            else:
                st.sidebar.warning(f"⚠️  Data is {hours_old/24:.1f} days old")
        
        # Show quality metrics in sidebar
        st.sidebar.metric(
            "Data Quality",
            f"{quality_score:.0f}/100",
            help="Overall data quality score from validation pipeline"
        )
        
        if quality_score >= 90:
            st.sidebar.success("Excellent quality")
        elif quality_score >= 70:
            st.sidebar.info("Good quality")
        else:
            st.sidebar.warning("Quality issues detected")
        
        st.success(f"✅ Loaded {len(df)} customers from SingleStore")
        
        # Add derived fields for dashboard
        if 'signup_date' in df.columns:
            df['signup_date'] = pd.to_datetime(df['signup_date'])
        if 'last_contact' in df.columns:
            df['last_contact'] = pd.to_datetime(df['last_contact'])
        
        return df
        
    except ImportError:
        st.warning("⚠️  Data module not available. Using local file or synthetic data.")
        # Fall back to local file or synthetic data
        return load_synthetic_data()
    except Exception as e:
        st.error(f"❌ Error loading from SingleStore: {str(e)}")
        st.info("Falling back to synthetic data for demo...")
        return load_synthetic_data()

def load_synthetic_data():
    """Generate synthetic data for demo purposes"""
    try:
        # Try to load from file if exists
        if Path("customer_data.csv").exists():
            df = pd.read_csv("customer_data.csv")
        else:
            # Generate sample data for demo
            np.random.seed(42)
            n_customers = 500
            
            df = pd.DataFrame({
                'customer_id': [f'CUST_{i:05d}' for i in range(n_customers)],
                'customer_name': [f'Customer {i}' for i in range(n_customers)],
                'tenure_months': np.random.uniform(1, 72, n_customers),
                'monthly_charges': np.random.uniform(20, 120, n_customers),
                'total_charges': np.random.uniform(100, 8000, n_customers),
                'service_calls': np.random.poisson(2, n_customers),
                'contract_duration': np.random.choice(['Monthly', 'Yearly', 'Two-Year'], n_customers, p=[0.5, 0.3, 0.2]),
                'paperless_billing': np.random.uniform(-1, 1.5, n_customers),
                'tech_support': np.random.uniform(-1.5, 1.5, n_customers),
                'online_backup': np.random.uniform(-1, 1, n_customers),
                'payment_method': np.random.choice(['Electronic', 'Credit Card', 'Bank Transfer', 'Mailed Check'], n_customers),
                'internet_service': np.random.uniform(-0.5, 1.5, n_customers),
                'streaming_tv': np.random.uniform(-1, 1.5, n_customers),
                'streaming_movies': np.random.uniform(-1, 1.5, n_customers),
                'device_protection': np.random.uniform(-1, 1, n_customers),
                'online_security': np.random.uniform(-1.5, 1, n_customers),
                'senior_citizen': np.random.uniform(-0.5, 2, n_customers),
                'signup_date': [datetime.now() - timedelta(days=np.random.randint(1, 730)) for _ in range(n_customers)],
                'last_contact': [datetime.now() - timedelta(days=np.random.randint(0, 90)) for _ in range(n_customers)]
            })
        
        return df
    except Exception as e:
        st.error(f"Error loading customer data: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# DATA TRANSFORMATION
# ============================================================================
def transform_singlestore_data(df):
    """Transform SingleStore data format to match model expectations"""
    df_transformed = df.copy()
    
    # Map contract_type to contract_duration if needed
    if 'contract_type' in df_transformed.columns and 'contract_duration' not in df_transformed.columns:
        contract_mapping = {
            'month-to-month': 'Monthly',
            'one year': 'Yearly',
            'two year': 'Two-Year'
        }
        df_transformed['contract_duration'] = df_transformed['contract_type'].map(contract_mapping)
        # Fill any unmapped values
        df_transformed['contract_duration'] = df_transformed['contract_duration'].fillna('Monthly')
    
    # Map payment methods if needed
    if 'payment_method' in df_transformed.columns:
        payment_mapping = {
            'electronic check': 'Electronic',
            'mailed check': 'Mailed Check',
            'bank transfer': 'Bank Transfer',
            'credit card': 'Credit Card'
        }
        df_transformed['payment_method'] = df_transformed['payment_method'].replace(payment_mapping)
    
    return df_transformed

# ============================================================================
# PREDICTION FUNCTIONS
# ============================================================================
def get_risk_level(probability):
    """Categorize churn probability into risk levels"""
    if probability >= 0.7:
        return "HIGH", "🔴"
    elif probability >= 0.4:
        return "MEDIUM", "🟡"
    else:
        return "LOW", "🟢"

def predict_churn_batch(predictor, customer_data):
    """Make batch predictions for all customers"""
    # Transform data if coming from SingleStore
    customer_data = transform_singlestore_data(customer_data)
    
    # Prepare features (exclude customer_id, customer_name, signup_date, last_contact)
    feature_cols = ['tenure_months', 'monthly_charges', 'total_charges', 'service_calls',
                    'contract_duration', 'paperless_billing', 'tech_support', 'online_backup',
                    'payment_method', 'internet_service', 'streaming_tv', 'streaming_movies',
                    'device_protection', 'online_security', 'senior_citizen']
    
    features_df = customer_data[feature_cols].copy()
    
    # Get predictions
    proba = predictor.predict_proba(features_df)
    customer_data['churn_probability'] = proba['Yes'].values
    
    # Add risk levels
    risk_data = customer_data['churn_probability'].apply(get_risk_level)
    customer_data['risk_level'] = [r[0] for r in risk_data]
    customer_data['risk_icon'] = [r[1] for r in risk_data]
    
    # Add binary prediction
    customer_data['churn_prediction'] = (customer_data['churn_probability'] >= 0.5).map({True: 'Yes', False: 'No'})
    
    return customer_data

def get_retention_recommendation(row):
    """Get retention action recommendation based on customer profile"""
    risk = row['risk_level']
    tenure = row['tenure_months']
    service_calls = row['service_calls']
    monthly_charges = row['monthly_charges']
    
    if risk == 'HIGH':
        if service_calls > 3:
            return "🎯 Immediate outreach: Address service issues + 20% discount offer"
        elif tenure < 12:
            return "🎯 Immediate call: Onboarding support + loyalty bonus"
        elif monthly_charges > 80:
            return "🎯 VIP retention: Personal account manager + premium perks"
        else:
            return "🎯 Urgent intervention: 15% discount + service upgrade"
    
    elif risk == 'MEDIUM':
        if service_calls > 2:
            return "📞 Proactive call: Service quality check-in"
        elif tenure < 6:
            return "📞 Welcome call: Ensure satisfaction + tips"
        else:
            return "📞 Engagement: Survey + small incentive"
    
    else:  # LOW
        return "✅ Standard engagement: Newsletter + loyalty program"

# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

# Sidebar
st.sidebar.title("🎯 Churn Prediction Dashboard")
st.sidebar.markdown("---")

# Date selector
st.sidebar.subheader("📅 Date Range")
date_range = st.sidebar.date_input(
    "Select date range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

# Risk filter
st.sidebar.subheader("🎚️ Filters")
risk_filter = st.sidebar.multiselect(
    "Risk Level",
    options=['HIGH', 'MEDIUM', 'LOW'],
    default=['HIGH', 'MEDIUM', 'LOW']
)

# Threshold selector
threshold = st.sidebar.slider(
    "Churn Probability Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Adjust prediction threshold for churn classification"
)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Use filters to focus on high-risk customers requiring immediate attention.")

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
st.title("📊 Customer Churn Prediction Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# Load model and data
predictor = load_model()

if predictor is None:
    st.error("⚠️ Failed to load model. Please check the model path.")
    st.stop()

customer_data = load_customer_data()

if customer_data.empty:
    st.error("⚠️ No customer data available.")
    st.stop()

# Make predictions
with st.spinner("🔮 Analyzing churn risk for all customers..."):
    predictions_df = predict_churn_batch(predictor, customer_data)

# Apply filters
filtered_df = predictions_df[predictions_df['risk_level'].isin(risk_filter)].copy()

# ============================================================================
# KEY METRICS ROW
# ============================================================================
st.subheader("📈 Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

total_customers = len(predictions_df)
high_risk = len(predictions_df[predictions_df['risk_level'] == 'HIGH'])
medium_risk = len(predictions_df[predictions_df['risk_level'] == 'MEDIUM'])
low_risk = len(predictions_df[predictions_df['risk_level'] == 'LOW'])
avg_churn_prob = predictions_df['churn_probability'].mean()

col1.metric(
    "Total Customers",
    f"{total_customers:,}",
    help="Total active customers"
)

col2.metric(
    "🔴 High Risk",
    f"{high_risk:,}",
    f"{high_risk/total_customers*100:.1f}%",
    delta_color="inverse",
    help="Customers with >70% churn probability"
)

col3.metric(
    "🟡 Medium Risk",
    f"{medium_risk:,}",
    f"{medium_risk/total_customers*100:.1f}%",
    help="Customers with 40-70% churn probability"
)

col4.metric(
    "🟢 Low Risk",
    f"{low_risk:,}",
    f"{low_risk/total_customers*100:.1f}%",
    delta_color="normal",
    help="Customers with <40% churn probability"
)

col5.metric(
    "Avg Churn Risk",
    f"{avg_churn_prob*100:.1f}%",
    help="Average churn probability across all customers"
)

st.markdown("---")

# ============================================================================
# VISUALIZATIONS
# ============================================================================

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔴 High-Risk Customers", "📈 Analytics", "🎯 Campaign Planning"])

with tab1:
    st.subheader("Risk Distribution Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk distribution pie chart
        risk_counts = predictions_df['risk_level'].value_counts()
        fig_pie = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker=dict(colors=['#ff4b4b', '#ffa500', '#00cc00']),
            hole=0.4
        )])
        fig_pie.update_layout(
            title="Customer Risk Distribution",
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Churn probability histogram
        fig_hist = px.histogram(
            predictions_df,
            x='churn_probability',
            nbins=50,
            title='Churn Probability Distribution',
            labels={'churn_probability': 'Churn Probability'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.add_vline(x=0.5, line_dash="dash", line_color="red", 
                          annotation_text="Threshold")
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Risk by contract type
    st.subheader("Risk Analysis by Customer Segments")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk by contract duration
        risk_contract = predictions_df.groupby(['contract_duration', 'risk_level']).size().reset_index(name='count')
        fig_contract = px.bar(
            risk_contract,
            x='contract_duration',
            y='count',
            color='risk_level',
            title='Risk Level by Contract Duration',
            color_discrete_map={'HIGH': '#ff4b4b', 'MEDIUM': '#ffa500', 'LOW': '#00cc00'},
            barmode='group'
        )
        st.plotly_chart(fig_contract, use_container_width=True)
    
    with col2:
        # Average churn probability by tenure
        predictions_df['tenure_bucket'] = pd.cut(predictions_df['tenure_months'], 
                                                  bins=[0, 6, 12, 24, 48, 100],
                                                  labels=['0-6m', '6-12m', '1-2y', '2-4y', '4y+'])
        tenure_churn = predictions_df.groupby('tenure_bucket')['churn_probability'].mean().reset_index()
        fig_tenure = px.bar(
            tenure_churn,
            x='tenure_bucket',
            y='churn_probability',
            title='Average Churn Risk by Tenure',
            labels={'tenure_bucket': 'Customer Tenure', 'churn_probability': 'Avg Churn Probability'},
            color='churn_probability',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_tenure, use_container_width=True)

with tab2:
    st.subheader("🔴 High-Risk Customers Requiring Immediate Attention")
    
    high_risk_df = predictions_df[predictions_df['risk_level'] == 'HIGH'].copy()
    high_risk_df = high_risk_df.sort_values('churn_probability', ascending=False)
    
    if len(high_risk_df) == 0:
        st.success("✅ No high-risk customers! Great retention performance!")
    else:
        st.warning(f"⚠️ {len(high_risk_df)} customers require immediate retention action")
        
        # Add recommendations
        high_risk_df['recommendation'] = high_risk_df.apply(get_retention_recommendation, axis=1)
        
        # Display high-risk customers
        display_cols = ['customer_id', 'customer_name', 'churn_probability', 'tenure_months', 
                       'monthly_charges', 'service_calls', 'contract_duration', 'recommendation']
        
        display_df = high_risk_df[display_cols].copy()
        display_df['churn_probability'] = display_df['churn_probability'].apply(lambda x: f"{x*100:.1f}%")
        display_df['tenure_months'] = display_df['tenure_months'].apply(lambda x: f"{x:.1f}")
        display_df['monthly_charges'] = display_df['monthly_charges'].apply(lambda x: f"${x:.2f}")
        
        # Rename columns for display
        display_df.columns = ['Customer ID', 'Customer Name', 'Churn Risk', 'Tenure (months)', 
                             'Monthly Charges', 'Service Calls', 'Contract', 'Recommended Action']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Export button
        csv = high_risk_df.to_csv(index=False)
        st.download_button(
            label="📥 Download High-Risk Customer List (CSV)",
            data=csv,
            file_name=f"high_risk_customers_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Campaign cost estimate
        st.subheader("💰 Retention Campaign Cost Estimate")
        
        col1, col2, col3 = st.columns(3)
        
        avg_retention_cost = 50  # Average cost per retention offer
        avg_customer_ltv = 500   # Average customer lifetime value
        
        total_campaign_cost = len(high_risk_df) * avg_retention_cost
        potential_revenue_at_risk = len(high_risk_df) * avg_customer_ltv
        estimated_retention_rate = 0.6  # Assume 60% retention success
        expected_revenue_saved = potential_revenue_at_risk * estimated_retention_rate
        roi = (expected_revenue_saved - total_campaign_cost) / total_campaign_cost
        
        col1.metric(
            "Campaign Cost",
            f"${total_campaign_cost:,.0f}",
            help=f"Estimated cost to target {len(high_risk_df)} customers @ ${avg_retention_cost}/customer"
        )
        
        col2.metric(
            "Expected Revenue Saved",
            f"${expected_revenue_saved:,.0f}",
            help=f"Assuming {estimated_retention_rate*100:.0f}% retention success rate"
        )
        
        col3.metric(
            "Campaign ROI",
            f"{roi*100:.1f}%",
            help="Return on investment for retention campaign"
        )

with tab3:
    st.subheader("📈 Detailed Analytics")
    
    # Churn risk by payment method
    col1, col2 = st.columns(2)
    
    with col1:
        payment_risk = predictions_df.groupby('payment_method')['churn_probability'].mean().reset_index()
        payment_risk = payment_risk.sort_values('churn_probability', ascending=False)
        fig_payment = px.bar(
            payment_risk,
            x='churn_probability',
            y='payment_method',
            orientation='h',
            title='Average Churn Risk by Payment Method',
            labels={'churn_probability': 'Avg Churn Probability', 'payment_method': 'Payment Method'},
            color='churn_probability',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_payment, use_container_width=True)
    
    with col2:
        # Service calls vs churn probability
        fig_scatter = px.scatter(
            predictions_df.sample(min(500, len(predictions_df))),
            x='service_calls',
            y='churn_probability',
            color='risk_level',
            title='Service Calls vs Churn Probability',
            labels={'service_calls': 'Number of Service Calls', 'churn_probability': 'Churn Probability'},
            color_discrete_map={'HIGH': '#ff4b4b', 'MEDIUM': '#ffa500', 'LOW': '#00cc00'},
            opacity=0.6
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Monthly charges distribution by risk
    st.subheader("Revenue at Risk Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Box plot of monthly charges by risk level
        fig_box = px.box(
            predictions_df,
            x='risk_level',
            y='monthly_charges',
            title='Monthly Charges Distribution by Risk Level',
            color='risk_level',
            color_discrete_map={'HIGH': '#ff4b4b', 'MEDIUM': '#ffa500', 'LOW': '#00cc00'}
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    with col2:
        # Total revenue at risk
        revenue_at_risk = predictions_df.groupby('risk_level')['monthly_charges'].sum().reset_index()
        revenue_at_risk['annual_revenue'] = revenue_at_risk['monthly_charges'] * 12
        
        fig_revenue = px.bar(
            revenue_at_risk,
            x='risk_level',
            y='annual_revenue',
            title='Annual Revenue at Risk by Customer Segment',
            labels={'annual_revenue': 'Annual Revenue ($)', 'risk_level': 'Risk Level'},
            color='risk_level',
            color_discrete_map={'HIGH': '#ff4b4b', 'MEDIUM': '#ffa500', 'LOW': '#00cc00'}
        )
        st.plotly_chart(fig_revenue, use_container_width=True)

with tab4:
    st.subheader("🎯 Retention Campaign Planning")
    
    # Campaign strategy recommendations
    st.markdown("""
    ### Recommended Campaign Strategy
    
    Based on the current customer risk profile, here's your action plan:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🔴 High-Risk Campaign")
        st.markdown(f"""
        **Target:** {high_risk} customers  
        **Urgency:** Immediate (24-48 hours)  
        **Budget:** ${high_risk * 50:,.0f}  
        
        **Actions:**
        - Personal outreach call
        - 15-20% discount offer
        - Service issue resolution
        - Account manager assignment
        """)
    
    with col2:
        st.markdown("#### 🟡 Medium-Risk Campaign")
        st.markdown(f"""
        **Target:** {medium_risk} customers  
        **Urgency:** This week  
        **Budget:** ${medium_risk * 25:,.0f}  
        
        **Actions:**
        - Automated satisfaction survey
        - 10% loyalty discount
        - Feature education email
        - Proactive check-in call
        """)
    
    with col3:
        st.markdown("#### 🟢 Low-Risk Engagement")
        st.markdown(f"""
        **Target:** {low_risk} customers  
        **Urgency:** This month  
        **Budget:** ${low_risk * 5:,.0f}  
        
        **Actions:**
        - Newsletter engagement
        - Loyalty program updates
        - Referral incentives
        - Feature tips & tricks
        """)
    
    st.markdown("---")
    
    # Campaign prioritization
    st.subheader("📋 Prioritized Action List (Top 20)")
    
    priority_df = predictions_df.sort_values('churn_probability', ascending=False).head(20).copy()
    priority_df['recommendation'] = priority_df.apply(get_retention_recommendation, axis=1)
    priority_df['priority'] = range(1, len(priority_df) + 1)
    
    priority_display = priority_df[['priority', 'customer_id', 'customer_name', 'churn_probability', 
                                    'monthly_charges', 'tenure_months', 'recommendation']].copy()
    priority_display['churn_probability'] = priority_display['churn_probability'].apply(lambda x: f"{x*100:.1f}%")
    priority_display['monthly_charges'] = priority_display['monthly_charges'].apply(lambda x: f"${x:.2f}")
    priority_display['tenure_months'] = priority_display['tenure_months'].apply(lambda x: f"{x:.1f}")
    
    priority_display.columns = ['Priority', 'Customer ID', 'Name', 'Risk %', 
                               'Monthly Value', 'Tenure', 'Action']
    
    st.dataframe(priority_display, use_container_width=True, hide_index=True)

# ============================================================================
# MODEL PERFORMANCE SECTION
# ============================================================================
st.markdown("---")
st.subheader("🤖 Model Performance Metrics")

col1, col2, col3, col4 = st.columns(4)

# Get model info
leaderboard = predictor.leaderboard(silent=True)
best_model = leaderboard.iloc[0]['model']
best_score = leaderboard.iloc[0]['score_val']

col1.metric(
    "Model Version",
    "v1.0",
    help="Current production model version"
)

col2.metric(
    "Best Model",
    best_model,
    help="Top performing model in ensemble"
)

col3.metric(
    "Validation Score",
    f"{best_score:.4f}",
    help="PR-AUC on validation set"
)

col4.metric(
    "Total Models",
    len(leaderboard),
    help="Number of models in ensemble"
)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>💡 <b>Need Help?</b> Contact the Data Science team for questions about predictions or campaign strategies.</p>
    <p>🔄 Dashboard refreshes automatically. Use the sidebar refresh button to update data manually.</p>
</div>
""", unsafe_allow_html=True)
