"""
Data package initialization.
Provides database connectivity, data extraction, and validation.
"""

from .database import get_database, init_database, SingleStoreConnection
from .extractors import CustomerDataExtractor, extract_customers
from .validators import DataValidator, MissingValueHandler, ValidationResult

__all__ = [
    'get_database',
    'init_database',
    'SingleStoreConnection',
    'CustomerDataExtractor',
    'extract_customers',
    'DataValidator',
    'MissingValueHandler',
    'ValidationResult'
]
