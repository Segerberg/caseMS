import sqlite3
from flask import current_app, g
import os

def get_db():
    """Get a database connection. Store it in the g object if not already there."""
    if 'db' not in g:
        # Make sure we're using the correct path
        db_path = current_app.config['DATABASE_PATH']

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def execute_query(query, args=(), one=False, commit=False):
    """Execute a query and return the results."""
    db = get_db()
    cursor = db.execute(query, args)

    if commit:
        db.commit()
        return cursor.lastrowid

    if one:
        return cursor.fetchone()

    return cursor.fetchall()


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)