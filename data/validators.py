# ============================================================================
# Data Validators
# ============================================================================
# Validates data quality and integrity for churn prediction pipeline

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Represents a single validation rule."""
    name: str
    column: str
    rule_type: str  # 'range', 'not_null', 'unique', 'values', 'pattern'
    params: Dict[str, Any] = field(default_factory=dict)
    severity: str = 'error'  # 'error' or 'warning'
    description: str = ''


@dataclass
class ValidationResult:
    """Results from data validation."""
    passed: bool
    total_checks: int
    failed_checks: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'passed': self.passed,
            'total_checks': self.total_checks,
            'failed_checks': self.failed_checks,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat()
        }


class DataValidator:
    """
    Validates customer data quality and integrity.
    """
    
    def __init__(self):
        """Initialize data validator with predefined rules."""
        self.rules = self._define_rules()
    
    def _define_rules(self) -> List[ValidationRule]:
        """Define validation rules for customer data."""
        return [
            # Required fields
            ValidationRule(
                name='customer_id_not_null',
                column='customer_id',
                rule_type='not_null',
                severity='error',
                description='Customer ID must not be null'
            ),
            ValidationRule(
                name='customer_id_unique',
                column='customer_id',
                rule_type='unique',
                severity='error',
                description='Customer ID must be unique'
            ),
            
            # Tenure validation
            ValidationRule(
                name='tenure_positive',
                column='tenure_months',
                rule_type='range',
                params={'min': 0, 'max': 100},
                severity='error',
                description='Tenure must be between 0 and 100 months'
            ),
            
            # Charges validation
            ValidationRule(
                name='monthly_charges_range',
                column='monthly_charges',
                rule_type='range',
                params={'min': 0, 'max': 500},
                severity='error',
                description='Monthly charges must be between $0 and $500'
            ),
            ValidationRule(
                name='total_charges_positive',
                column='total_charges',
                rule_type='range',
                params={'min': 0, 'max': 10000},
                severity='warning',
                description='Total charges should be positive and under $10,000'
            ),
            
            # Service calls validation
            ValidationRule(
                name='service_calls_range',
                column='service_calls',
                rule_type='range',
                params={'min': 0, 'max': 50},
                severity='warning',
                description='Service calls should be between 0 and 50'
            ),
            
            # Categorical validations
            ValidationRule(
                name='contract_duration_values',
                column='contract_duration',
                rule_type='values',
                params={'allowed_values': ['Monthly', 'Yearly', 'Two-Year']},
                severity='error',
                description='Contract duration must be Monthly, Yearly, or Two-Year'
            ),
            ValidationRule(
                name='payment_method_values',
                column='payment_method',
                rule_type='values',
                params={'allowed_values': ['Electronic', 'Credit Card', 'Bank Transfer', 'Mailed Check']},
                severity='error',
                description='Payment method must be valid'
            ),
            
            # Score validations (normalized features)
            ValidationRule(
                name='paperless_billing_range',
                column='paperless_billing',
                rule_type='range',
                params={'min': -3, 'max': 3},
                severity='warning',
                description='Paperless billing score should be normalized'
            ),
            ValidationRule(
                name='tech_support_range',
                column='tech_support',
                rule_type='range',
                params={'min': -3, 'max': 3},
                severity='warning',
                description='Tech support score should be normalized'
            ),
        ]
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Run all validation rules on the DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult with all check results
        """
        logger.info(f"Starting validation on {len(df)} records")
        
        errors = []
        warnings = []
        total_checks = len(self.rules)
        
        for rule in self.rules:
            try:
                check_result = self._apply_rule(df, rule)
                
                if not check_result['passed']:
                    issue = {
                        'rule': rule.name,
                        'column': rule.column,
                        'description': rule.description,
                        'failed_count': check_result['failed_count'],
                        'failed_percentage': check_result['failed_percentage'],
                        'sample_values': check_result.get('sample_failures', [])
                    }
                    
                    if rule.severity == 'error':
                        errors.append(issue)
                    else:
                        warnings.append(issue)
                        
            except Exception as e:
                logger.error(f"Error applying rule {rule.name}: {str(e)}")
                errors.append({
                    'rule': rule.name,
                    'column': rule.column,
                    'description': f"Validation failed with error: {str(e)}",
                    'failed_count': 0,
                    'failed_percentage': 0.0
                })
        
        failed_checks = len(errors)
        passed = failed_checks == 0
        
        result = ValidationResult(
            passed=passed,
            total_checks=total_checks,
            failed_checks=failed_checks,
            errors=errors,
            warnings=warnings
        )
        
        if passed:
            logger.info("✅ All validation checks passed")
        else:
            logger.warning(f"⚠️  Validation failed: {failed_checks} errors, {len(warnings)} warnings")
        
        return result
    
    def _apply_rule(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Apply a single validation rule."""
        if rule.column not in df.columns:
            return {
                'passed': False,
                'failed_count': len(df),
                'failed_percentage': 100.0,
                'sample_failures': []
            }
        
        if rule.rule_type == 'not_null':
            return self._check_not_null(df, rule)
        elif rule.rule_type == 'unique':
            return self._check_unique(df, rule)
        elif rule.rule_type == 'range':
            return self._check_range(df, rule)
        elif rule.rule_type == 'values':
            return self._check_values(df, rule)
        else:
            return {'passed': True, 'failed_count': 0, 'failed_percentage': 0.0}
    
    def _check_not_null(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Check for null values."""
        null_count = df[rule.column].isna().sum()
        total = len(df)
        percentage = (null_count / total * 100) if total > 0 else 0
        
        return {
            'passed': null_count == 0,
            'failed_count': null_count,
            'failed_percentage': percentage
        }
    
    def _check_unique(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Check for duplicate values."""
        duplicates = df[rule.column].duplicated().sum()
        total = len(df)
        percentage = (duplicates / total * 100) if total > 0 else 0
        
        sample_failures = df[df[rule.column].duplicated(keep=False)][rule.column].head(5).tolist()
        
        return {
            'passed': duplicates == 0,
            'failed_count': duplicates,
            'failed_percentage': percentage,
            'sample_failures': sample_failures
        }
    
    def _check_range(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Check if values are within range."""
        min_val = rule.params.get('min', -np.inf)
        max_val = rule.params.get('max', np.inf)
        
        out_of_range = ((df[rule.column] < min_val) | (df[rule.column] > max_val)).sum()
        total = len(df)
        percentage = (out_of_range / total * 100) if total > 0 else 0
        
        sample_failures = df[
            (df[rule.column] < min_val) | (df[rule.column] > max_val)
        ][rule.column].head(5).tolist()
        
        return {
            'passed': out_of_range == 0,
            'failed_count': out_of_range,
            'failed_percentage': percentage,
            'sample_failures': sample_failures
        }
    
    def _check_values(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Check if values are in allowed list."""
        allowed_values = rule.params.get('allowed_values', [])
        invalid = (~df[rule.column].isin(allowed_values + [None, np.nan])).sum()
        total = len(df)
        percentage = (invalid / total * 100) if total > 0 else 0
        
        sample_failures = df[~df[rule.column].isin(allowed_values)][rule.column].unique()[:5].tolist()
        
        return {
            'passed': invalid == 0,
            'failed_count': invalid,
            'failed_percentage': percentage,
            'sample_failures': sample_failures
        }
    
    def get_data_quality_score(self, df: pd.DataFrame) -> float:
        """
        Calculate overall data quality score (0-100).
        
        Args:
            df: DataFrame to score
            
        Returns:
            Quality score between 0 and 100
        """
        result = self.validate(df)
        
        if result.total_checks == 0:
            return 100.0
        
        # Weight errors more than warnings
        error_weight = 1.0
        warning_weight = 0.3
        
        error_penalty = len(result.errors) * error_weight
        warning_penalty = len(result.warnings) * warning_weight
        
        total_penalty = error_penalty + warning_penalty
        max_penalty = result.total_checks * error_weight
        
        score = max(0, 100 * (1 - total_penalty / max_penalty))
        
        return round(score, 2)


class MissingValueHandler:
    """Handles missing values and outliers in customer data."""
    
    @staticmethod
    def detect_missing(df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect missing values in DataFrame.
        
        Returns:
            DataFrame with missing value statistics
        """
        missing_stats = pd.DataFrame({
            'column': df.columns,
            'missing_count': df.isna().sum().values,
            'missing_percentage': (df.isna().sum() / len(df) * 100).values,
            'dtype': df.dtypes.values
        })
        
        missing_stats = missing_stats[missing_stats['missing_count'] > 0].sort_values(
            'missing_percentage', ascending=False
        )
        
        return missing_stats
    
    @staticmethod
    def impute_missing(df: pd.DataFrame, strategy: str = 'median') -> pd.DataFrame:
        """
        Impute missing values.
        
        Args:
            df: DataFrame with missing values
            strategy: 'median', 'mean', 'mode', or 'forward_fill'
            
        Returns:
            DataFrame with imputed values
        """
        df = df.copy()
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if strategy == 'median':
            for col in numeric_cols:
                df[col].fillna(df[col].median(), inplace=True)
        elif strategy == 'mean':
            for col in numeric_cols:
                df[col].fillna(df[col].mean(), inplace=True)
        elif strategy == 'mode':
            for col in categorical_cols:
                df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown', inplace=True)
        elif strategy == 'forward_fill':
            df.fillna(method='ffill', inplace=True)
        
        # Fill remaining categorical nulls with 'Unknown'
        for col in categorical_cols:
            df[col].fillna('Unknown', inplace=True)
        
        logger.info(f"Missing values imputed using strategy: {strategy}")
        return df
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
        """
        Detect outliers in a column.
        
        Args:
            df: DataFrame
            column: Column name to check
            method: 'iqr' or 'zscore'
            threshold: Threshold for outlier detection
            
        Returns:
            Boolean Series indicating outliers
        """
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            return (df[column] < lower_bound) | (df[column] > upper_bound)
        
        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(df[column].dropna()))
            return z_scores > threshold
        
        return pd.Series([False] * len(df))
    
    @staticmethod
    def handle_outliers(df: pd.DataFrame, column: str, method: str = 'clip') -> pd.DataFrame:
        """
        Handle outliers in a column.
        
        Args:
            df: DataFrame
            column: Column to handle
            method: 'clip', 'remove', or 'log_transform'
            
        Returns:
            DataFrame with outliers handled
        """
        df = df.copy()
        
        if method == 'clip':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df[column] = df[column].clip(lower_bound, upper_bound)
            
        elif method == 'remove':
            outliers = MissingValueHandler.detect_outliers(df, column)
            df = df[~outliers]
            
        elif method == 'log_transform':
            df[column] = np.log1p(df[column])
        
        logger.info(f"Outliers handled in {column} using method: {method}")
        return df


if __name__ == "__main__":
    # Test validation
    test_data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003'],
        'tenure_months': [12, 24, -5],  # Invalid: negative tenure
        'monthly_charges': [50.0, 75.0, 600.0],  # Invalid: > 500
        'contract_duration': ['Monthly', 'Yearly', 'Invalid'],  # Invalid value
        'paperless_billing': [0.5, 1.0, 0.8]
    })
    
    validator = DataValidator()
    result = validator.validate(test_data)
    
    print("\n📊 Validation Results:")
    print(f"  Passed: {result.passed}")
    print(f"  Total Checks: {result.total_checks}")
    print(f"  Failed Checks: {result.failed_checks}")
    print(f"\n❌ Errors: {len(result.errors)}")
    for error in result.errors:
        print(f"  - {error['rule']}: {error['description']}")
    
    print(f"\n⚠️  Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        print(f"  - {warning['rule']}: {warning['description']}")
    
    quality_score = validator.get_data_quality_score(test_data)
    print(f"\n🎯 Data Quality Score: {quality_score}/100")
