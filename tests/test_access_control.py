import unittest
from datetime import timedelta
from app import create_app
from database.database import db
from database.models import User, PatientCase, CaseAccessToken, CaseAuditEvent, utc_now
from services.case_service import create_patient_case
from services.qr_service import create_case_access_token
from services.access_service import verify_token_and_grant_access, access_case_by_identifier

class AccessControlTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.patient = User(full_name='Patient Sam', email='sam@example.com', role='patient')
        self.patient.set_password('Pass123')
        self.doctor = User(full_name='Dr. House', email='house@clinic.com', role='doctor')
        self.doctor.set_password('DocPass123')
        self.other_patient = User(full_name='Eve Intruder', email='eve@example.com', role='patient')
        self.other_patient.set_password('EvePass123')

        db.session.add_all([self.patient, self.doctor, self.other_patient])
        db.session.commit()

        self.case = create_patient_case(self.patient.id, {
            'chief_complaint': 'Migraine with aura',
            'symptoms': 'Visual flashing lights followed by throbbing unilateral headache',
            'duration': '6 hours',
            'severity': 'Severe (8/10)'
        })

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_doctor_token_verification(self):
        token_obj = self.case.access_tokens.first()
        self.assertIsNotNone(token_obj)

        success, case, msg = verify_token_and_grant_access(token_obj.token_value, self.doctor)
        self.assertTrue(success)
        self.assertEqual(case.id, self.case.id)

        # Check audit event was created
        audit = CaseAuditEvent.query.filter_by(case_id=self.case.id, action='qr_token_verified_and_accessed').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor_id, self.doctor.id)

    def test_non_doctor_cannot_use_doctor_token_access(self):
        token_obj = self.case.access_tokens.first()
        success, case, msg = verify_token_and_grant_access(token_obj.token_value, self.other_patient)
        self.assertFalse(success)
        self.assertIn('Unauthorized', msg)

    def test_revoked_token_fails(self):
        token_obj = self.case.access_tokens.first()
        token_obj.revoked_at = utc_now()
        db.session.commit()

        success, case, msg = verify_token_and_grant_access(token_obj.token_value, self.doctor)
        self.assertFalse(success)
        self.assertIn('revoked', msg.lower())

    def test_barcode_and_manual_identifier_lookup(self):
        # By public case ID
        success, case, msg = access_case_by_identifier(self.case.public_case_id, self.doctor)
        self.assertTrue(success)
        self.assertEqual(case.id, self.case.id)

        # By unhyphenated barcode ID (e.g. PC2026...)
        barcode_id = self.case.public_case_id.replace('-', '')
        success_b, case_b, msg_b = access_case_by_identifier(barcode_id, self.doctor)
        self.assertTrue(success_b)
        self.assertEqual(case_b.id, self.case.id)

if __name__ == '__main__':
    unittest.main()
