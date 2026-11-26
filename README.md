# PATIENTCASE AI
> **"Smarter Case-Taking for Better Care"**

### AI-Assisted Patient Case-Taking Software
**Project Category:** Healthcare Technology + Web Development + AI/NLP

---

## 1. Project Overview

**PatientCase AI** is a full-stack healthcare web application designed to streamline patient clinical intake and triage. The platform empowers patients to describe their symptoms naturally via speech or text in **English (India)** or **Hindi**, automatically converts unstructured patient narratives into structured clinical summaries, generates clarifying follow-up questions, and issues encrypted **QR passes** and **Code 128 barcodes** for clinic check-in.

Physicians access a dedicated clinical console to scan QR passes, retrieve verified case records, document observations, assess provisional diagnoses, and update treatment plans.

### Medical Safety Guarantee
> **IMPORTANT CLINICAL SAFETY NOTICE:** PatientCase AI is strictly an **AI-assisted documentation and intake organization tool**. It does **NOT** autonomously diagnose diseases, prescribe medication, or recommend definitive treatments. Automatically extracted information is clearly demarcated from patient-reported facts, and final clinical assessment remains exclusively with a qualified healthcare professional.

---

## 2. Key Features

- **Multilingual Voice Intake:** Browser Web Speech API integration supporting **English (`en-IN`)** and **Hindi (`hi-IN`)**, with real-time editable transcripts and graceful keyboard text fallback.
- **Deterministic Rule-Based AI Engine:** 100% offline baseline NLP extractor that identifies 60+ symptoms, duration expressions, severity metrics, and aggravating patterns with zero external API fees or heavy model downloads.
- **Dynamic Follow-Up Questions:** Automatically identifies missing clinical dimensions (timeline, severity, radiating pain, allergy history) and asks targeted questions to complete the case.
- **Structured Case Summaries:** Compiles standardized medical documentation with explicit honesty labeling (`Automated preliminary extraction`) and safety disclaimers.
- **QR Code & Code 128 Barcode Passes:** Generates unique public case identifiers (`PC-2026-XXXXXX`), secure opaque QR tokens, and printable triage barcodes with high-resolution SVG/PNG downloads.
- **Doctor Clinical Console:** Dark navy sidebar dashboard featuring interactive **Chart.js** analytics, triage queue, live camera QR/barcode scanner (`html5-qrcode`), file upload scanner, and manual Case ID lookup.
- **Physician Review & Audit Logging:** Doctors can document clinical impressions, recommendations, and status updates (`in_review`, `reviewed`, `completed`), with immutable security audit trail tracking.

---

## 3. Technology Stack

- **Backend:** Python 3.10+, Flask 3.x, Flask Blueprints, Jinja2
- **Database:** SQLAlchemy 2.x, SQLite (auto-initialized and seeded on startup)
- **Security:** Werkzeug password hashing, CSRF session protection, role-based decorators (`@patient_required`, `@doctor_required`)
- **Frontend:** Vanilla JavaScript (ES6+), Bootstrap 5, Font Awesome 6 Icons
- **Data Visualizations:** Chart.js 4.x
- **Identification & Scanning:** QRCode.js, JsBarcode (Code 128), html5-qrcode
- **Testing:** Python `unittest` test suite covering authentication, intake workflows, access control, and NLP extraction

---

## 4. Project Directory Structure

```text
AI-Patient-Case-Taking/
│
├── app.py                     # Main application factory and server entrypoint
├── config.py                  # Environment configurations (dev, testing, prod)
├── requirements.txt           # Python package dependencies
├── README.md                  # Comprehensive documentation
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── database/
│   ├── __init__.py            # Database exports
│   ├── database.py            # SQLAlchemy instance & initializer
│   └── models.py              # User, PatientCase, DoctorNote, Audit models
│
├── routes/
│   ├── __init__.py            # Blueprint registrations
│   ├── auth_routes.py         # Patient registration, login, doctor portal
│   ├── patient_routes.py      # Patient dashboard, profile, case details
│   ├── case_routes.py         # Multi-step intake wizard & submission
│   ├── doctor_routes.py       # Doctor dashboard, reviews, triage queue
│   └── api_routes.py          # Real-time AI extraction & scanner APIs
│
├── services/
│   ├── __init__.py            # Services export
│   ├── ai_service.py          # Modular rule-based clinical NLP extractor
│   ├── case_service.py        # Case creation, statistics, reviews
│   ├── qr_service.py          # Secure QR access tokens and rendering
│   ├── barcode_service.py     # Code 128 barcode formatting and SVG helper
│   └── access_service.py      # Authorization gatekeeper and audit logger
│
├── utils/
│   ├── __init__.py            # Utilities export
│   ├── security.py            # Passwords, CSRF, role-based decorators
│   ├── validators.py          # Input format validators & sanitization
│   ├── helpers.py             # Public case ID generator & status badges
│   └── seed.py                # Development database seeder
│
├── templates/
│   ├── base.html              # Core layout with CDN scripts
│   ├── index.html             # Healthcare landing page
│   ├── 404.html, 403.html, 500.html
│   ├── auth/                  # Login, registration, doctor login
│   ├── patient/               # Dashboard, wizard, summary, QR pass
│   └── doctor/                # Console, camera scanner, case review
│
├── static/
│   ├── css/                   # Modular design system & media print styles
│   ├── js/                    # Voice, AI, QR, Barcode, Scanner, Charts
│   └── images/                # Vector SVG logos, avatars, and hero graphics
│
├── instance/
│   └── patientcase.db         # SQLite database file
│
└── tests/
    ├── __init__.py
    ├── test_auth.py           # Authentication & role protection tests
    ├── test_cases.py          # Case creation and workflow tests
    ├── test_access_control.py # Token security and barcode tests
    └── test_ai_service.py     # Deterministic NLP extraction tests
```

---

## 5. Quick Start & Installation

### Step 1: Clone or Navigate to the Project Directory
```bash
cd "d:\AI ASSISTANT PATEINT CASE-TAKING"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Launch the Web Application
```bash
python app.py
```
The application will automatically initialize the SQLite database and seed initial test accounts upon first launch.

Open your browser and navigate to:
```text
http://localhost:5000
```

---

## 6. Pre-Configured Test Accounts

For immediate testing, use the pre-seeded development accounts:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Doctor** | `doctor@patientcase.ai` | `Doctor@123` | Dr. Sarah Jenkins, MD (General Medicine) |
| **Patient** | `patient@patientcase.ai` | `Patient@123` | Rahul Sharma (Age 34, Male) |

*Tip: Login forms include a 1-click **Auto-Fill** button for instant development testing.*

---

## 7. Running the Automated Test Suite

Execute the complete test suite across authentication, case management, token security, and NLP services:

```bash
python -m unittest discover tests
```

Expected output:
```text
Ran 14 tests in ~3.5s
OK
```

---

## 8. License & Medical Ethics
Built for educational and clinical documentation research. Complies with clinical documentation safety principles by requiring qualified healthcare professional validation for all assessments.
