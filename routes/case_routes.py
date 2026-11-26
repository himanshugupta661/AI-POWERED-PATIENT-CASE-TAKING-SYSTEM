import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database.database import db
from database.models import PatientCase
from utils.security import patient_required, get_current_user, validate_csrf
from utils.validators import sanitize_text, validate_patient_intake
from utils.helpers import get_status_info, to_barcode_id
from services.ai_service import ai_service
from services.case_service import create_patient_case
from services.qr_service import get_or_create_case_token, generate_qr_base64

case_bp = Blueprint('case', __name__, url_prefix='/patient/case-taking')

@case_bp.route('/new', methods=['GET', 'POST'])
def new_case():
    """Multi-step intake workflow - Step 1, 2, 3."""
    # Ensure patient is authenticated
    if 'user_id' not in session:
        flash('Please log in to start a new patient case.', 'warning')
        return redirect(url_for('auth.login', next=request.path))

    user = get_current_user()
    if not user or user.role != 'patient':
        flash('Only registered patients can file a new case.', 'danger')
        return redirect(url_for('index'))

    profile = user.patient_profile

    if request.method == 'POST':
        # Retrieve submitted intake data
        intake_data = {
            'chief_complaint': sanitize_text(request.form.get('chief_complaint', ''), 255),
            'symptoms': sanitize_text(request.form.get('symptoms', ''), 3000),
            'duration': sanitize_text(request.form.get('duration', ''), 100),
            'severity': sanitize_text(request.form.get('severity', ''), 50),
            'pattern': sanitize_text(request.form.get('pattern', ''), 150),
            'medical_history': sanitize_text(request.form.get('medical_history', ''), 2000),
            'allergies': sanitize_text(request.form.get('allergies', ''), 1000),
            'medications': sanitize_text(request.form.get('medications', ''), 1000),
            'family_history': sanitize_text(request.form.get('family_history', ''), 1000),
            'additional_information': sanitize_text(request.form.get('additional_information', ''), 2000)
        }

        # Check options for allergies/meds/history
        history_status = request.form.get('history_status')
        if history_status == 'none':
            intake_data['medical_history'] = 'No known significant medical history'
        elif history_status == 'not_sure':
            intake_data['medical_history'] = 'Not sure / Prefer not to specify'

        allergies_status = request.form.get('allergies_status')
        if allergies_status == 'none':
            intake_data['allergies'] = 'No known drug or food allergies (NKDA)'
        elif allergies_status == 'not_sure':
            intake_data['allergies'] = 'Not sure / Prefer not to specify'

        meds_status = request.form.get('meds_status')
        if meds_status == 'none':
            intake_data['medications'] = 'No current regular medications'
        elif meds_status == 'not_sure':
            intake_data['medications'] = 'Not sure / Prefer not to specify'

        # Validate
        valid, errors = validate_patient_intake(intake_data)
        if not valid:
            for err in errors:
                flash(err, 'danger')
            return render_template('patient/new_case.html', user=user, profile=profile, form_data=intake_data)

        # Store in session for follow-up and review steps
        session['case_intake_data'] = intake_data

        # Check if user requested 'Save Draft' directly
        action = request.form.get('action')
        if action == 'save_draft':
            case = create_patient_case(user.id, intake_data, followup_answers=[], is_draft=True)
            session.pop('case_intake_data', None)
            flash('Your case draft has been saved successfully.', 'info')
            return redirect(url_for('patient.my_cases'))

        # Move to Follow-up questions step
        return redirect(url_for('case.follow_up'))

    # GET request
    existing_data = session.get('case_intake_data', {})
    return render_template('patient/new_case.html', user=user, profile=profile, form_data=existing_data)


@case_bp.route('/follow-up', methods=['GET', 'POST'])
def follow_up():
    """Step 4: Dynamic AI-Assisted Follow-Up Questions."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = get_current_user()
    intake_data = session.get('case_intake_data')
    if not intake_data:
        flash('Please fill in your primary symptoms first.', 'warning')
        return redirect(url_for('case.new_case'))

    # Generate follow-up questions using rule-based AI engine
    questions = ai_service.generate_followup_questions(intake_data)

    if request.method == 'POST':
        # Collect answers
        followup_answers = []
        for i, q in enumerate(questions):
            ans_text = sanitize_text(request.form.get(f'answer_{i}', ''), 1000)
            if ans_text:
                followup_answers.append({
                    'question': q['question'],
                    'answer': ans_text
                })

        session['case_followup_answers'] = followup_answers
        return redirect(url_for('case.summary'))

    existing_answers = session.get('case_followup_answers', [])
    answer_map = {item['question']: item['answer'] for item in existing_answers}

    return render_template(
        'patient/follow_up.html',
        user=user,
        intake_data=intake_data,
        questions=questions,
        answer_map=answer_map
    )


@case_bp.route('/summary', methods=['GET'])
def summary():
    """Step 5: Review & Structured Summary Preview before submission."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = get_current_user()
    intake_data = session.get('case_intake_data')
    if not intake_data:
        flash('Please initiate your case first.', 'warning')
        return redirect(url_for('case.new_case'))

    followup_answers = session.get('case_followup_answers', [])
    structured_summary = ai_service.generate_structured_summary(intake_data)

    return render_template(
        'patient/case_summary.html',
        user=user,
        intake_data=intake_data,
        followup_answers=followup_answers,
        summary=structured_summary
    )


@case_bp.route('/submit', methods=['POST'])
def submit():
    """Final submission saving case to database."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if not validate_csrf(request.form.get('csrf_token')):
        flash('Invalid session token. Please try again.', 'danger')
        return redirect(url_for('case.summary'))

    user = get_current_user()
    intake_data = session.get('case_intake_data')
    if not intake_data:
        flash('Session expired. Please fill in your symptoms again.', 'warning')
        return redirect(url_for('case.new_case'))

    followup_answers = session.get('case_followup_answers', [])

    # Prevent duplicate submission: create the case
    case = create_patient_case(
        patient_id=user.id,
        intake_data=intake_data,
        followup_answers=followup_answers,
        is_draft=False
    )

    # Clear intake session
    session.pop('case_intake_data', None)
    session.pop('case_followup_answers', None)

    flash('Your medical case intake has been securely registered and organized!', 'success')
    return redirect(url_for('case.case_submitted', public_case_id=case.public_case_id))


@case_bp.route('/submitted/<public_case_id>')
def case_submitted(public_case_id):
    """Case submission confirmation page featuring QR code and Barcode."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = get_current_user()
    case = PatientCase.query.filter_by(public_case_id=public_case_id, patient_id=user.id).first()
    if not case:
        flash('Case not found.', 'danger')
        return redirect(url_for('patient.dashboard'))

    token = get_or_create_case_token(case)
    access_url = request.url_root.rstrip('/') + url_for('doctor.access_case', token=token)
    barcode_id = to_barcode_id(case.public_case_id)
    qr_data_url = generate_qr_base64(access_url)

    return render_template(
        'patient/case_submitted.html',
        user=user,
        case=case,
        token=token,
        access_url=access_url,
        barcode_id=barcode_id,
        qr_data_url=qr_data_url,
        get_status_info=get_status_info
    )
