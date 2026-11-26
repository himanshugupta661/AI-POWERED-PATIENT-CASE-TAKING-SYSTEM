import os
from flask import Flask, render_template, session, redirect, url_for
from config import config_by_name
from database import db, init_db, User
from utils.security import get_current_user, generate_csrf_token
from utils.seed import seed_database
from routes import auth_bp, patient_bp, case_bp, doctor_bp, api_bp

def create_app(config_name=None):
    """Application factory for PatientCase AI."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize Database
    init_db(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(case_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(api_bp)

    # Global Context Processors
    @app.context_processor
    def inject_globals():
        user = get_current_user()
        return {
            'current_user': user,
            'csrf_token': generate_csrf_token(),
            'app_name': app.config.get('APP_NAME', 'PATIENTCASE AI'),
            'app_tagline': app.config.get('APP_TAGLINE', 'Smarter Case-Taking for Better Care'),
            'app_version': app.config.get('APP_VERSION', '1.0.0')
        }

    # Landing Page Route
    @app.route('/')
    def index():
        if 'user_id' in session:
            user = get_current_user()
            if user:
                if user.role == 'doctor':
                    return redirect(url_for('doctor.dashboard'))
                return redirect(url_for('patient.dashboard'))
        return render_template('index.html')

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # CLI command: flask seed-db
    @app.cli.command('seed-db')
    def seed_db_command():
        """Seed database with test doctor and patient accounts."""
        seed_database()
        print("Database seeded successfully via CLI command!")

    # Auto seed in development if database is empty
    with app.app_context():
        try:
            if not User.query.first():
                seed_database()
        except Exception as e:
            print(f"Initial seed notice: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
