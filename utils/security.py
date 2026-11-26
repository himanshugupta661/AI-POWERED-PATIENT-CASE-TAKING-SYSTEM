import secrets
import hashlib
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, current_app
from database.models import User

def generate_random_token(length=32):
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)

def hash_token(token_string):
    """Generate SHA-256 hash of a token for storage."""
    return hashlib.sha256(token_string.encode('utf-8')).hexdigest()

def generate_csrf_token():
    """Generate or retrieve a CSRF token for the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(24)
    return session['_csrf_token']

def validate_csrf(token):
    """Validate submitted CSRF token against session."""
    if not current_app.config.get('WTF_CSRF_ENABLED', True):
        return True
    expected = session.get('_csrf_token')
    if not expected or not token:
        return False
    return secrets.compare_digest(expected, token)

def get_current_user():
    """Fetch the currently logged-in user or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    from database.database import db
    return db.session.get(User, user_id)

def login_required(f):
    """Ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def patient_required(f):
    """Ensure authenticated user is a patient."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as a patient to continue.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        
        user = get_current_user()
        if not user or user.role != 'patient':
            flash('This area is reserved for patients.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    """Ensure authenticated user is a doctor."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in with doctor credentials to continue.', 'warning')
            return redirect(url_for('auth.doctor_login', next=request.path))
        
        user = get_current_user()
        if not user or user.role != 'doctor':
            flash('Access restricted: Doctor credentials required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
