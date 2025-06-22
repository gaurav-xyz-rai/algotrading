#!/usr/bin/env python3
"""
Helper script to generate a database configuration file in the resources directory
"""
import argparse
import os
import sys
from pathlib import Path

def generate_db_config(host, user, password, database, port=3306):
    """Generate database configuration template"""
    config_template = f'''"""
Database Configuration for Yenesis point-in-time market database
"""

# Database configuration
DATABASE_CONFIG = {{
    "host": "{host}",
    "user": "{user}",
    "password": "{password}",
    "database": "{database}",
    "port": {port},
    
    # Connection options
    "options": {{
        "pool_size": 5,  # Number of connections in pool
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "connect_timeout": 10,  # Connection timeout in seconds
        "use_unicode": True,
        "charset": "utf8mb4",
    }}
}}

def get_db_config():
    """Returns the database configuration dictionary"""
    return DATABASE_CONFIG.copy()
'''
    return config_template

def main():
    parser = argparse.ArgumentParser(description="Generate database configuration file in resources directory")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--user", default="root", help="Database user")
    parser.add_argument("--password", default="", help="Database password")
    parser.add_argument("--database", default="yenesis_market_data", help="Database name")
    parser.add_argument("--port", type=int, default=3306, help="Database port")
    parser.add_argument("--output", help="Output file to write config (if not specified, uses resources/db_config.py)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing file if it exists")
    
    args = parser.parse_args()
    
    config = generate_db_config(
        args.host, 
        args.user,
        args.password,
        args.database,
        args.port
    )
    
    # Determine output path
    output_path = args.output
    if not output_path:
        # Get the project root directory (2 levels up from this script)
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        project_root = script_dir.parent
        resources_dir = project_root / "resources"
        
        # Create resources directory if it doesn't exist
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
            # Create __init__.py if it doesn't exist
            init_file = resources_dir / "__init__.py"
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write("# Resources package for configuration and static files")
        
        output_path = resources_dir / "db_config.py"
    
    # Check if file exists and handle accordingly
    if os.path.exists(output_path) and not args.force:
        print(f"File {output_path} already exists. Use --force to overwrite.")
        return
    
    # Write config to file
    with open(output_path, 'w') as f:
        f.write(config)
    print(f"Database configuration written to {output_path}")

if __name__ == "__main__":
    main()
