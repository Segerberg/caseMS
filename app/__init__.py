from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import sqlite3

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def get_db_connection():
    from flask import current_app
    conn = sqlite3.connect(
        current_app.config['DATABASE_PATH'],
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    conn.row_factory = sqlite3.Row
    return conn


def create_app(config_class=None):
    # Initialize Flask app
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        from config import Config
        app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Import models
        from app.models.user import User

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Import and register blueprints
        from app.routes.auth import auth_bp
        from app.routes.cases import cases_bp
        from app.routes.api import api_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(cases_bp)
        app.register_blueprint(api_bp)

        # Create tables for SQLAlchemy models
        db.create_all()

        # Initialize tables from schema.sql
        db_path = app.config['DATABASE_PATH']
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schema.sql')

        print(f"Database path: {db_path}")
        print(f"Schema path: {schema_path}")

        # Check if database file exists or is empty
        db_exists = os.path.exists(db_path)
        db_empty = db_exists and os.path.getsize(db_path) < 10000

        if not db_exists or db_empty:
            print("Creating database tables from schema.sql...")
            try:
                # Get absolute path to schema.sql
                with sqlite3.connect(db_path) as conn:
                    with open(schema_path, 'r') as f:
                        conn.executescript(f.read())
                print("Database tables created successfully")
            except Exception as e:
                print(f"Error initializing database: {e}")
        else:
            print("Database already exists and has content.")

    return app