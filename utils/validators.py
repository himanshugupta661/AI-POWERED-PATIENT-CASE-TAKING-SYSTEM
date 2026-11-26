import re
import html

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
CASE_ID_REGEX = re.compile(r'^PC-\d{4}-[A-Z0-9]{6}$', re.IGNORECASE)

def validate_email(email):
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False, "Email address is required."
    email = email.strip()
    if len(email) > 150:
        return False, "Email address is too long."
    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address."
    return True, email.lower()

def validate_password(password):
    """Validate password rules."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    return True, None

def validate_case_id(case_id):
    """Validate public case ID format (e.g., PC-2026-A8F4K2)."""
    if not case_id or not isinstance(case_id, str):
        return False, "Case ID is required."
    case_id = case_id.strip().upper()
    if not CASE_ID_REGEX.match(case_id):
        # Also allow barcode format without hyphens (e.g. PC2026A8F4K2)
        clean = case_id.replace('-', '')
        if len(clean) == 12 and clean.startswith('PC'):
            formatted = f"{clean[:2]}-{clean[2:6]}-{clean[6:]}"
            return True, formatted
        return False, "Invalid Case ID format. Example: PC-2026-A8F4K2"
    return True, case_id

def sanitize_text(text, max_length=5000):
    """Escape and strip user-submitted free text."""
    if not text:
        return ""
    text = str(text).strip()
    if len(text) > max_length:
        text = text[:max_length]
    # Basic HTML escaping for storage safety
    return html.escape(text)

def validate_patient_intake(data):
    """Validate required intake fields for patient case."""
    errors = []
    
    chief_complaint = (data.get('chief_complaint') or '').strip()
    symptoms = (data.get('symptoms') or '').strip()
    
    if not chief_complaint:
        errors.append("Chief complaint is required.")
    elif len(chief_complaint) < 3:
        errors.append("Chief complaint must be at least 3 characters long.")
        
    if not symptoms:
        errors.append("Symptoms description is required.")
    elif len(symptoms) < 3:
        errors.append("Please provide more details about your symptoms.")
        
    return len(errors) == 0, errors
