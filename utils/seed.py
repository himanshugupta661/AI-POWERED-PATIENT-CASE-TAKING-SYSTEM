import json
from datetime import datetime, timedelta, timezone
from database.database import db
from database.models import (
    User,
    PatientProfile,
    DoctorProfile,
    PatientCase,
    FollowUpResponse,
    CaseAccessToken,
    DoctorNote,
    CaseAuditEvent,
    utc_now
)
from utils.security import generate_random_token, hash_token

def seed_database():
    """Seed initial development test accounts and realistic sample cases."""
    # Check if data already exists
    if User.query.first():
        print("Database already contains users. Skipping initial seed.")
        return

    print("Seeding database with development accounts and clinical cases...")

    # 1. Create Default Doctor Account
    doctor_user = User(
        full_name="Dr. Sarah Jenkins, MD",
        email="doctor@patientcase.ai",
        role="doctor",
        is_active=True
    )
    doctor_user.set_password("Doctor@123")
    db.session.add(doctor_user)
    db.session.flush()

    doctor_profile = DoctorProfile(
        user_id=doctor_user.id,
        specialization="Internal Medicine & General Practice",
        clinic_name="PatientCase Medical Center",
        license_number="MED-IND-2024-8841",
        qualification="MBBS, MD (General Medicine)",
        phone="+91 98765 43210"
    )
    db.session.add(doctor_profile)

    # 2. Create Default Patient Account
    patient_user = User(
        full_name="Rahul Sharma",
        email="patient@patientcase.ai",
        role="patient",
        is_active=True
    )
    patient_user.set_password("Patient@123")
    db.session.add(patient_user)
    db.session.flush()

    patient_profile = PatientProfile(
        user_id=patient_user.id,
        age=34,
        date_of_birth="1992-05-14",
        gender="Male",
        phone="+91 98111 22334",
        blood_group="B+",
        emergency_contact="Priya Sharma (+91 98111 22335)"
    )
    db.session.add(patient_profile)

    # 3. Create Sample Patient Case 1: Active/Submitted Case
    summary_1 = {
        "chief_complaint": "Persistent dry cough with low-grade fever",
        "extracted_symptoms": ["Dry cough", "Low-grade fever", "Slight fatigue", "Sore throat"],
        "duration": "5 days",
        "severity": "Moderate (5/10)",
        "pattern": "Worse at night and early morning",
        "medical_history": "Mild seasonal allergic rhinitis",
        "allergies": "No known drug allergies",
        "current_medications": "Cetirizine 10mg as needed for allergies",
        "family_history": "Father has hypertension",
        "ai_analysis_type": "Automated preliminary extraction",
        "safety_disclaimer": "This is an AI-assisted intake summary. Not a diagnostic assessment. Must be clinically evaluated by a licensed physician."
    }

    case_1 = PatientCase(
        public_case_id="PC-2026-B7E2X9",
        patient_id=patient_user.id,
        chief_complaint="Persistent dry cough with low-grade fever",
        symptoms="Dry barking cough, scratchy throat, temperature around 99.8 F in evenings, mild body ache.",
        duration="5 days",
        severity="Moderate (5/10)",
        pattern="Coughing attacks worsen when lying down at night",
        medical_history="Seasonal dust allergies",
        allergies="No known drug allergies (NKDA)",
        medications="Cetirizine 10mg PRN",
        family_history="Father: Hypertension; Mother: Healthy",
        additional_information="Has not traveled recently. Non-smoker.",
        structured_summary=json.dumps(summary_1),
        status="submitted",
        created_at=utc_now() - timedelta(hours=3)
    )
    db.session.add(case_1)
    db.session.flush()

    # Add follow-up responses for Case 1
    followups_1 = [
        FollowUpResponse(
            case_id=case_1.id,
            question="Are you experiencing any shortness of breath or chest pain?",
            answer="No shortness of breath or chest pain. Just chest tightness from repeated coughing."
        ),
        FollowUpResponse(
            case_id=case_1.id,
            question="Have you been in close contact with anyone who tested positive for influenza or COVID-19?",
            answer="A coworker had the flu last week."
        )
    ]
    db.session.add_all(followups_1)

    # Access Token for Case 1
    raw_token_1 = "pc_tok_demo_case1_live_access_key"
    access_token_1 = CaseAccessToken(
        case_id=case_1.id,
        token_value=raw_token_1,
        token_hash=hash_token(raw_token_1),
        expires_at=utc_now() + timedelta(days=7)
    )
    db.session.add(access_token_1)

    # Audit log for Case 1
    audit_1 = CaseAuditEvent(
        case_id=case_1.id,
        actor_id=patient_user.id,
        action="case_created",
        ip_address="127.0.0.1"
    )
    db.session.add(audit_1)

    # 4. Create Sample Patient Case 2: Reviewed Case with Doctor Note
    summary_2 = {
        "chief_complaint": "Acute lower back pain after lifting gym weights",
        "extracted_symptoms": ["Lumbar back pain", "Muscle spasm", "Stiffness bending forward"],
        "duration": "2 days",
        "severity": "Severe (7/10)",
        "pattern": "Sharp pain on bending forward or sitting for extended periods",
        "medical_history": "No prior disc issues or spine surgeries",
        "allergies": "No known allergies",
        "current_medications": "Over-the-counter paracetamol 650mg once",
        "family_history": "Non-contributory",
        "ai_analysis_type": "Automated preliminary extraction",
        "safety_disclaimer": "This is an AI-assisted intake summary. Not a diagnostic assessment. Must be clinically evaluated by a licensed physician."
    }

    case_2 = PatientCase(
        public_case_id="PC-2026-F4N8T1",
        patient_id=patient_user.id,
        chief_complaint="Acute lower back pain after lifting gym weights",
        symptoms="Localized lower back pain, tightness across lumbar region, hurts to bend forward or tie shoes.",
        duration="2 days",
        severity="Severe (7/10)",
        pattern="Sharp pain with movement, dull ache when resting with knees elevated",
        medical_history="Healthy, regular gym goer",
        allergies="None reported",
        medications="Paracetamol 650mg PRN",
        family_history="No history of spinal diseases",
        additional_information="No radiating pain down legs, no numbness or tingling.",
        structured_summary=json.dumps(summary_2),
        status="reviewed",
        assigned_doctor_id=doctor_user.id,
        created_at=utc_now() - timedelta(days=2),
        updated_at=utc_now() - timedelta(days=1)
    )
    db.session.add(case_2)
    db.session.flush()

    # Doctor Note for Case 2
    doc_note = DoctorNote(
        case_id=case_2.id,
        doctor_id=doctor_user.id,
        note="Patient examined via clinical review. Symptoms and physical descriptions are consistent with acute lumbar paraspinal muscle strain. No red flag neurological symptoms (no sciatica, bowel/bladder incontinence, or motor weakness).",
        diagnosis_impression="Acute Lumbar Muscle Strain (ICD-10 M54.5)",
        clinical_recommendation="1. Local ice/heat application for 15 mins TID.\n2. Prescribed NSAID + muscle relaxant as clinically indicated.\n3. Avoid heavy lifting and deep flexion for 10-14 days.\n4. Follow-up if pain radiates or persists beyond 2 weeks."
    )
    db.session.add(doc_note)

    raw_token_2 = "pc_tok_demo_case2_doctor_reviewed_key"
    access_token_2 = CaseAccessToken(
        case_id=case_2.id,
        token_value=raw_token_2,
        token_hash=hash_token(raw_token_2),
        expires_at=utc_now() + timedelta(days=7)
    )
    db.session.add(access_token_2)

    audit_2a = CaseAuditEvent(
        case_id=case_2.id,
        actor_id=patient_user.id,
        action="case_created",
        ip_address="127.0.0.1"
    )
    audit_2b = CaseAuditEvent(
        case_id=case_2.id,
        actor_id=doctor_user.id,
        action="doctor_reviewed",
        ip_address="127.0.0.1"
    )
    db.session.add_all([audit_2a, audit_2b])

    db.session.commit()
    print("Database seeding completed successfully!")
