from flask import Blueprint, request, jsonify, session
from services.ai_service import ai_service
from services.case_service import get_doctor_stats
from services.access_service import verify_token_and_grant_access, access_case_by_identifier
from database.models import User, PatientCase

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/extract-symptoms', methods=['POST'])
def extract_symptoms():
    """Real-time AI/NLP extraction endpoint for voice transcripts or typed narrative."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()

    if not text:
        return jsonify({
            'success': False,
            'error': 'Text input is required for extraction.'
        }), 400

    extracted = ai_service.extract_case_information(text)
    return jsonify({
        'success': True,
        'data': extracted
    })

@api_bp.route('/generate-followup', methods=['POST'])
def generate_followup():
    """Dynamic follow-up questions generator endpoint."""
    data = request.get_json(silent=True) or {}
    questions = ai_service.generate_followup_questions(data)
    return jsonify({
        'success': True,
        'questions': questions
    })

@api_bp.route('/doctor/stats', methods=['GET'])
def doctor_stats():
    """Stats endpoint for Chart.js dashboard charts."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = get_doctor_stats()
    return jsonify({
        'success': True,
        'stats': stats
    })

@api_bp.route('/verify-scanner-code', methods=['POST'])
def verify_scanner_code():
    """
    Endpoint called by html5-qrcode scanner when a QR code or barcode is detected.
    Resolves URLs, tokens, or Case IDs into the destination doctor review page.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Doctor login required'}), 401

    from database.database import db
    doctor = db.session.get(User, session['user_id'])
    if not doctor or doctor.role != 'doctor':
        return jsonify({'success': False, 'error': 'Only doctors can access patient cases'}), 403

    data = request.get_json(silent=True) or {}
    raw_code = data.get('code', '').strip()

    if not raw_code:
        return jsonify({'success': False, 'error': 'No barcode or QR data provided'}), 400

    # If full URL scanned (e.g. https://domain.com/doctor/access-case?token=xyz)
    token = None
    if 'token=' in raw_code:
        import urllib.parse
        parsed = urllib.parse.urlparse(raw_code)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get('token', [None])[0]
    elif raw_code.startswith('pc_tok_'):
        token = raw_code

    if token:
        success, case, msg = verify_token_and_grant_access(token, doctor, request.remote_addr)
        if success and case:
            return jsonify({
                'success': True,
                'redirect_url': f'/doctor/case/{case.public_case_id}',
                'case_id': case.public_case_id
            })
        return jsonify({'success': False, 'error': msg}), 400

    # Otherwise assume raw Case ID or Barcode value
    success, case, msg = access_case_by_identifier(raw_code, doctor, request.remote_addr)
    if success and case:
        return jsonify({
            'success': True,
            'redirect_url': f'/doctor/case/{case.public_case_id}',
            'case_id': case.public_case_id
        })

    return jsonify({'success': False, 'error': msg or 'Could not resolve scanned code.'}), 404
