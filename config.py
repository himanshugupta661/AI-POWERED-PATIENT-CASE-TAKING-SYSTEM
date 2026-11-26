import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'patientcase-ai-dev-secret-key-2026-alpha')
    
    # SQLite Database URI
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'patientcase.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Application metadata
    APP_NAME = "PATIENTCASE AI"
    APP_TAGLINE = "Smarter Case-Taking for Better Care"
    APP_VERSION = "1.0.0"
    
    # AI service configuration
    AI_ENABLED = True
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'rule_based')  # 'rule_based', 'local', or 'external'
    
    # Access token expiration in hours
    CASE_ACCESS_TOKEN_EXPIRY_HOURS = 72

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

class ProductionConfig(Config):
    DEBUG = False
    # In production, require actual secure secret keys
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
