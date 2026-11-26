from datetime import datetime, timezone
import json
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    """User account model for patients and doctors."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # 'patient' or 'doctor'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    patient_profile = db.relationship('PatientProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    cases = db.relationship('PatientCase', foreign_keys='PatientCase.patient_id', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    doctor_notes = db.relationship('DoctorNote', backref='doctor', lazy='dynamic')
    audit_events = db.relationship('CaseAuditEvent', backref='actor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_doctor(self):
        return self.role == 'doctor'

    def is_patient(self):
        return self.role == 'patient'

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class PatientProfile(db.Model):
    """Extended profile information for patients."""
    __tablename__ = 'patient_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=True)
    date_of_birth = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'age': self.age,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'phone': self.phone,
            'blood_group': self.blood_group,
            'emergency_contact': self.emergency_contact
        }


class DoctorProfile(db.Model):
    """Extended profile information for doctors."""
    __tablename__ = 'doctor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    specialization = db.Column(db.String(120), default='General Medicine')
    clinic_name = db.Column(db.String(150), default='PatientCase Medical Center')
    license_number = db.Column(db.String(60), nullable=True)
    qualification = db.Column(db.String(120), default='MBBS, MD')
    phone = db.Column(db.String(30), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'specialization': self.specialization,
            'clinic_name': self.clinic_name,
            'license_number': self.license_number,
            'qualification': self.qualification,
            'phone': self.phone
        }


class PatientCase(db.Model):
    """Medical case record captured from patient interaction."""
    __tablename__ = 'patient_cases'

    id = db.Column(db.Integer, primary_key=True)
    public_case_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Core Clinical Intake Fields
    chief_complaint = db.Column(db.String(255), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(100), nullable=True)
    severity = db.Column(db.String(50), nullable=True)  # Mild, Moderate, Severe, 1-10
    pattern = db.Column(db.String(150), nullable=True)   # Constant, Intermittent, Worse at night, etc.

    # Medical Background
    medical_history = db.Column(db.Text, nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    medications = db.Column(db.Text, nullable=True)
    family_history = db.Column(db.Text, nullable=True)
    additional_information = db.Column(db.Text, nullable=True)

    # Structured AI Summary JSON
    structured_summary = db.Column(db.Text, nullable=True)

    # Workflow Status: 'draft', 'submitted', 'in_review', 'reviewed', 'completed'
    status = db.Column(db.String(30), default='submitted', nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Assigned or reviewing doctor
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    follow_up_responses = db.relationship('FollowUpResponse', backref='case', cascade='all, delete-orphan', lazy='joined')
    access_tokens = db.relationship('CaseAccessToken', backref='case', cascade='all, delete-orphan', lazy='dynamic')
    notes = db.relationship('DoctorNote', backref='case', cascade='all, delete-orphan', lazy='joined', order_by='DoctorNote.created_at.desc()')
    audit_events = db.relationship('CaseAuditEvent', backref='case', cascade='all, delete-orphan', lazy='dynamic')
    assigned_doctor = db.relationship('User', foreign_keys=[assigned_doctor_id], backref='assigned_cases')

    def get_summary_dict(self):
        """Parse structured summary JSON into a dict."""
        if not self.structured_summary:
            return {}
        try:
            return json.loads(self.structured_summary)
        except Exception:
            return {'raw': self.structured_summary}

    def to_dict(self):
        return {
            'id': self.id,
            'public_case_id': self.public_case_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.full_name if self.patient else 'Unknown',
            'chief_complaint': self.chief_complaint,
            'symptoms': self.symptoms,
            'duration': self.duration,
            'severity': self.severity,
            'pattern': self.pattern,
            'medical_history': self.medical_history,
            'allergies': self.allergies,
            'medications': self.medications,
            'family_history': self.family_history,
            'additional_information': self.additional_information,
            'structured_summary': self.get_summary_dict(),
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }


class FollowUpResponse(db.Model):
    """Dynamic follow-up questions and patient answers."""
    __tablename__ = 'follow_up_responses'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('patient_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CaseAccessToken(db.Model):
    """Secure access tokens generated for QR codes and controlled case sharing."""
    __tablename__ = 'case_access_tokens'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('patient_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    token_value = db.Column(db.String(64), nullable=False, unique=True, index=True)
    token_hash = db.Column(db.String(128), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def is_valid(self):
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None:
            # Handle tz-aware or tz-naive
            now = utc_now()
            if self.expires_at.tzinfo is None:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
            if now > self.expires_at:
                return False
        return True


class DoctorNote(db.Model):
    """Doctor clinical observations, diagnosis impressions, and instructions."""
    __tablename__ = 'doctor_notes'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('patient_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    diagnosis_impression = db.Column(db.Text, nullable=True)
    clinical_recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.full_name if self.doctor else 'Doctor',
            'note': self.note,
            'diagnosis_impression': self.diagnosis_impression,
            'clinical_recommendation': self.clinical_recommendation,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class CaseAuditEvent(db.Model):
    """Audit log tracking access and updates to patient medical cases."""
    __tablename__ = 'case_audit_events'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('patient_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # 'created', 'qr_accessed', 'doctor_viewed', 'status_updated', 'note_added'
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'actor_id': self.actor_id,
            'actor_name': self.actor.full_name if self.actor else 'System/Anonymous',
            'action': self.action,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
