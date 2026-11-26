import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from database.database import db
from database.models import (
    PatientCase,
    FollowUpResponse,
    DoctorNote,
    CaseAuditEvent,
    User,
    utc_now
)
from utils.helpers import generate_public_case_id
from services.ai_service import ai_service
from services.qr_service import create_case_access_token

def create_patient_case(
    patient_id: int,
    intake_data: Dict[str, Any],
    followup_answers: Optional[List[Dict[str, str]]] = None,
    is_draft: bool = False
) -> PatientCase:
    """
    Create a new patient case record with AI-assisted structured summary and QR access token.
    """
    public_id = generate_public_case_id()
    status = 'draft' if is_draft else 'submitted'

    # Generate structured summary
    structured_summary = ai_service.generate_structured_summary({
        'chief_complaint': intake_data.get('chief_complaint', ''),
        'symptoms': intake_data.get('symptoms', ''),
        'duration': intake_data.get('duration', ''),
        'severity': intake_data.get('severity', ''),
        'pattern': intake_data.get('pattern', ''),
        'medical_history': intake_data.get('medical_history', ''),
        'allergies': intake_data.get('allergies', ''),
        'medications': intake_data.get('medications', ''),
        'family_history': intake_data.get('family_history', ''),
        'additional_information': intake_data.get('additional_information', ''),
        'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    })

    case = PatientCase(
        public_case_id=public_id,
        patient_id=patient_id,
        chief_complaint=intake_data.get('chief_complaint', '').strip(),
        symptoms=intake_data.get('symptoms', '').strip(),
        duration=intake_data.get('duration', '').strip(),
        severity=intake_data.get('severity', '').strip(),
        pattern=intake_data.get('pattern', '').strip(),
        medical_history=intake_data.get('medical_history', '').strip(),
        allergies=intake_data.get('allergies', '').strip(),
        medications=intake_data.get('medications', '').strip(),
        family_history=intake_data.get('family_history', '').strip(),
        additional_information=intake_data.get('additional_information', '').strip(),
        structured_summary=json.dumps(structured_summary),
        status=status
    )
    db.session.add(case)
    db.session.flush()

    # Save follow-up responses if provided
    if followup_answers:
        for item in followup_answers:
            q_text = item.get('question', '').strip()
            a_text = item.get('answer', '').strip()
            if q_text and a_text:
                resp = FollowUpResponse(
                    case_id=case.id,
                    question=q_text,
                    answer=a_text
                )
                db.session.add(resp)

    # Generate QR access token
    create_case_access_token(case.id, expiry_days=7)

    # Audit log
    audit = CaseAuditEvent(
        case_id=case.id,
        actor_id=patient_id,
        action="case_created" if not is_draft else "draft_saved",
        ip_address="127.0.0.1"
    )
    db.session.add(audit)
    db.session.commit()

    return case

def add_doctor_review(
    case: PatientCase,
    doctor_id: int,
    note: str,
    diagnosis_impression: str = None,
    clinical_recommendation: str = None,
    new_status: str = 'reviewed'
) -> DoctorNote:
    """Record a clinical doctor note and advance the case workflow status."""
    doctor_note = DoctorNote(
        case_id=case.id,
        doctor_id=doctor_id,
        note=note.strip(),
        diagnosis_impression=diagnosis_impression.strip() if diagnosis_impression else None,
        clinical_recommendation=clinical_recommendation.strip() if clinical_recommendation else None
    )
    db.session.add(doctor_note)

    case.status = new_status
    case.assigned_doctor_id = doctor_id
    case.updated_at = utc_now()

    audit = CaseAuditEvent(
        case_id=case.id,
        actor_id=doctor_id,
        action=f"doctor_reviewed_status_{new_status}",
        ip_address="127.0.0.1"
    )
    db.session.add(audit)
    db.session.commit()
    return doctor_note

def get_patient_stats(patient_id: int) -> Dict[str, int]:
    """Calculate dashboard statistics for patient."""
    total = PatientCase.query.filter_by(patient_id=patient_id).count()
    completed = PatientCase.query.filter_by(patient_id=patient_id, status='completed').count()
    in_progress = PatientCase.query.filter(
        PatientCase.patient_id == patient_id,
        PatientCase.status.in_(['in_review', 'reviewed'])
    ).count()
    pending = PatientCase.query.filter_by(patient_id=patient_id, status='submitted').count()

    return {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'pending_review': pending
    }

def get_doctor_stats() -> Dict[str, Any]:
    """Calculate dashboard statistics and status distribution for doctor."""
    total = PatientCase.query.count()
    
    # Cases created in the last 24 hours
    since_yesterday = utc_now() - timedelta(days=1)
    today_cases = PatientCase.query.filter(PatientCase.created_at >= since_yesterday).count()

    reviewed = PatientCase.query.filter(
        PatientCase.status.in_(['reviewed', 'completed'])
    ).count()
    
    pending = PatientCase.query.filter(
        PatientCase.status.in_(['submitted', 'in_review'])
    ).count()

    # Status distribution for charts
    status_counts = {
        'Submitted': PatientCase.query.filter_by(status='submitted').count(),
        'In Review': PatientCase.query.filter_by(status='in_review').count(),
        'Reviewed': PatientCase.query.filter_by(status='reviewed').count(),
        'Completed': PatientCase.query.filter_by(status='completed').count()
    }

    return {
        'total': total,
        'today': today_cases,
        'reviewed': reviewed,
        'pending_review': pending,
        'status_distribution': status_counts
    }
