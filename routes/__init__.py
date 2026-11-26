from routes.auth_routes import auth_bp
from routes.patient_routes import patient_bp
from routes.case_routes import case_bp
from routes.doctor_routes import doctor_bp
from routes.api_routes import api_bp

__all__ = [
    'auth_bp',
    'patient_bp',
    'case_bp',
    'doctor_bp',
    'api_bp'
]
