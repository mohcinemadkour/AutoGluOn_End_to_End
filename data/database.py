# ============================================================================
# SingleStore Database Connection Manager
# ============================================================================
# Manages connections to SingleStore database for customer data extraction

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SingleStoreConnection:
    """
    Manages SingleStore database connections with connection pooling
    and automatic reconnection handling.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600
    ):
        """
        Initialize SingleStore connection manager.
        
        Args:
            host: SingleStore host (defaults to env variable SINGLESTORE_HOST)
            port: SingleStore port (defaults to env variable SINGLESTORE_PORT or 3306)
            database: Database name (defaults to env variable SINGLESTORE_DATABASE)
            user: Database user (defaults to env variable SINGLESTORE_USER)
            password: Database password (defaults to env variable SINGLESTORE_PASSWORD)
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_recycle: Time to recycle connections (seconds)
        """
        self.host = host or os.getenv('SINGLESTORE_HOST', 'localhost')
        self.port = port or int(os.getenv('SINGLESTORE_PORT', '3306'))
        self.database = database or os.getenv('SINGLESTORE_DATABASE', 'churn_db')
        self.user = user or os.getenv('SINGLESTORE_USER', 'admin')
        self.password = password or os.getenv('SINGLESTORE_PASSWORD', '')
        
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        
        self._engine: Optional[Engine] = None
        self._session_factory = None
        
        logger.info(f"Initializing SingleStore connection to {self.host}:{self.port}/{self.database}")
    
    def _create_connection_string(self) -> str:
        """Create SQLAlchemy connection string for SingleStore."""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )
    
    @property
    def engine(self) -> Engine:
        """Get or create database engine."""
        if self._engine is None:
            connection_string = self._create_connection_string()
            self._engine = create_engine(
                connection_string,
                poolclass=pool.QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
                echo=False
            )
            logger.info("Database engine created successfully")
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Usage:
            with db.get_session() as session:
                result = session.execute("SELECT * FROM customers")
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Execute a query and return results as a pandas DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
                logger.info(f"Query executed successfully, returned {len(df)} rows")
                return df
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_write(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute a write query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, params or {})
                conn.commit()
                logger.info(f"Write query executed, {result.rowcount} rows affected")
                return result.rowcount
        except Exception as e:
            logger.error(f"Write query failed: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """
        Get information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            DataFrame with column information
        """
        query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_KEY,
            EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{self.database}'
        AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return int(result['count'].iloc[0])
    
    def close(self):
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# Singleton instance
_db_instance: Optional[SingleStoreConnection] = None


def get_database() -> SingleStoreConnection:
    """
    Get singleton database connection instance.
    
    Returns:
        SingleStoreConnection instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = SingleStoreConnection()
    return _db_instance


def init_database(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> SingleStoreConnection:
    """
    Initialize database connection with custom parameters.
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        
    Returns:
        SingleStoreConnection instance
    """
    global _db_instance
    _db_instance = SingleStoreConnection(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    return _db_instance


# Example usage
if __name__ == "__main__":
    # Test connection
    db = get_database()
    
    if db.test_connection():
        print("✅ Database connection successful!")
        
        # Example query
        try:
            result = db.execute_query("SELECT DATABASE() as current_db")
            print(f"\nCurrent database: {result['current_db'].iloc[0]}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
    else:
        print("❌ Database connection failed!")
