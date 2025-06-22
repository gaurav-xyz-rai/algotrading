"""
Sample Database Configuration for Yenesis point-in-time market database
This is a template that can be copied to resources/db_config.py and adjusted
"""

# Database configuration
DATABASE_CONFIG = {
    # Basic connection parameters
    "host": "localhost",     # Database server hostname or IP
    "user": "yenesis_user",  # Database username
    "password": "secure_password_here",  # Database password
    "database": "yenesis_market_data",   # Database name
    "port": 3306,            # MySQL default port
    
    # Connection options
    "options": {
        "pool_size": 5,         # Number of connections in pool
        "pool_recycle": 3600,   # Recycle connections after 1 hour
        "connect_timeout": 10,  # Connection timeout in seconds
        "use_unicode": True,    # Use Unicode for string encoding
        "charset": "utf8mb4",   # Character set for strings
        
        # Additional MySQL-specific options
        "autocommit": True,     # Auto-commit transactions
        "buffered": True,       # Use buffered cursors
    }
}

def get_db_config():
    """Returns the database configuration dictionary"""
    return DATABASE_CONFIG.copy()
