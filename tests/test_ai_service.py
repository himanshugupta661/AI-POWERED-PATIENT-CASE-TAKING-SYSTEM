import unittest
from services.ai_service import ai_service, RuleBasedAIProvider

class AIServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.provider = RuleBasedAIProvider()

    def test_nlp_extraction_baseline(self):
        sample_input = "I have had a severe cough for five days and it gets worse at night."
        extracted = self.provider.extract(sample_input)

        self.assertIn('Cough', extracted['detected_symptoms'])
        self.assertIn('five days', extracted['duration'].lower())
        self.assertIn('severe', extracted['severity'].lower())
        self.assertIn('worse at night', extracted['pattern'].lower())
        self.assertEqual(extracted['extraction_source'], 'Automated preliminary extraction')

    def test_extraction_with_fever_and_headache(self):
        sample_input = "Moderate fever since yesterday with headache and chills."
        extracted = self.provider.extract(sample_input)

        self.assertIn('Fever', extracted['detected_symptoms'])
        self.assertIn('Headache', extracted['detected_symptoms'])
        self.assertIn('yesterday', extracted['duration'].lower())
        self.assertIn('moderate', extracted['severity'].lower())

    def test_followup_question_generation(self):
        # Case data missing duration and severity
        case_data = {
            'chief_complaint': 'Cough and throat pain',
            'symptoms': 'Dry coughing and irritation in throat',
            'duration': '',
            'severity': '',
            'pattern': '',
            'allergies': 'Not specified',
            'medications': 'Not specified'
        }

        questions = self.provider.generate_followup(case_data)
        self.assertGreater(len(questions), 0)

        # Ensure targeted categories are generated
        categories = [q['category'] for q in questions]
        self.assertTrue('Timeline' in categories or 'Severity' in categories or 'Respiratory Detail' in categories)

    def test_structured_summary_includes_safety_disclaimer(self):
        case_data = {
            'chief_complaint': 'Mild headache',
            'symptoms': 'Throbbing frontal headache',
            'duration': '2 hours',
            'severity': 'Mild',
            'pattern': 'Constant',
            'medical_history': 'No history',
            'allergies': 'None',
            'medications': 'None'
        }

        summary = self.provider.generate_summary(case_data)
        self.assertIn('medical_safety_disclaimer', summary)
        disclaimer = summary['medical_safety_disclaimer']
        self.assertIn('does NOT constitute a medical diagnosis', disclaimer)
        self.assertIn('physician', disclaimer)
        self.assertEqual(summary['intake_analysis_metadata']['processing_type'], 'Automated preliminary extraction')

if __name__ == '__main__':
    unittest.main()
