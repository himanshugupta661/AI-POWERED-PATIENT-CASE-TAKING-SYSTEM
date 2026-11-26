from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from database.database import db
from database.models import PatientCase, DoctorNote, User, PatientProfile, DoctorProfile
from utils.security import doctor_required, get_current_user, validate_csrf
from utils.validators import sanitize_text, validate_case_id
from utils.helpers import get_status_info, to_barcode_id
from services.case_service import get_doctor_stats, add_doctor_review
from services.access_service import verify_token_and_grant_access, access_case_by_identifier, log_audit_event
from services.qr_service import get_or_create_case_token, generate_qr_base64

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/dashboard')
@doctor_required
def dashboard():
    """Doctor clinical dashboard with analytics, KPIs, and recent intake records."""
    doctor = get_current_user()
    stats = get_doctor_stats()

    # Get recent cases
    recent_cases = PatientCase.query.order_by(PatientCase.created_at.desc()).limit(8).all()
    
    # Get recent reviewed cases
    my_reviews = DoctorNote.query.filter_by(doctor_id=doctor.id)\
        .order_by(DoctorNote.created_at.desc()).limit(5).all()

    return render_template(
        'doctor/dashboard.html',
        doctor=doctor,
        stats=stats,
        recent_cases=recent_cases,
        my_reviews=my_reviews,
        get_status_info=get_status_info
    )

@doctor_bp.route('/scan-case')
@doctor_required
def scan_case():
    """QR code & Barcode scanner interface with camera and manual fallback."""
    doctor = get_current_user()
    return render_template('doctor/scan_case.html', doctor=doctor)

@doctor_bp.route('/access-case', methods=['GET', 'POST'])
@doctor_required
def access_case():
    """
    Controlled gateway to open a patient case via QR token or manual Case ID.
    Enforces authorization check and audit logging.
    """
    doctor = get_current_user()
    ip_addr = request.remote_addr or '127.0.0.1'

    # 1. Access via QR token in URL query parameter (?token=...)
    token = request.args.get('token')
    if token:
        success, case, msg = verify_token_and_grant_access(token, doctor, ip_addr)
        if success and case:
            flash(f"Authorized access to case {case.public_case_id} verified.", "success")
            return redirect(url_for('doctor.patient_case', public_case_id=case.public_case_id))
        else:
            flash(f"Access Denied: {msg}", "danger")
            return redirect(url_for('doctor.scan_case'))

    # 2. Access via POST form (manual input or scanner submission)
    if request.method == 'POST':
        case_input = request.form.get('case_id', '').strip()
        token_input = request.form.get('token', '').strip()

        if token_input:
            success, case, msg = verify_token_and_grant_access(token_input, doctor, ip_addr)
            if success and case:
                return redirect(url_for('doctor.patient_case', public_case_id=case.public_case_id))
            flash(f"Token error: {msg}", "danger")
            return redirect(url_for('doctor.scan_case'))

        if case_input:
            success, case, msg = access_case_by_identifier(case_input, doctor, ip_addr)
            if success and case:
                flash(f"Patient case {case.public_case_id} retrieved successfully.", "success")
                return redirect(url_for('doctor.patient_case', public_case_id=case.public_case_id))
            flash(msg, "danger")
            return redirect(url_for('doctor.scan_case'))

        flash("Please enter a valid Case ID or scan a QR code.", "warning")
        return redirect(url_for('doctor.scan_case'))

    return render_template('doctor/access_case.html', doctor=doctor)

@doctor_bp.route('/case/<public_case_id>', methods=['GET', 'POST'])
@doctor_required
def patient_case(public_case_id):
    """
    Doctor review interface for an individual patient case.
    Shows demographics, AI-assisted structured intake, follow-up Q&A, and notes form.
    """
    doctor = get_current_user()
    case = PatientCase.query.filter_by(public_case_id=public_case_id).first()
    if not case:
        flash(f"Case '{public_case_id}' was not found.", "danger")
        return redirect(url_for('doctor.dashboard'))

    # Handle Doctor Clinical Review Submission
    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            flash("Invalid session token.", "danger")
            return redirect(url_for('doctor.patient_case', public_case_id=public_case_id))

        note_text = sanitize_text(request.form.get('note', ''), 4000)
        diagnosis = sanitize_text(request.form.get('diagnosis_impression', ''), 1000)
        recommendation = sanitize_text(request.form.get('clinical_recommendation', ''), 2000)
        new_status = request.form.get('status', 'reviewed')

        if not note_text and not diagnosis and not recommendation:
            flash("Please provide clinical observations or notes before submitting.", "warning")
        else:
            add_doctor_review(
                case=case,
                doctor_id=doctor.id,
                note=note_text or "Clinical intake reviewed.",
                diagnosis_impression=diagnosis,
                clinical_recommendation=recommendation,
                new_status=new_status
            )
            flash("Doctor notes saved and case status updated successfully!", "success")
            return redirect(url_for('doctor.patient_case', public_case_id=public_case_id))

    # Log viewing audit event
    log_audit_event(case.id, doctor.id, "doctor_viewed_case", request.remote_addr)

    token = get_or_create_case_token(case)
    barcode_id = to_barcode_id(case.public_case_id)
    qr_data_url = generate_qr_base64(request.url_root.rstrip('/') + url_for('doctor.access_case', token=token))

    return render_template(
        'doctor/patient_case.html',
        doctor=doctor,
        case=case,
        patient=case.patient,
        patient_profile=case.patient.patient_profile if case.patient else None,
        summary=case.get_summary_dict(),
        token=token,
        barcode_id=barcode_id,
        qr_data_url=qr_data_url,
        audit_events=case.audit_events.order_by(db.desc('created_at')).limit(10).all(),
        get_status_info=get_status_info
    )

@doctor_bp.route('/patients')
@doctor_required
def patients():
    """List of all registered patients with case counts and contact info."""
    doctor = get_current_user()
    patient_users = User.query.filter_by(role='patient').order_by(User.full_name).all()
    return render_template('doctor/patients.html', doctor=doctor, patients=patient_users)

@doctor_bp.route('/case-history')
@doctor_required
def case_history():
    """Comprehensive archive of all patient cases with filter and search."""
    doctor = get_current_user()
    status_filter = request.args.get('status')
    search_q = request.args.get('q', '').strip()

    query = PatientCase.query
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search_q:
        query = query.filter(
            (PatientCase.public_case_id.ilike(f'%{search_q}%')) |
            (PatientCase.chief_complaint.ilike(f'%{search_q}%'))
        )

    cases = query.order_by(PatientCase.created_at.desc()).all()

    return render_template(
        'doctor/case_history.html',
        doctor=doctor,
        cases=cases,
        current_status=status_filter or 'all',
        search_query=search_q,
        get_status_info=get_status_info
    )

@doctor_bp.route('/doctor-notes')
def doctor_notes():
    """History of all clinical notes authored by doctor."""
    if 'user_id' not in session:
        return redirect(url_for('auth.doctor_login'))
    doctor = get_current_user()
    notes = DoctorNote.query.filter_by(doctor_id=doctor.id).order_by(DoctorNote.created_at.desc()).all()
    return render_template('doctor/doctor_notes.html', doctor=doctor, notes=notes, get_status_info=get_status_info)

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@doctor_required
def profile():
    """Doctor professional profile settings."""
    doctor = get_current_user()
    profile = doctor.doctor_profile

    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            flash('Invalid session token.', 'danger')
            return redirect(url_for('doctor.profile'))

        doctor.full_name = sanitize_text(request.form.get('full_name', ''), 120)
        
        if not profile:
            profile = DoctorProfile(user_id=doctor.id)
            db.session.add(profile)

        profile.specialization = sanitize_text(request.form.get('specialization', ''), 120)
        profile.clinic_name = sanitize_text(request.form.get('clinic_name', ''), 150)
        profile.license_number = sanitize_text(request.form.get('license_number', ''), 60)
        profile.qualification = sanitize_text(request.form.get('qualification', ''), 120)
        profile.phone = sanitize_text(request.form.get('phone', ''), 30)

        db.session.commit()
        flash('Doctor profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))

    return render_template('doctor/profile.html', doctor=doctor, profile=profile)
