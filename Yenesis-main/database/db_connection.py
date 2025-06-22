import mysql.connector
from mysql.connector import Error
import os
import sys
from utilities.log_util import get_logger

# Try to import from resources first, fall back to config if not found
try:
    from resources.db_config import DATABASE_CONFIG, get_db_config
except ImportError:
    from config import DATABASE_CONFIG, get_db_config

logger = get_logger()

class DatabaseConnection:
    """
    A class to manage database connections for Yenesis.
    This handles connecting to a MySQL database and provides basic operations.
    Reads configuration from config.py but allows override via constructor parameters.
    """
    
    def __init__(self, host=None, user=None, password=None, database=None, port=None, **kwargs):
        """Initialize database connection parameters"""
        # First try constructor parameters
        # Then try environment variables
        # Finally fall back to config values
        self.host = host or os.environ.get('MYSQL_HOST', DATABASE_CONFIG.get('host', 'localhost'))
        self.user = user or os.environ.get('MYSQL_USER', DATABASE_CONFIG.get('user', 'root'))
        self.password = password or os.environ.get('MYSQL_PASSWORD', DATABASE_CONFIG.get('password', ''))
        self.database = database or os.environ.get('MYSQL_DATABASE', DATABASE_CONFIG.get('database', 'yenesis_market_data'))
        self.port = port or os.environ.get('MYSQL_PORT', DATABASE_CONFIG.get('port', 3306))
        
        # Additional connection options from config
        self.options = DATABASE_CONFIG.get('options', {})
        
        # Override with any additional kwargs
        self.options.update(kwargs)
        
        self.connection = None
    
    def connect(self):
        """Create a connection to the MySQL database using config parameters"""
        try:
            # Basic connection parameters
            connection_params = {
                'host': self.host,
                'user': self.user,
                'password': self.password,
                'database': self.database,
                'port': self.port
            }
            
            # Add additional options from config
            for key, value in self.options.items():
                if key not in connection_params:  # Don't override basic params
                    connection_params[key] = value
            
            self.connection = mysql.connector.connect(**connection_params)
            
            if self.connection.is_connected():
                logger.info(f"Connected to MySQL database: {self.database} at {self.host}:{self.port}")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
    
    def execute_query(self, query, params=None, fetch=False, multi=False):
        """
        Execute a SQL query with optional parameters
        
        Parameters:
            query (str): SQL query to execute
            params (tuple or list of tuples): Query parameters
            fetch (bool): Whether to fetch results
            multi (bool): Whether params contains multiple sets of parameters for batch execution
            
        Returns:
            For SELECT: List of dictionaries with results (if fetch=True)
            For INSERT/UPDATE/DELETE: Number of affected rows
            For other queries: True if successful
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            # Handle different query execution scenarios
            if multi and params:
                cursor.executemany(query, params)
            elif params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Handle different return values based on query type
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                self.connection.commit()
                rows_affected = cursor.rowcount
                cursor.close()
                return rows_affected
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
                
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error executing query: {e}")
            # Print detailed error information for debugging
            logger.error(f"Query: {query}")
            if params and not multi:
                logger.error(f"Params: {params}")
            elif params and multi:
                logger.error(f"Batch size: {len(params)}")
            return None
    
    def create_schema_if_not_exists(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect to MySQL server without specifying a database
            conn_params = {
                'host': self.host,
                'user': self.user,
                'password': self.password,
                'port': self.port
            }
            
            # Add relevant connection options
            for key, value in self.options.items():
                if key not in ['database', 'db'] and key not in conn_params:
                    conn_params[key] = value
            
            conn = mysql.connector.connect(**conn_params)
            
            if conn.is_connected():
                cursor = conn.cursor()
                # Create the database if it doesn't exist
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                cursor.close()
                conn.close()
                logger.info(f"Database '{self.database}' created or already exists")
                return True
        except Error as e:
            logger.error(f"Error creating database schema: {e}")
            return False
