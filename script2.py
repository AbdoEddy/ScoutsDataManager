# File: migrate_postgres_recreate_table_permissions.py

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# --- Database Configuration ---
# Ensure this is your correct PostgreSQL connection string.
DATABASE_URL = "postgresql://myuser:mypassword@localhost:5432/scout_manager"
# --- End Database Configuration ---

def recreate_table_permissions_for_postgres():
    """
    Recreates the 'table_permissions' table in PostgreSQL to ensure 'field_id'
    is nullable and the schema matches the desired structure.
    This method involves creating a new table, copying data, dropping the old
    table, and renaming the new one.
    """
    display_url = DATABASE_URL
    try:
        uri_parts = sqlalchemy.engine.url.make_url(DATABASE_URL)
        if uri_parts.password:
            display_url = f"{uri_parts.drivername}://{uri_parts.username}:***@{uri_parts.host or ''}:{uri_parts.port or ''}/{uri_parts.database or ''}"
        else:
            display_url = f"{uri_parts.drivername}://{uri_parts.username}@{uri_parts.host or ''}:{uri_parts.port or ''}/{uri_parts.database or ''}"
    except Exception:
        display_url = "postgresql://USER:***@HOST:PORT/DBNAME (details in script)"

    print(f"Attempting to connect directly to PostgreSQL database: {display_url}")

    engine = None
    session = None

    # IMPORTANT: Define the schema for the new table carefully.
    # This should match your intended final schema for table_permissions.
    # 'id SERIAL PRIMARY KEY' makes 'id' an auto-incrementing primary key in PostgreSQL.
    # 'field_id INTEGER' without 'NOT NULL' makes it nullable.
    # 'all_access BOOLEAN DEFAULT FALSE' is the PostgreSQL equivalent of 'DEFAULT 0'.
    # 'created_at TIMESTAMP WITHOUT TIME ZONE' is for date/time.
    create_new_table_sql = text("""
        CREATE TABLE table_permissions_new (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            field_id INTEGER, -- Nullable
            match_value VARCHAR(255),
            all_access BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id),
            CONSTRAINT fk_table FOREIGN KEY (table_id) REFERENCES tables (id),
            CONSTRAINT fk_field FOREIGN KEY (field_id) REFERENCES table_fields (id)
        );
    """)

    # Ensure the column order in SELECT matches the implicit column order of
    # table_permissions_new if not specifying columns in INSERT.
    # Or, explicitly list columns: INSERT INTO table_permissions_new (id, user_id, ...) SELECT id, user_id, ...
    copy_data_sql = text("""
        INSERT INTO table_permissions_new (id, user_id, table_id, field_id, match_value, all_access, created_at)
        SELECT id, user_id, table_id, field_id, match_value, all_access, created_at
        FROM table_permissions;
    """)

    drop_old_table_sql = text("DROP TABLE table_permissions;")
    rename_new_table_sql = text("ALTER TABLE table_permissions_new RENAME TO table_permissions;")

    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session() # Autocommit is false by default

        print("Starting transaction to recreate 'table_permissions' table...")

        print("Step 1: Creating 'table_permissions_new' with the new schema...")
        session.execute(create_new_table_sql)
        print("'table_permissions_new' created successfully.")

        print("Step 2: Copying data from old 'table_permissions' to 'table_permissions_new'...")
        result = session.execute(copy_data_sql)
        print(f"{result.rowcount} rows copied to 'table_permissions_new'.")

        print("Step 3: Dropping old 'table_permissions' table...")
        session.execute(drop_old_table_sql)
        print("Old 'table_permissions' table dropped successfully.")

        print("Step 4: Renaming 'table_permissions_new' to 'table_permissions'...")
        session.execute(rename_new_table_sql)
        print("'table_permissions_new' renamed to 'table_permissions' successfully.")

        session.commit()
        print("\nSuccessfully recreated 'table_permissions' table with 'field_id' nullable!")

    except SQLAlchemyError as e:
        if session:
            session.rollback()
            print("\nTransaction rolled back due to an SQLAlchemy error.")
        print(f"An SQLAlchemy error occurred: {e}")
        print("Please check the error message, your database schema (e.g., referenced tables like 'users', 'tables', 'table_fields' must exist), and user permissions.")
    except Exception as e:
        if session:
            session.rollback()
            print("\nTransaction rolled back due to an unexpected error.")
        print(f"An unexpected error occurred: {e}")
    finally:
        if session:
            session.close()
            print("Database session closed.")
        if engine:
            engine.dispose()
            print("Database engine connections disposed.")

if __name__ == "__main__":
    print("Starting script to recreate 'table_permissions' for PostgreSQL...")
    print("WARNING: This script performs major table operations (CREATE, INSERT, DROP, RENAME).")
    print("It is highly recommended to BACK UP YOUR DATABASE before running this script.")
    # Confirmation_prompt = input("Type 'YES' to continue, or anything else to abort: ")
    # if confirmation_prompt == "YES":
    recreate_table_permissions_for_postgres()
    # else:
    # print("Operation aborted by user.")
    print("Script finished.")
