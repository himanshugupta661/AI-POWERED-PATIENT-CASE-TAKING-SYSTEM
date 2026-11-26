import unittest
from app import create_app
from database.database import db
from database.models import User, PatientProfile, DoctorProfile

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_patient_registration_and_login(self):
        # Register
        resp = self.client.post('/auth/patient-register', data={
            'full_name': 'Test Patient',
            'email': 'testpatient@example.com',
            'phone': '+91 99999 88888',
            'age': '30',
            'gender': 'Male',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'consent': 'on'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Check DB
        user = User.query.filter_by(email='testpatient@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'patient')
        self.assertTrue(user.check_password('Password@123'))

        # Logout
        self.client.get('/auth/logout', follow_redirects=True)

        # Login again
        login_resp = self.client.post('/auth/login', data={
            'email': 'testpatient@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn(b'Patient Portal', login_resp.data)

    def test_invalid_password_login(self):
        user = User(full_name='Alice', email='alice@example.com', role='patient')
        user.set_password('CorrectPassword')
        db.session.add(user)
        db.session.commit()

        resp = self.client.post('/auth/login', data={
            'email': 'alice@example.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', resp.data)

    def test_doctor_login_authorization(self):
        # Doctor user
        doc = User(full_name='Dr. Smith', email='drsmith@clinic.com', role='doctor')
        doc.set_password('DoctorPass123')
        db.session.add(doc)
        db.session.commit()

        # Doctor login should succeed
        resp = self.client.post('/auth/doctor-login', data={
            'email': 'drsmith@clinic.com',
            'password': 'DoctorPass123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Clinical Physician Console', resp.data)

    def test_patient_blocked_from_doctor_route(self):
        patient = User(full_name='Bob', email='bob@example.com', role='patient')
        patient.set_password('BobPass123')
        db.session.add(patient)
        db.session.commit()

        # Login as patient
        self.client.post('/auth/login', data={
            'email': 'bob@example.com',
            'password': 'BobPass123'
        }, follow_redirects=True)

        # Attempt to access doctor dashboard
        resp = self.client.get('/doctor/dashboard')
        self.assertEqual(resp.status_code, 403)

if __name__ == '__main__':
    unittest.main()
