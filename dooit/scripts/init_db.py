#!/usr/bin/env python3
"""
Standalone script to initialize the dooit database without launching the CLI.
"""

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

def init_database(db_path: Optional[str] = None):
    """
    Initialize the dooit database.
    
    Args:
        db_path: Optional path to SQLite database file
    """
    # Check required environment variables
    if 'DATABASE_CONN_STRING' not in os.environ:
        raise Exception("DATABASE_CONN_STRING environment variable is not set")
    
    DATABASE_CONN_STRING = os.environ['DATABASE_CONN_STRING']
    
    # Import models to ensure they're registered with SQLAlchemy
    from dooit.api import BaseModel, Todo, Workspace
    
    # Create engine and session
    engine = create_engine(DATABASE_CONN_STRING)
    session = Session(engine)
    
    # Check existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Create all tables
    print("Creating database tables...")
    BaseModel.metadata.create_all(bind=engine)
    
    print("Database initialization complete!")
    
    # Close the session
    session.close()
    engine.dispose()


if __name__ == "__main__":
    import sys
    
    # Optional: Accept database path from command line
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        init_database(db_path)
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)