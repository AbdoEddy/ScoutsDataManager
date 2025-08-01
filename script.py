# File: migrate_postgres_add_all_access_column_direct_db.py

import sqlalchemy # Used for parsing the URL for display
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# --- Database Configuration ---
# This DATABASE_URL will be used directly by this script to connect to PostgreSQL.
# Replace with your actual connection string if different.
DATABASE_URL = "postgresql://myuser:mypassword@localhost:5432/scout_manager"
# --- End Database Configuration ---

def add_all_access_column_directly():
    """
    Connects directly to the PostgreSQL database using the specified DATABASE_URL
    and ensures the 'all_access' column exists in the 'table_permissions' table.

    This version uses 'ADD COLUMN IF NOT EXISTS', which requires PostgreSQL 9.6+.
    It sets the column as BOOLEAN with a DEFAULT value of FALSE.
    """
    
    # Mask credentials for printing the URL
    display_url = DATABASE_URL
    try:
        uri_parts = sqlalchemy.engine.url.make_url(DATABASE_URL)
        if uri_parts.password: # Check if password exists before trying to mask
            display_url = f"{uri_parts.drivername}://{uri_parts.username}:***@{uri_parts.host or ''}:{uri_parts.port or ''}/{uri_parts.database or ''}"
        else:
            display_url = f"{uri_parts.drivername}://{uri_parts.username}@{uri_parts.host or ''}:{uri_parts.port or ''}/{uri_parts.database or ''}"

    except Exception:
        # If parsing fails for any reason, print a generic message or the raw URL carefully
        display_url = "postgresql://USER:***@HOST:PORT/DBNAME (details in script)"
        # For safety, avoid printing the raw DATABASE_URL here if parsing fails.

    print(f"Attempting to connect directly to PostgreSQL database: {display_url}")

    engine = None
    session = None

    try:
        # Create a new SQLAlchemy engine with the specified URL
        engine = create_engine(DATABASE_URL)
        
        # Create a session factory and then a session instance
        Session = sessionmaker(bind=engine)
        session = Session()

        # PostgreSQL-specific DDL to add the column if it doesn't exist.
        # 'IF NOT EXISTS' makes the operation idempotent (safe to run multiple times).
        # This requires PostgreSQL 9.6 or newer.
        alter_table_sql = text("""
            ALTER TABLE table_permissions
            ADD COLUMN IF NOT EXISTS all_access BOOLEAN DEFAULT FALSE;
        """)

        print("Executing DDL on 'table_permissions' using direct database connection...")
        session.execute(alter_table_sql)
        session.commit()
        print("Successfully ensured 'all_access' column (BOOLEAN DEFAULT FALSE) exists in 'table_permissions' table.")
        print("If the column already existed, PostgreSQL's 'IF NOT EXISTS' clause prevented an error and no change was made to the column itself.")

    except SQLAlchemyError as e:
        if session:
            session.rollback()
        print(f"\nAn SQLAlchemy error occurred: {e}")
        print("Common causes:")
        print("  - Incorrect DATABASE_URL (double-check username, password, host, port, database name).")
        print("  - PostgreSQL server not running or inaccessible from where this script is executed.")
        print("  - Network connectivity issues (firewalls, etc.).")
        print("  - Insufficient database user permissions for 'myuser' to ALTER TABLE.")
        print("  - The table 'table_permissions' does not exist (check for typos).")
    except Exception as e: # Catch any other unexpected errors
        if session:
            session.rollback()
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if session:
            session.close()
            print("Database session closed.")
        if engine:
            # Dispose of the engine to close all underlying database connections
            engine.dispose()
            print("Database engine connections disposed.")

if __name__ == "__main__":
    print("Starting migration script for 'table_permissions' on PostgreSQL (using direct DB connection from script)...")
    add_all_access_column_directly()
    print("Migration script finished.")
