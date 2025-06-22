"""
Database Configuration for Yenesis point-in-time market database
"""

# Database configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "yenesis_market_data",
    "port": 3306,
    
    # Connection options
    "options": {
        "pool_size": 5,  # Number of connections in pool
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "connect_timeout": 10,  # Connection timeout in seconds
        "use_unicode": True,
        "charset": "utf8mb4",
    }
}

def get_db_config():
    """Returns the database configuration dictionary"""
    return DATABASE_CONFIG.copy()
