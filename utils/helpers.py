import secrets
from datetime import datetime, timezone
from database.models import PatientCase

SAFE_CHARACTERS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def generate_public_case_id(year=None):
    """
    Generate an unguessable, human-readable public case ID.
    Format: PC-YYYY-XXXXXX (e.g., PC-2026-A8F4K2)
    Checks for database collisions with retry.
    """
    if year is None:
        year = datetime.now(timezone.utc).year
        
    for _ in range(10):
        # Generate 6 cryptographically random characters
        random_suffix = ''.join(secrets.choice(SAFE_CHARACTERS) for _ in range(6))
        candidate_id = f"PC-{year}-{random_suffix}"
        
        # Check collision in database
        exists = PatientCase.query.filter_by(public_case_id=candidate_id).first()
        if not exists:
            return candidate_id
            
    # Fallback with timestamp suffix in the rare event of 10 collisions
    ms_suffix = f"{int(datetime.now().timestamp() * 1000) % 1000000:06d}"
    return f"PC-{year}-{ms_suffix}"

def to_barcode_id(public_case_id):
    """Convert PC-2026-A8F4K2 to PC2026A8F4K2 for Code 128 barcode."""
    if not public_case_id:
        return ""
    return public_case_id.replace('-', '').upper()

def get_status_info(status):
    """Return display label and CSS badge class for case status."""
    status_map = {
        'draft': {
            'label': 'Draft',
            'badge_class': 'badge-secondary',
            'icon': 'fa-pen-to-square'
        },
        'submitted': {
            'label': 'Submitted (Pending Review)',
            'badge_class': 'badge-warning',
            'icon': 'fa-clock'
        },
        'in_review': {
            'label': 'In Review',
            'badge_class': 'badge-info',
            'icon': 'fa-stethoscope'
        },
        'reviewed': {
            'label': 'Reviewed',
            'badge_class': 'badge-primary',
            'icon': 'fa-user-doctor'
        },
        'completed': {
            'label': 'Completed',
            'badge_class': 'badge-success',
            'icon': 'fa-circle-check'
        }
    }
    return status_map.get(status, {'label': status.title(), 'badge_class': 'badge-secondary', 'icon': 'fa-circle'})
