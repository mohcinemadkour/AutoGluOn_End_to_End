# ============================================================================
# Data Quality Monitoring
# ============================================================================
# Monitors data quality metrics and tracks changes over time

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from data.validators import DataValidator, MissingValueHandler

logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """
    Monitors and tracks data quality metrics over time.
    """
    
    def __init__(self, metrics_dir: str = './monitoring/data_quality_metrics'):
        """
        Initialize data quality monitor.
        
        Args:
            metrics_dir: Directory to store metrics history
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.validator = DataValidator()
        self.missing_handler = MissingValueHandler()
    
    def collect_metrics(self, df: pd.DataFrame, dataset_name: str = 'customers') -> Dict[str, Any]:
        """
        Collect comprehensive data quality metrics.
        
        Args:
            df: DataFrame to analyze
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with all metrics
        """
        logger.info(f"Collecting metrics for {dataset_name}")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'dataset_name': dataset_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
        }
        
        # Basic statistics
        metrics['basic_stats'] = {
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'duplicate_rows': df.duplicated().sum(),
            'duplicate_percentage': (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
        }
        
        # Missing value statistics
        missing_stats = self.missing_handler.detect_missing(df)
        metrics['missing_values'] = {
            'total_missing_cells': df.isna().sum().sum(),
            'columns_with_missing': len(missing_stats),
            'by_column': missing_stats.to_dict('records') if not missing_stats.empty else []
        }
        
        # Data types
        metrics['data_types'] = df.dtypes.astype(str).to_dict()
        
        # Validation results
        validation_result = self.validator.validate(df)
        metrics['validation'] = {
            'passed': validation_result.passed,
            'quality_score': self.validator.get_data_quality_score(df),
            'total_checks': validation_result.total_checks,
            'failed_checks': validation_result.failed_checks,
            'errors': validation_result.errors,
            'warnings': validation_result.warnings
        }
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metrics['numeric_stats'] = {}
        for col in numeric_cols:
            metrics['numeric_stats'][col] = {
                'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                'median': float(df[col].median()) if not df[col].isna().all() else None,
                'std': float(df[col].std()) if not df[col].isna().all() else None,
                'min': float(df[col].min()) if not df[col].isna().all() else None,
                'max': float(df[col].max()) if not df[col].isna().all() else None,
                'q25': float(df[col].quantile(0.25)) if not df[col].isna().all() else None,
                'q75': float(df[col].quantile(0.75)) if not df[col].isna().all() else None,
                'outliers_count': self.missing_handler.detect_outliers(df, col).sum() if col in df.columns else 0
            }
        
        # Categorical column statistics
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        metrics['categorical_stats'] = {}
        for col in categorical_cols:
            unique_values = df[col].nunique()
            value_counts = df[col].value_counts().head(10).to_dict()
            metrics['categorical_stats'][col] = {
                'unique_count': int(unique_values),
                'top_values': {str(k): int(v) for k, v in value_counts.items()},
                'cardinality': 'high' if unique_values > 50 else 'medium' if unique_values > 10 else 'low'
            }
        
        # Data freshness (if timestamp column exists)
        if 'extracted_at' in df.columns:
            try:
                latest_data = pd.to_datetime(df['extracted_at']).max()
                metrics['data_freshness'] = {
                    'latest_record': latest_data.isoformat(),
                    'hours_since_update': (datetime.now() - latest_data).total_seconds() / 3600
                }
            except:
                pass
        
        logger.info(f"Metrics collected for {dataset_name}: Quality Score = {metrics['validation']['quality_score']}")
        return metrics
    
    def save_metrics(self, metrics: Dict[str, Any], dataset_name: str = 'customers'):
        """
        Save metrics to file.
        
        Args:
            metrics: Metrics dictionary
            dataset_name: Name of the dataset
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{dataset_name}_metrics_{timestamp}.json"
        filepath = self.metrics_dir / filename
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        metrics_serializable = convert_numpy_types(metrics)
        
        with open(filepath, 'w') as f:
            json.dump(metrics_serializable, f, indent=2)
        
        logger.info(f"Metrics saved to {filepath}")
    
    def load_metrics_history(self, dataset_name: str = 'customers', days: int = 30) -> List[Dict[str, Any]]:
        """
        Load historical metrics.
        
        Args:
            dataset_name: Name of the dataset
            days: Number of days to look back
            
        Returns:
            List of metrics dictionaries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        metrics_history = []
        
        for filepath in self.metrics_dir.glob(f"{dataset_name}_metrics_*.json"):
            try:
                # Extract timestamp from filename
                timestamp_str = filepath.stem.split('_')[-2:]
                file_date = datetime.strptime('_'.join(timestamp_str), '%Y%m%d_%H%M%S')
                
                if file_date >= cutoff_date:
                    with open(filepath, 'r') as f:
                        metrics = json.load(f)
                        metrics_history.append(metrics)
            except Exception as e:
                logger.warning(f"Failed to load metrics from {filepath}: {e}")
        
        # Sort by timestamp
        metrics_history.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"Loaded {len(metrics_history)} historical metric records")
        return metrics_history
    
    def compare_metrics(self, current_metrics: Dict[str, Any], previous_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current metrics with previous metrics.
        
        Args:
            current_metrics: Current metrics
            previous_metrics: Previous metrics
            
        Returns:
            Dictionary with changes
        """
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'changes': {}
        }
        
        # Row count change
        row_count_change = current_metrics['row_count'] - previous_metrics['row_count']
        row_count_pct = (row_count_change / previous_metrics['row_count'] * 100) if previous_metrics['row_count'] > 0 else 0
        comparison['changes']['row_count'] = {
            'current': current_metrics['row_count'],
            'previous': previous_metrics['row_count'],
            'change': row_count_change,
            'change_percentage': round(row_count_pct, 2)
        }
        
        # Quality score change
        current_score = current_metrics['validation']['quality_score']
        previous_score = previous_metrics['validation']['quality_score']
        score_change = current_score - previous_score
        comparison['changes']['quality_score'] = {
            'current': current_score,
            'previous': previous_score,
            'change': round(score_change, 2)
        }
        
        # Missing values change
        current_missing = current_metrics['missing_values']['total_missing_cells']
        previous_missing = previous_metrics['missing_values']['total_missing_cells']
        missing_change = current_missing - previous_missing
        comparison['changes']['missing_values'] = {
            'current': current_missing,
            'previous': previous_missing,
            'change': missing_change
        }
        
        # Alert if significant changes
        alerts = []
        if abs(row_count_pct) > 10:
            alerts.append(f"Row count changed by {row_count_pct:.1f}%")
        if abs(score_change) > 5:
            alerts.append(f"Quality score changed by {score_change:.1f} points")
        if missing_change > 100:
            alerts.append(f"Missing values increased by {missing_change}")
        
        comparison['alerts'] = alerts
        
        return comparison
    
    def generate_quality_report(self, df: pd.DataFrame, dataset_name: str = 'customers') -> str:
        """
        Generate a human-readable quality report.
        
        Args:
            df: DataFrame to analyze
            dataset_name: Name of the dataset
            
        Returns:
            Formatted report string
        """
        metrics = self.collect_metrics(df, dataset_name)
        
        report = f"""
{'='*80}
DATA QUALITY REPORT - {dataset_name.upper()}
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DATASET OVERVIEW
{'─'*80}
Rows:               {metrics['row_count']:,}
Columns:            {metrics['column_count']}
Memory Usage:       {metrics['basic_stats']['memory_usage_mb']:.2f} MB
Duplicate Rows:     {metrics['basic_stats']['duplicate_rows']} ({metrics['basic_stats']['duplicate_percentage']:.2f}%)

📈 DATA QUALITY SCORE
{'─'*80}
Overall Score:      {metrics['validation']['quality_score']:.1f}/100
Validation Status:  {'✅ PASSED' if metrics['validation']['passed'] else '❌ FAILED'}
Total Checks:       {metrics['validation']['total_checks']}
Failed Checks:      {metrics['validation']['failed_checks']}

🔍 MISSING VALUES
{'─'*80}
Total Missing:      {metrics['missing_values']['total_missing_cells']}
Columns Affected:   {metrics['missing_values']['columns_with_missing']}
"""
        
        if metrics['missing_values']['by_column']:
            report += "\nTop Columns with Missing Values:\n"
            for col_stats in metrics['missing_values']['by_column'][:5]:
                report += f"  • {col_stats['column']}: {col_stats['missing_count']} ({col_stats['missing_percentage']:.1f}%)\n"
        
        # Errors
        if metrics['validation']['errors']:
            report += f"\n❌ VALIDATION ERRORS ({len(metrics['validation']['errors'])})\n"
            report += '─'*80 + '\n'
            for error in metrics['validation']['errors'][:5]:
                report += f"  • {error['rule']}: {error['failed_count']} issues ({error['failed_percentage']:.1f}%)\n"
                report += f"    {error['description']}\n"
        
        # Warnings
        if metrics['validation']['warnings']:
            report += f"\n⚠️  VALIDATION WARNINGS ({len(metrics['validation']['warnings'])})\n"
            report += '─'*80 + '\n'
            for warning in metrics['validation']['warnings'][:5]:
                report += f"  • {warning['rule']}: {warning['failed_count']} issues ({warning['failed_percentage']:.1f}%)\n"
        
        report += '\n' + '='*80 + '\n'
        
        return report
    
    def monitor_and_alert(self, df: pd.DataFrame, dataset_name: str = 'customers', alert_threshold: float = 70.0) -> bool:
        """
        Monitor data quality and return alert status.
        
        Args:
            df: DataFrame to monitor
            dataset_name: Name of the dataset
            alert_threshold: Minimum acceptable quality score
            
        Returns:
            True if quality is acceptable, False if alert triggered
        """
        metrics = self.collect_metrics(df, dataset_name)
        quality_score = metrics['validation']['quality_score']
        
        # Save metrics
        self.save_metrics(metrics, dataset_name)
        
        # Check threshold
        if quality_score < alert_threshold:
            logger.warning(
                f"🚨 DATA QUALITY ALERT: {dataset_name} quality score ({quality_score:.1f}) "
                f"is below threshold ({alert_threshold})"
            )
            return False
        
        logger.info(f"✅ Data quality acceptable: {quality_score:.1f}/100")
        return True


if __name__ == "__main__":
    # Test monitoring
    test_data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003', 'C004'],
        'tenure_months': [12, 24, 36, np.nan],
        'monthly_charges': [50.0, 75.0, 100.0, 85.0],
        'contract_duration': ['Monthly', 'Yearly', 'Two-Year', 'Monthly'],
        'extracted_at': [datetime.now()] * 4
    })
    
    monitor = DataQualityMonitor()
    
    # Collect metrics
    metrics = monitor.collect_metrics(test_data, 'test_dataset')
    print(f"\n📊 Quality Score: {metrics['validation']['quality_score']}/100")
    
    # Generate report
    report = monitor.generate_quality_report(test_data, 'test_dataset')
    print(report)
    
    # Monitor and alert
    is_ok = monitor.monitor_and_alert(test_data, 'test_dataset', alert_threshold=70.0)
    print(f"\n{'✅' if is_ok else '❌'} Quality check: {'Passed' if is_ok else 'Failed'}")
