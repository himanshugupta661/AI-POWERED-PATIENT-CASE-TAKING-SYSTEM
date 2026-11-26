import io
import base64
from datetime import datetime, timedelta, timezone
from database.database import db
from database.models import CaseAccessToken, PatientCase, utc_now
from utils.security import generate_random_token, hash_token

try:
    import qrcode
    from qrcode.image.svg import SvgPathImage
    HAS_QRCODE_LIB = True
except ImportError:
    HAS_QRCODE_LIB = False

def create_case_access_token(case_id: int, expiry_days: int = 7) -> CaseAccessToken:
    """
    Generate and store a secure opaque access token for a case.
    The QR code will contain this token or its secure access URL.
    """
    raw_token = f"pc_tok_{generate_random_token(24)}"
    token_hash = hash_token(raw_token)
    expires_at = utc_now() + timedelta(days=expiry_days)

    access_token = CaseAccessToken(
        case_id=case_id,
        token_value=raw_token,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.session.add(access_token)
    db.session.commit()
    return access_token

def get_or_create_case_token(case: PatientCase) -> str:
    """Retrieve an active token for the case, or create a new one."""
    active_token = CaseAccessToken.query.filter_by(
        case_id=case.id,
        revoked_at=None
    ).order_by(CaseAccessToken.created_at.desc()).first()

    if active_token and active_token.is_valid():
        return active_token.token_value

    new_token_obj = create_case_access_token(case.id)
    return new_token_obj.token_value

def generate_qr_base64(data_payload: str) -> str:
    """
    Generate a base64 encoded PNG or SVG data URI for server-side QR rendering.
    Safe fallback if client-side JS fails or for PDF/print generation.
    """
    if not HAS_QRCODE_LIB:
        return ""

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(data_payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Server-side QR generation error: {e}")
        return ""
