from typing import Tuple, Optional
from database.database import db
from database.models import CaseAccessToken, PatientCase, CaseAuditEvent, User, utc_now
from services.barcode_service import format_display_case_id

def log_audit_event(case_id: int, actor_id: Optional[int], action: str, ip_address: Optional[str] = None):
    """Record an audit trail event for case security tracking."""
    event = CaseAuditEvent(
        case_id=case_id,
        actor_id=actor_id,
        action=action,
        ip_address=ip_address or '127.0.0.1'
    )
    db.session.add(event)
    db.session.commit()
    return event

def verify_token_and_grant_access(token_string: str, doctor: User, ip_address: str = None) -> Tuple[bool, Optional[PatientCase], str]:
    """
    Validate a QR code access token and verify doctor authorization.
    Logs audit event upon access.
    """
    if not doctor or doctor.role != 'doctor':
        return False, None, "Unauthorized: Access requires doctor authentication."

    if not token_string:
        return False, None, "Invalid request: Missing access token."

    token_obj = CaseAccessToken.query.filter_by(token_value=token_string).first()
    if not token_obj:
        return False, None, "Invalid or unrecognized access token."

    if not token_obj.is_valid():
        return False, None, "Access token has expired or has been revoked."

    case = token_obj.case
    if not case:
        return False, None, "Associated medical case could not be located."

    # Audit log access
    log_audit_event(
        case_id=case.id,
        actor_id=doctor.id,
        action="qr_token_verified_and_accessed",
        ip_address=ip_address
    )

    return True, case, "Case access authorized."

def access_case_by_identifier(case_identifier: str, doctor: User, ip_address: str = None) -> Tuple[bool, Optional[PatientCase], str]:
    """
    Access a case using its public case ID or barcode representation.
    """
    if not doctor or doctor.role != 'doctor':
        return False, None, "Unauthorized: Doctor credentials required."

    if not case_identifier:
        return False, None, "Case ID is required."

    # Normalize if entered as barcode (e.g. PC2026A8F4K2 -> PC-2026-A8F4K2)
    normalized_id = format_display_case_id(case_identifier)

    case = PatientCase.query.filter_by(public_case_id=normalized_id).first()
    if not case:
        # Also try searching raw
        case = PatientCase.query.filter_by(public_case_id=case_identifier.strip().upper()).first()

    if not case:
        return False, None, f"No medical record found matching Case ID '{case_identifier}'."

    # Audit log
    log_audit_event(
        case_id=case.id,
        actor_id=doctor.id,
        action="doctor_manual_lookup_accessed",
        ip_address=ip_address
    )

    return True, case, "Case record accessed."
