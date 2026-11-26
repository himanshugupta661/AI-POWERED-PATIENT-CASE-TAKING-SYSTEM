import unittest
from app import create_app
from database.database import db
from database.models import User, PatientCase, FollowUpResponse, DoctorNote
from services.case_service import create_patient_case, add_doctor_review
from utils.helpers import generate_public_case_id

class CaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test patient and doctor
        self.patient = User(full_name='John Patient', email='john@example.com', role='patient')
        self.patient.set_password('Pass123')
        self.doctor = User(full_name='Dr. Adams', email='adams@example.com', role='doctor')
        self.doctor.set_password('DocPass123')
        db.session.add_all([self.patient, self.doctor])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_case_creation_and_public_id(self):
        intake_data = {
            'chief_complaint': 'Throat irritation and mild dry cough',
            'symptoms': 'Dry coughing fits especially at night, slight hoarseness',
            'duration': '3 days',
            'severity': 'Mild (2/10)',
            'pattern': 'Worse at night',
            'medical_history': 'None',
            'allergies': 'None',
            'medications': 'None',
            'family_history': 'None',
            'additional_information': 'Non-smoker'
        }

        followups = [
            {'question': 'Any fever or chills?', 'answer': 'No fever recorded.'}
        ]

        case = create_patient_case(self.patient.id, intake_data, followups, is_draft=False)
        self.assertIsNotNone(case)
        self.assertTrue(case.public_case_id.startswith('PC-'))
        self.assertEqual(case.status, 'submitted')
        self.assertEqual(len(case.follow_up_responses), 1)
        self.assertEqual(case.follow_up_responses[0].answer, 'No fever recorded.')

    def test_doctor_review_and_status_update(self):
        intake_data = {
            'chief_complaint': 'Sprained wrist',
            'symptoms': 'Pain on rotation after fall',
            'duration': '1 day',
            'severity': 'Moderate'
        }
        case = create_patient_case(self.patient.id, intake_data, [], is_draft=False)

        # Doctor reviews
        note = add_doctor_review(
            case=case,
            doctor_id=self.doctor.id,
            note='Wrist tender over distal radius, full active finger range of motion.',
            diagnosis_impression='Mild wrist sprain, rule out scaphoid fracture.',
            clinical_recommendation='Splint for 5 days. Ice QID. Return for repeat X-ray if tenderness persists.',
            new_status='reviewed'
        )

        self.assertEqual(case.status, 'reviewed')
        self.assertEqual(case.assigned_doctor_id, self.doctor.id)
        self.assertIsNotNone(note)
        self.assertEqual(len(case.notes), 1)

if __name__ == '__main__':
    unittest.main()
