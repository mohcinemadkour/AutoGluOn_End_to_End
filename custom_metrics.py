"""
Custom Metrics for AutoGluon Model
===================================
This module defines custom metrics used during model training.
Must be importable for model loading to work properly.
"""

from sklearn.metrics import precision_score, recall_score


def calculate_business_f1(y_true, y_pred, **kwargs):
    """
    Custom business F1 score function used during model training.
    
    This metric weights recall as beta-times more important than precision,
    which is useful for churn prediction where we want to catch most churners.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        **kwargs: Additional arguments (ignored)
        
    Returns:
        float: Business F1 score (0-1)
    """
    p = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    r = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    beta = 0.5  # Recall is beta-times more important
    
    if (beta**2 * p) + r == 0:
        return 0.0
    
    return (1 + beta**2) * (p * r) / ((beta**2 * p) + r)
