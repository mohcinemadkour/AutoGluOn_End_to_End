# ============================================================================
# Customer Data Extractor
# ============================================================================
# Handles extraction of customer data from SingleStore for churn prediction

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
from .database import get_database

logger = logging.getLogger(__name__)


class CustomerDataExtractor:
    """
    Extracts and prepares customer data from SingleStore database
    for churn prediction modeling.
    """
    
    def __init__(self):
        """Initialize data extractor."""
        self.db = get_database()
        self.required_features = [
            'customer_id',
            'tenure_months',
            'monthly_charges',
            'total_charges',
            'service_calls',
            'contract_duration',
            'paperless_billing',
            'tech_support',
            'online_backup',
            'payment_method',
            'internet_service',
            'streaming_tv',
            'streaming_movies',
            'device_protection',
            'online_security',
            'senior_citizen'
        ]
    
    def extract_active_customers(
        self,
        as_of_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract all active customers as of a specific date.
        
        Args:
            as_of_date: Date to extract customers for (defaults to today)
            limit: Maximum number of customers to extract
            
        Returns:
            DataFrame with customer data
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        
        query = """
        SELECT 
            c.customer_id,
            c.customer_name,
            c.signup_date,
            c.status,
            
            -- Tenure calculation
            TIMESTAMPDIFF(MONTH, c.signup_date, %(as_of_date)s) as tenure_months,
            
            -- Charges
            b.monthly_charges,
            b.total_charges,
            
            -- Service metrics
            COALESCE(s.service_calls_30d, 0) as service_calls,
            
            -- Contract information
            ct.contract_type as contract_duration,
            
            -- Service features (normalized scores)
            COALESCE(f.paperless_billing_score, 0) as paperless_billing,
            COALESCE(f.tech_support_score, 0) as tech_support,
            COALESCE(f.online_backup_score, 0) as online_backup,
            COALESCE(f.internet_service_score, 0) as internet_service,
            COALESCE(f.streaming_tv_score, 0) as streaming_tv,
            COALESCE(f.streaming_movies_score, 0) as streaming_movies,
            COALESCE(f.device_protection_score, 0) as device_protection,
            COALESCE(f.online_security_score, 0) as online_security,
            
            -- Payment method
            p.payment_method,
            
            -- Demographics
            c.senior_citizen,
            
            -- Metadata
            c.last_contact_date as last_contact,
            NOW() as extracted_at
            
        FROM customers c
        
        -- Billing information
        LEFT JOIN billing b ON c.customer_id = b.customer_id
        
        -- Service metrics (last 30 days)
        LEFT JOIN (
            SELECT 
                customer_id,
                COUNT(*) as service_calls_30d
            FROM service_calls
            WHERE call_date >= DATE_SUB(%(as_of_date)s, INTERVAL 30 DAY)
            AND call_date <= %(as_of_date)s
            GROUP BY customer_id
        ) s ON c.customer_id = s.customer_id
        
        -- Contract information
        LEFT JOIN contracts ct ON c.customer_id = ct.customer_id
            AND ct.start_date <= %(as_of_date)s
            AND (ct.end_date IS NULL OR ct.end_date >= %(as_of_date)s)
        
        -- Feature scores
        LEFT JOIN customer_features f ON c.customer_id = f.customer_id
        
        -- Payment method
        LEFT JOIN payment_methods p ON c.customer_id = p.customer_id
        
        WHERE c.status = 'active'
        AND c.signup_date <= %(as_of_date)s
        """
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        params = {'as_of_date': as_of_date.strftime('%Y-%m-%d')}
        
        logger.info(f"Extracting active customers as of {as_of_date.date()}")
        df = self.db.execute_query(query, params)
        
        logger.info(f"Extracted {len(df)} active customers")
        return df
    
    def extract_recent_signups(self, days: int = 30) -> pd.DataFrame:
        """
        Extract customers who signed up in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            DataFrame with new customer data
        """
        query = """
        SELECT 
            customer_id,
            customer_name,
            signup_date,
            TIMESTAMPDIFF(DAY, signup_date, NOW()) as days_since_signup
        FROM customers
        WHERE signup_date >= DATE_SUB(NOW(), INTERVAL %(days)s DAY)
        AND status = 'active'
        ORDER BY signup_date DESC
        """
        
        params = {'days': days}
        return self.db.execute_query(query, params)
    
    def extract_high_value_customers(self, threshold: float = 100.0) -> pd.DataFrame:
        """
        Extract high-value customers (monthly charges above threshold).
        
        Args:
            threshold: Minimum monthly charges
            
        Returns:
            DataFrame with high-value customers
        """
        query = """
        SELECT 
            c.customer_id,
            c.customer_name,
            b.monthly_charges,
            b.total_charges,
            TIMESTAMPDIFF(MONTH, c.signup_date, NOW()) as tenure_months
        FROM customers c
        JOIN billing b ON c.customer_id = b.customer_id
        WHERE c.status = 'active'
        AND b.monthly_charges >= %(threshold)s
        ORDER BY b.monthly_charges DESC
        """
        
        params = {'threshold': threshold}
        return self.db.execute_query(query, params)
    
    def extract_churn_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Extract historical churn data for model training.
        
        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with churned customer features
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)
        
        query = """
        SELECT 
            c.customer_id,
            TIMESTAMPDIFF(MONTH, c.signup_date, c.churn_date) as tenure_months,
            b.monthly_charges,
            b.total_charges,
            s.service_calls,
            ct.contract_type as contract_duration,
            f.paperless_billing_score as paperless_billing,
            f.tech_support_score as tech_support,
            f.online_backup_score as online_backup,
            f.internet_service_score as internet_service,
            f.streaming_tv_score as streaming_tv,
            f.streaming_movies_score as streaming_movies,
            f.device_protection_score as device_protection,
            f.online_security_score as online_security,
            p.payment_method,
            c.senior_citizen,
            'Yes' as churn
            
        FROM customers c
        LEFT JOIN billing b ON c.customer_id = b.customer_id
        LEFT JOIN (
            SELECT customer_id, COUNT(*) as service_calls
            FROM service_calls
            GROUP BY customer_id
        ) s ON c.customer_id = s.customer_id
        LEFT JOIN contracts ct ON c.customer_id = ct.customer_id
        LEFT JOIN customer_features f ON c.customer_id = f.customer_id
        LEFT JOIN payment_methods p ON c.customer_id = p.customer_id
        
        WHERE c.status = 'churned'
        AND c.churn_date BETWEEN %(start_date)s AND %(end_date)s
        """
        
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        logger.info(f"Extracting churn history from {start_date.date()} to {end_date.date()}")
        df = self.db.execute_query(query, params)
        
        logger.info(f"Extracted {len(df)} churned customers")
        return df
    
    def extract_customer_by_id(self, customer_id: str) -> pd.DataFrame:
        """
        Extract data for a specific customer.
        
        Args:
            customer_id: Customer ID to extract
            
        Returns:
            DataFrame with single customer's data
        """
        df = self.extract_active_customers()
        return df[df['customer_id'] == customer_id]
    
    def extract_for_prediction(
        self,
        customer_ids: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract customer data prepared for prediction.
        
        Args:
            customer_ids: Specific customer IDs to extract (None = all)
            limit: Maximum number of customers
            
        Returns:
            DataFrame ready for model prediction
        """
        df = self.extract_active_customers(limit=limit)
        
        if customer_ids:
            df = df[df['customer_id'].isin(customer_ids)]
        
        # Ensure all required features are present
        missing_features = set(self.required_features) - set(df.columns)
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")
            for feature in missing_features:
                df[feature] = np.nan
        
        # Select only required features
        df = df[self.required_features + ['customer_name', 'extracted_at', 'last_contact']]
        
        return df
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """
        Get statistics about available data.
        
        Returns:
            Dictionary with data statistics
        """
        stats = {}
        
        # Total customers
        stats['total_customers'] = self.db.get_table_count('customers')
        
        # Active customers
        active_query = "SELECT COUNT(*) as count FROM customers WHERE status = 'active'"
        stats['active_customers'] = int(self.db.execute_query(active_query)['count'].iloc[0])
        
        # Churned customers
        churned_query = "SELECT COUNT(*) as count FROM customers WHERE status = 'churned'"
        stats['churned_customers'] = int(self.db.execute_query(churned_query)['count'].iloc[0])
        
        # Date range
        date_query = """
        SELECT 
            MIN(signup_date) as earliest_signup,
            MAX(signup_date) as latest_signup,
            MIN(churn_date) as earliest_churn,
            MAX(churn_date) as latest_churn
        FROM customers
        """
        date_stats = self.db.execute_query(date_query).iloc[0]
        stats.update(date_stats.to_dict())
        
        logger.info(f"Data statistics: {stats}")
        return stats


# Convenience function
def extract_customers(**kwargs) -> pd.DataFrame:
    """
    Convenience function to extract customer data.
    
    Args:
        **kwargs: Arguments passed to CustomerDataExtractor methods
        
    Returns:
        DataFrame with customer data
    """
    extractor = CustomerDataExtractor()
    return extractor.extract_for_prediction(**kwargs)


if __name__ == "__main__":
    # Test extraction
    extractor = CustomerDataExtractor()
    
    # Get stats
    stats = extractor.get_extraction_stats()
    print("\n📊 Data Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Extract sample
    print("\n🔍 Extracting sample customers...")
    df = extractor.extract_for_prediction(limit=10)
    print(f"\n✅ Extracted {len(df)} customers")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nSample:\n{df.head()}")
