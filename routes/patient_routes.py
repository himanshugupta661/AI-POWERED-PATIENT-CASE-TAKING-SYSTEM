from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from database.database import db
from database.models import PatientCase, PatientProfile
from utils.security import patient_required, get_current_user, validate_csrf
from utils.validators import sanitize_text
from utils.helpers import get_status_info, to_barcode_id
from services.case_service import get_patient_stats
from services.qr_service import get_or_create_case_token, generate_qr_base64

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
@patient_required
def dashboard():
    """Patient dashboard showing statistics, quick actions, and recent cases."""
    user = get_current_user()
    stats = get_patient_stats(user.id)
    recent_cases = PatientCase.query.filter_by(patient_id=user.id)\
        .order_by(PatientCase.created_at.desc())\
        .limit(5)\
        .all()

    return render_template(
        'patient/dashboard.html',
        user=user,
        stats=stats,
        recent_cases=recent_cases,
        get_status_info=get_status_info
    )

@patient_bp.route('/my-cases')
@patient_required
def my_cases():
    """List all cases filed by the patient with filtering."""
    user = get_current_user()
    status_filter = request.args.get('status')
    
    query = PatientCase.query.filter_by(patient_id=user.id)
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)

    cases = query.order_by(PatientCase.created_at.desc()).all()
    stats = get_patient_stats(user.id)

    return render_template(
        'patient/my_cases.html',
        user=user,
        cases=cases,
        stats=stats,
        current_filter=status_filter or 'all',
        get_status_info=get_status_info
    )

@patient_bp.route('/case/<public_case_id>')
@patient_required
def case_details(public_case_id):
    """View full details of an individual case owned by the patient."""
    user = get_current_user()
    case = PatientCase.query.filter_by(public_case_id=public_case_id, patient_id=user.id).first()
    if not case:
        flash("Medical case not found or access unauthorized.", "danger")
        return redirect(url_for('patient.my_cases'))

    token = get_or_create_case_token(case)
    barcode_id = to_barcode_id(case.public_case_id)
    qr_data_url = generate_qr_base64(request.url_root.rstrip('/') + url_for('doctor.access_case', token=token))

    return render_template(
        'patient/case_details.html',
        user=user,
        case=case,
        token=token,
        barcode_id=barcode_id,
        qr_data_url=qr_data_url,
        summary=case.get_summary_dict(),
        get_status_info=get_status_info
    )

@patient_bp.route('/case/<public_case_id>/qr-barcode')
@patient_required
def qr_barcode(public_case_id):
    """Display dedicated QR and Barcode pass for check-in and doctor scanning."""
    user = get_current_user()
    case = PatientCase.query.filter_by(public_case_id=public_case_id, patient_id=user.id).first()
    if not case:
        flash("Case not found.", "danger")
        return redirect(url_for('patient.my_cases'))

    token = get_or_create_case_token(case)
    access_url = request.url_root.rstrip('/') + url_for('doctor.access_case', token=token)
    barcode_id = to_barcode_id(case.public_case_id)
    qr_data_url = generate_qr_base64(access_url)

    return render_template(
        'patient/qr_barcode.html',
        user=user,
        case=case,
        token=token,
        access_url=access_url,
        barcode_id=barcode_id,
        qr_data_url=qr_data_url,
        get_status_info=get_status_info
    )

@patient_bp.route('/profile', methods=['GET', 'POST'])
@patient_required
def profile():
    """View and update patient profile demographics."""
    user = get_current_user()
    profile = user.patient_profile

    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            flash('Invalid session token.', 'danger')
            return redirect(url_for('patient.profile'))

        user.full_name = sanitize_text(request.form.get('full_name', ''), 120)
        
        if not profile:
            profile = PatientProfile(user_id=user.id)
            db.session.add(profile)

        age_val = request.form.get('age', '').strip()
        if age_val:
            try:
                profile.age = int(age_val)
            except ValueError:
                pass
        
        profile.phone = sanitize_text(request.form.get('phone', ''), 30)
        profile.gender = sanitize_text(request.form.get('gender', ''), 30)
        profile.date_of_birth = sanitize_text(request.form.get('date_of_birth', ''), 20)
        profile.blood_group = sanitize_text(request.form.get('blood_group', ''), 10)
        profile.emergency_contact = sanitize_text(request.form.get('emergency_contact', ''), 100)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))

    return render_template('patient/profile.html', user=user, profile=profile)
