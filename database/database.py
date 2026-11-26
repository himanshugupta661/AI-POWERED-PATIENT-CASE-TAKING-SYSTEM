from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask application."""
    db.init_app(app)
    with app.app_context():
        # Ensure instance directory exists
        import os
        instance_dir = os.path.join(app.root_path, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db.create_all()
