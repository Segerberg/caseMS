import os


class Config:
    # Application configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')

    # Database configuration
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASEDIR, 'case_management.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False