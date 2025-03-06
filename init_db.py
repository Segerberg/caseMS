import os
import sqlite3
from config import Config


def init_db():
    """Initialize the database with the schema.sql file"""
    db_path = Config.DATABASE_PATH
    schema_path = 'schema.sql'  # Adjust this path if needed

    print(f"Initializing database at: {db_path}")

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Connect to database and execute schema
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'r') as f:
            script = f.read()
            conn.executescript(script)

    print("Database initialized successfully!")


if __name__ == '__main__':
    # Delete the db file if it exists
    if os.path.exists(Config.DATABASE_PATH):
        os.remove(Config.DATABASE_PATH)
        print(f"Removed existing database at {Config.DATABASE_PATH}")

    init_db()