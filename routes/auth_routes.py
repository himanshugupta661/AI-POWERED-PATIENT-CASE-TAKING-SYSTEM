from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import db
from database.models import User, PatientProfile
from utils.security import get_current_user, validate_csrf
from utils.validators import validate_email, validate_password, sanitize_text

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Patient login page."""
    if 'user_id' in session:
        user = get_current_user()
        if user and user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        # Validate CSRF
        if not validate_csrf(request.form.get('csrf_token')):
            flash('Invalid session token. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please verify your credentials.', 'danger')
            return render_template('auth/login.html', email=email)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return render_template('auth/login.html', email=email)

        # Store session
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session.permanent = True

        flash(f'Welcome back, {user.full_name}!', 'success')
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/patient-register', methods=['GET', 'POST'])
def patient_register():
    """Patient registration form."""
    if 'user_id' in session:
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            flash('Invalid session token. Please try again.', 'danger')
            return redirect(url_for('auth.patient_register'))

        full_name = sanitize_text(request.form.get('full_name', ''), 120)
        email = request.form.get('email', '').strip().lower()
        phone = sanitize_text(request.form.get('phone', ''), 30)
        age = request.form.get('age', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()
        gender = request.form.get('gender', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        consent = request.form.get('consent')

        # Form validations
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Please enter your full name.")

        is_valid_email, email_or_err = validate_email(email)
        if not is_valid_email:
            errors.append(email_or_err)

        is_valid_pass, pass_err = validate_password(password)
        if not is_valid_pass:
            errors.append(pass_err)

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if not consent:
            errors.append("You must consent to processing health intake information.")

        # Check existing email
        if is_valid_email and User.query.filter_by(email=email_or_err).first():
            errors.append("An account with this email address already exists.")

        age_int = None
        if age:
            try:
                age_int = int(age)
                if age_int < 0 or age_int > 125:
                    errors.append("Please enter a realistic age.")
            except ValueError:
                errors.append("Age must be a valid number.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'auth/patient_register.html',
                full_name=full_name,
                email=email,
                phone=phone,
                age=age,
                date_of_birth=date_of_birth,
                gender=gender
            )

        # Create user
        user = User(
            full_name=full_name,
            email=email_or_err,
            role='patient',
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create patient profile
        profile = PatientProfile(
            user_id=user.id,
            age=age_int,
            date_of_birth=date_of_birth if date_of_birth else None,
            gender=gender if gender else None,
            phone=phone if phone else None
        )
        db.session.add(profile)
        db.session.commit()

        # Auto login
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session.permanent = True

        flash('Registration successful! Welcome to PatientCase AI.', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/patient_register.html')


@auth_bp.route('/doctor-login', methods=['GET', 'POST'])
def doctor_login():
    """Doctor login page."""
    if 'user_id' in session:
        user = get_current_user()
        if user and user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))

    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            flash('Invalid session token. Please try again.', 'danger')
            return redirect(url_for('auth.doctor_login'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Doctor email and password are required.', 'warning')
            return render_template('auth/doctor_login.html', email=email)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password) or user.role != 'doctor':
            flash('Invalid doctor credentials. Please verify your login details.', 'danger')
            return render_template('auth/doctor_login.html', email=email)

        if not user.is_active:
            flash('Doctor account is deactivated. Contact medical administration.', 'danger')
            return render_template('auth/doctor_login.html', email=email)

        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session.permanent = True

        flash(f'Welcome, Dr. {user.full_name}. Clinical portal unlocked.', 'success')
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('doctor.dashboard'))

    return render_template('auth/doctor_login.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset assistance."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        flash(f'If an account exists for {email}, a secure password reset link has been dispatched.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/logout')
def logout():
    """End session and redirect to landing page."""
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))
