import re
import os
from typing import Dict, Any, List

class AIProviderInterface:
    """Base interface for AI/NLP extraction providers."""
    def extract(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError
        
    def generate_followup(self, case_data: Dict[str, Any]) -> List[Dict[str, str]]:
        raise NotImplementedError
        
    def generate_summary(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class RuleBasedAIProvider(AIProviderInterface):
    """
    Guaranteed deterministic baseline rule-based NLP extraction service.
    Requires 0 paid APIs, 0 heavy model downloads, and runs 100% offline.
    Honesty label: 'Automated preliminary extraction'.
    """

    # Clinical symptom patterns
    SYMPTOM_PATTERNS = {
        'Cough': [r'\bcough(ing)?\b', r'\bkhansi\b'],
        'Fever': [r'\bfever\b', r'\bhigh temperature\b', r'\bchills\b', r'\bbukhar\b', r'\bpyrexia\b'],
        'Headache': [r'\bheadache\b', r'\bhead pain\b', r'\bmigraine\b', r'\bsir dard\b'],
        'Chest Pain': [r'\bchest pain\b', r'\bchest tightness\b', r'\bchest pressure\b'],
        'Shortness of Breath': [r'\bshort(ness)? of breath\b', r'\bdifficulty breathing\b', r'\bbreathless\b', r'\bsaans\b'],
        'Back Pain': [r'\bback pain\b', r'\bbackache\b', r'\blumber\b', r'\blumbo-sacral\b', r'\bkamar dard\b'],
        'Sore Throat': [r'\bsore throat\b', r'\bthroat pain\b', r'\bscratchy throat\b', r'\bgale me dard\b'],
        'Abdominal Pain': [r'\bstomach ache\b', r'\bstomach pain\b', r'\babdominal pain\b', r'\bcramps\b', r'\bpet dard\b'],
        'Nausea / Vomiting': [r'\bnausea\b', r'\bvomit(ing)?\b', r'\bqueasy\b', r'\bulti\b'],
        'Fatigue': [r'\bfatigue\b', r'\btired(ness)?\b', r'\bexhaust(ion)?\b', r'\blethargic\b', r'\bkamzori\b'],
        'Dizziness': [r'\bdizz(y|iness)\b', r'\blightheaded\b', r'\bvertigo\b', r'\bchakkar\b'],
        'Skin Rash': [r'\brash\b', r'\bitching\b', r'\bhives\b', r'\bred spots\b', r'\bkhujli\b'],
        'Joint Pain': [r'\bjoint pain\b', r'\barthr(itis|algia)\b', r'\bknee pain\b', r'\bshoulder pain\b'],
        'Diarrhea': [r'\bdiarrhea\b', r'\bloose motion\b', r'\bloose stool\b', r'\bdast\b'],
        'Runny Nose': [r'\brunny nose\b', r'\bcongestion\b', r'\bcold\b', r'\bsneezing\b', r'\bzukam\b']
    }

    # Duration patterns
    DURATION_PATTERNS = [
        r'(for\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a few|several)\s+(days?|weeks?|months?|hours?|years?)',
        r'(since\s+)?(yesterday|last night|last week|last month|this morning|a couple of days)',
        r'(past\s+)(\d+|few|couple of)\s+(days?|weeks?|months?)',
        r'(\d+)\s*-\s*(\d+)\s*(days?|weeks?)'
    ]

    # Severity patterns
    SEVERITY_PATTERNS = [
        (r'\b(severe|intense|excruciating|unbearable|very bad|acute|terrible)\b', 'Severe (8-10/10)'),
        (r'\b(moderate|manageable|medium|average)\b', 'Moderate (4-7/10)'),
        (r'\b(mild|slight|minor|little|tolerable)\b', 'Mild (1-3/10)'),
        (r'\b([1-9]|10)\s*(out of|\/)\s*10\b', r'Patient-rated \g<0>'),
        (r'\bscale of (10|[1-9])\b', r'Rated \g<0>')
    ]

    # Pattern / Aggravating factors
    PATTERN_PATTERNS = [
        r'\b(worse\s+at\s+night|worse\s+in\s+the\s+evening)\b',
        r'\b(worse\s+in\s+the\s+morning)\b',
        r'\b(comes\s+and\s+goes|intermittent|periodic|on\s+and\s+off)\b',
        r'\b(constant|continuous|persistent|unrelenting)\b',
        r'\b(after\s+eating|post\s+meals?)\b',
        r'\b(when\s+walking|when\s+bending|during\s+exercise|when\s+resting)\b',
        r'\b(sudden\s+onset|gradual\s+onset)\b'
    ]

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract structured medical information from patient narrative text."""
        if not text:
            return {
                'chief_complaint': '',
                'detected_symptoms': [],
                'duration': '',
                'severity': '',
                'pattern': '',
                'extraction_source': 'Automated preliminary extraction (rule-based)',
                'confidence': 'baseline'
            }

        text_lower = text.lower()

        # 1. Detect symptoms
        detected_symptoms = []
        for symptom_name, regex_list in self.SYMPTOM_PATTERNS.items():
            for regex in regex_list:
                if re.search(regex, text_lower):
                    detected_symptoms.append(symptom_name)
                    break

        # 2. Extract Duration
        extracted_duration = ""
        for pattern in self.DURATION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                extracted_duration = match.group(0).strip()
                break

        # 3. Extract Severity
        extracted_severity = ""
        for regex, label in self.SEVERITY_PATTERNS:
            match = re.search(regex, text_lower)
            if match:
                if '\\g<' in label:
                    extracted_severity = match.expand(label).capitalize()
                else:
                    extracted_severity = label
                break

        # 4. Extract Pattern
        extracted_pattern = ""
        for pattern in self.PATTERN_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                extracted_pattern = match.group(0).strip().capitalize()
                break

        # 5. Determine Chief Complaint candidate
        chief_complaint = ""
        if detected_symptoms:
            chief_complaint = detected_symptoms[0]
            if len(detected_symptoms) > 1:
                chief_complaint += f" with {', '.join(detected_symptoms[1:3])}"
        else:
            # Fallback: take first clause up to 80 chars
            first_sentence = text.split('.')[0].strip()
            chief_complaint = (first_sentence[:80] + '...') if len(first_sentence) > 80 else first_sentence

        return {
            'chief_complaint': chief_complaint,
            'detected_symptoms': detected_symptoms,
            'duration': extracted_duration,
            'severity': extracted_severity,
            'pattern': extracted_pattern,
            'extraction_source': 'Automated preliminary extraction',
            'confidence': 'Standard Rule-Based Baseline',
            'review_notice': 'Please review and adjust these automatically recognized values before continuing.'
        }

    def generate_followup(self, case_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate targeted clinical follow-up questions to fill in missing information.
        Does not force diagnosis; focuses on comprehensive intake.
        """
        questions = []
        complaint = (case_data.get('chief_complaint') or '').lower()
        symptoms = (case_data.get('symptoms') or '').lower()
        full_text = f"{complaint} {symptoms}"

        # Check missing duration
        if not case_data.get('duration'):
            questions.append({
                'id': 'q_duration',
                'category': 'Timeline',
                'question': 'When did you first notice these symptoms, and how has the intensity changed over time?'
            })

        # Check missing severity
        if not case_data.get('severity'):
            questions.append({
                'id': 'q_severity',
                'category': 'Severity',
                'question': 'On a scale from 1 (very mild) to 10 (unbearable), how severe is your discomfort right now?'
            })

        # Check missing pattern
        if not case_data.get('pattern'):
            questions.append({
                'id': 'q_pattern',
                'category': 'Symptom Pattern',
                'question': 'Is the symptom constant throughout the day, or does anything specific make it better or worse (e.g., resting, moving, eating)?'
            })

        # Symptom-specific targeted questions
        if 'cough' in full_text or 'breathing' in full_text or 'throat' in full_text:
            questions.append({
                'id': 'q_respiratory',
                'category': 'Respiratory Detail',
                'question': 'Is your cough producing any phlegm/mucus or blood, and are you having any trouble breathing or chest tightness?'
            })

        if 'fever' in full_text or 'temperature' in full_text:
            questions.append({
                'id': 'q_fever',
                'category': 'Temperature',
                'question': 'Have you measured your body temperature with a thermometer, and have you experienced chills or night sweats?'
            })

        if 'pain' in full_text or 'ache' in full_text:
            questions.append({
                'id': 'q_pain_radiation',
                'category': 'Pain Quality',
                'question': 'Does the pain stay in one specific spot, or does it radiate or spread to other parts of your body?'
            })

        if 'stomach' in full_text or 'nausea' in full_text or 'vomit' in full_text or 'abdomen' in full_text:
            questions.append({
                'id': 'q_gi',
                'category': 'Digestive System',
                'question': 'Have you experienced any vomiting, loss of appetite, changes in bowel habits, or intolerance to food or liquids?'
            })

        # Check medications & allergies
        if not case_data.get('medications') or case_data.get('medications') == 'Not specified':
            questions.append({
                'id': 'q_meds',
                'category': 'Current Medications',
                'question': 'Are you taking any over-the-counter or prescription medicines, inhalers, or home remedies for this condition?'
            })

        if not case_data.get('allergies') or case_data.get('allergies') == 'Not specified':
            questions.append({
                'id': 'q_allergies',
                'category': 'Allergy Verification',
                'question': 'Do you have any known allergies to medicines (such as penicillin, sulfa, ibuprofen) or foods?'
            })

        # Provide a general baseline if all details were already covered
        if not questions:
            questions.append({
                'id': 'q_general',
                'category': 'Additional Context',
                'question': 'Is there any other symptom, previous medical event, or detail that you feel the doctor should know?'
            })

        # Cap follow-up questions to 5 so patient is not overwhelmed
        return questions[:5]

    def generate_summary(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize raw and extracted patient responses into a structured medical intake summary.
        Clearly separates patient-reported facts from automated preliminary extraction.
        """
        return {
            'case_header': {
                'title': 'AI-Assisted Patient Intake Documentation',
                'timestamp': case_data.get('created_at', ''),
                'status': 'Pending Clinical Review'
            },
            'patient_reported_intake': {
                'chief_complaint': case_data.get('chief_complaint', 'Not provided'),
                'symptoms_narrative': case_data.get('symptoms', 'Not provided'),
                'reported_duration': case_data.get('duration') or 'Not reported by patient',
                'reported_severity': case_data.get('severity') or 'Not reported by patient',
                'reported_pattern': case_data.get('pattern') or 'Not reported by patient'
            },
            'clinical_background': {
                'past_medical_history': case_data.get('medical_history') or 'No past history reported',
                'known_allergies': case_data.get('allergies') or 'No known allergies reported',
                'current_medications': case_data.get('medications') or 'No current medications reported',
                'family_history': case_data.get('family_history') or 'Not provided / Non-contributory',
                'additional_information': case_data.get('additional_information') or 'None'
            },
            'intake_analysis_metadata': {
                'processing_type': 'Automated preliminary extraction',
                'nlp_engine': 'PatientCase Rule-Based Clinical Intake Engine v1.0',
                'requires_physician_verification': True
            },
            'medical_safety_disclaimer': (
                "IMPORTANT NOTICE: This document is an AI-assisted structured intake summary. "
                "It is designed solely for preliminary clinical documentation and does NOT constitute "
                "a medical diagnosis, prognosis, prescription, or clinical assessment. All findings "
                "must be independently reviewed and validated by a licensed physician or qualified "
                "healthcare professional."
            )
        }


class AIService:
    """
    Modular AI Service dispatcher.
    Uses RuleBasedAIProvider by default with zero external dependencies.
    Can be seamlessly extended with local LLM or API provider if configured.
    """
    def __init__(self):
        provider_name = os.environ.get('AI_PROVIDER', 'rule_based').lower()
        if provider_name == 'rule_based':
            self.provider = RuleBasedAIProvider()
        else:
            # Fallback to rule-based baseline
            self.provider = RuleBasedAIProvider()

    def extract_case_information(self, text: str) -> Dict[str, Any]:
        return self.provider.extract(text)

    def generate_followup_questions(self, case_data: Dict[str, Any]) -> List[Dict[str, str]]:
        return self.provider.generate_followup(case_data)

    def generate_structured_summary(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.provider.generate_summary(case_data)

# Singleton instance for application usage
ai_service = AIService()
