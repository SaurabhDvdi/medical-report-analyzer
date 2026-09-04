# 🏥 Medical Report Analyzer & AI Clinical Intelligence Platform

> An enterprise-grade, full-stack medical intelligence platform combining automated OCR document ingestion, longitudinal lab analytics, consent-driven doctor-patient collaboration, and a **LangGraph-orchestrated AI Clinical Assistant** powered by **Model Context Protocol (MCP)** tools and hybrid LLM support (Ollama & Groq).

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Key Capabilities & Features](#-key-capabilities--features)
3. [System Architecture](#-system-architecture)
4. [Tech Stack](#-tech-stack)
5. [Complete Project Structure](#-complete-project-structure)
6. [Data Architecture & Database Models](#-data-architecture--database-models)
7. [AI Agent & MCP Architecture](#-ai-agent--mcp-architecture)
8. [Complete Model Context Protocol (MCP) Tool Suite](#-complete-model-context-protocol-mcp-tool-suite)
9. [Security & Access Control Matrix](#-security--access-control-matrix)
10. [Exhaustive API Reference](#-exhaustive-api-reference)
11. [Frontend Component & Page Inventory](#-frontend-component--page-inventory)
12. [Setup & Installation Guide](#-setup--installation-guide)
13. [Environment Configuration (`.env`)](#-environment-configuration-env)
14. [Testing & Quality Assurance](#-testing--quality-assurance)
15. [Limitations & Future Roadmap](#-limitations--future-roadmap)

---

## 🎯 Project Overview

Modern medical care is often fragmented. Patients receive diagnostic laboratory reports in physical or unstructured PDF formats, making it difficult to detect long-term health trends or abnormal lab value shifts over time. Healthcare providers also face challenges when retrieving grounded patient histories, analyzing multi-report deltas, and providing clinical decision support.

The **Medical Report Analyzer** bridges this gap by transforming static, unstructured medical documents into structured, actionable intelligence:

- **For Patients:** Upload medical reports (PDF/images), track lab parameters over time with interactive time-series charts, analyze longitudinal health trends, manage current/past medication regimens, calculate health risks, find specialized doctors, grant/revoke doctor data access, and interact with an AI Assistant grounded in their own personal medical data.
- **For Healthcare Providers (Doctors):** Request and manage patient access, inspect approved patient histories, compare historical reports side-by-side with calculated percentage deltas, review AI summaries, add clinical consultation/examination notes, and utilize an AI Assistant strictly scoped to authorized patient records.

---

## 🔥 Key Capabilities & Features

### 🧠 1. LangGraph AI Clinical Assistant
- **Intent Recognition & State Orchestration:** Custom LangGraph `StateGraph` workflow classifying user queries into discrete intent routes (`CLINICAL`, `MY_DOCTORS`, `DOCTOR_DIRECTORY`, `MY_PATIENTS`, `APPLICATION_HELP`).
- **Hybrid Multi-LLM Backend:** Multi-provider architecture supporting offline local inference via **Ollama** (e.g., `qwen2.5:3b`, `llama2`, `llama3`) and cloud inference via **Groq Cloud API** (`llama-3.1-8b-instant`, `mixtral-8x7b-32768`).
- **Grounding & Source Transparency:** All AI responses include inline source citations (`[Patient Profile]`, `[Lab Parameter: HbA1c]`, `[Medical Glossary]`, `[Doctor Directory]`), tools executed log, and active security boundary checks.
- **Automated Follow-Up Suggestions:** Integrated `SuggestionService` generating 3 contextually relevant follow-up questions after every chat response.

### 🔌 2. Security-Scoped Model Context Protocol (MCP) Tool Suite
- **18 Standardized MCP Tools:** Standardized tool registry carrying an immutable `SecurityContext` enforcing requesting user ID, role (`patient`/`doctor`), target patient ID, and database transaction scope.
- **Role Boundary Controls:** Doctors can only execute tools against patients who have explicitly granted approved data access. Patients can only query their own records.

### 📄 3. Robust Multi-Engine Document OCR & Parsing Pipeline
- **Multi-Engine OCR Strategy:** Automatic text extraction from PDF and image files (PNG, JPG, JPEG) using PyTesseract, EasyOCR, and PyMuPDF (`fitz`) fallback, with optional Poppler (`pdf2image`) support.
- **Regex & Pattern Extraction Engine:** Automatic parsing of lab parameter names, quantitative values, measurement units, and reference ranges.
- **Automatic Range Normalization & Flagging:** Standardizes units and flags abnormal values (`is_abnormal`) against clinical bounds.
- **AI Clinical Summarization:** Integrated `LLMService` generating concise clinical summaries of extracted document text during ingestion.

### 📈 4. Advanced Health Analytics & Report Comparison
- **Linear Regression Trends:** Time-series tracking of lab parameter trajectory over multiple report dates with calculated trend slopes (improving, stable, worsening).
- **Longitudinal Health Trends & Trajectories:** Multi-parameter trajectory tracking highlighting biomarker shifts, rates of change, and baseline deviations over time.
- **Side-by-Side Longitudinal Comparison:** Deterministic report comparison calculating absolute values, parameter deltas, percentage changes, and status shifts (e.g., `Normal` ➔ `Elevated`).
- **Health Risk & Insights Engine:** Evaluates overall patient risk scores and generates structured clinical observations based on flagged anomalies.

### 👨‍⚕️ 5. Consent-Driven Doctor-Patient Access System
- **Clinical Taxonomy:** Structured categorization of doctors by clinical specialty (`DoctorCategory`, `DoctorSpecialty`) with custom specialty creation on registration.
- **Patient Sovereignty Lifecycle:** Explicit access request, approval, rejection, and revocation workflow (`pending`, `approved`/`accepted`, `rejected`, `revoked`).
- **Doctor Patient Inspection View:** Dedicated interface for doctors to review approved patient profiles, lab timelines, report deltas, and record clinical notes.

### 💊 6. Medication Regimen & Interaction Tracking
- **Medication Management:** Track active/current and past prescribed medications with dosage, frequency, and date ranges.
- **Drug Interaction Engine:** Evaluates known drug-drug contraindications and warnings via MCP tool execution.

### 📝 7. Doctor Clinical Consultation Notes
- **Linked Doctor Notes:** Doctors can record structured notes (`consultation`, `examination`, `followup`) attached to patient profiles and specific medical reports.

---

## 🏗️ System Architecture

```text
                                  +---------------------------------------+
                                  |         React 18 Frontend             |
                                  | (Vite + TailwindCSS + Recharts + Query)|
                                  +-------------------+-------------------+
                                                      |
                                             HTTP / REST API Calls
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |            FastAPI Backend            |
                                  |  (JWT Auth + SQLAlchemy + Pydantic)   |
                                  +-------------------+-------------------+
                                                      |
                                        +-------------+-------------+
                                        |                           |
                                        v                           v
                           +------------------------+  +------------------------+
                           |  REST Services & ORM   |  |   AI Clinical Agent    |
                           | (OCR, Analytics, DB)   |  |   (LangGraph Engine)   |
                           +-----------+------------+  +-----------+------------+
                                       |                           |
                                       |                           v
                                       |              +-------------------------+
                                       |              |  MCP Client / Registry  |
                                       |              |   (Security Context)    |
                                       |              +------------+------------+
                                       |                           |
                                       |             +-------------+-------------+
                                       |             |                           |
                                       v             v                           v
                           +------------------------+  +------------------------+  +------------------------+
                           |  Database Layer        |  | Grounded RAG &         |  | LLM Provider           |
                           |  (SQLite / PyMySQL)    |  | Analytics Services     |  | (Ollama / Groq Cloud)  |
                           +------------------------+  +------------------------+  +------------------------+
```

---

## 💻 Tech Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+, FastAPI, Uvicorn | High-performance asynchronous REST API backend |
| **Database & ORM** | SQLAlchemy, SQLite / PyMySQL | Relational database mapping, migrations & persistence |
| **Authentication & Security**| JWT (`python-jose`), `passlib` (`bcrypt`) | Token-based role authentication & password hashing |
| **AI Orchestration** | LangGraph, LangChain Core / Community | StateGraph agent workflow & intent routing |
| **Tool Architecture** | Model Context Protocol (MCP) | Standardized, role-scoped tool execution layer |
| **LLM Providers** | Ollama (`langchain-ollama`), Groq / OpenAI (`langchain-groq`, `openai`) | Hybrid local offline or cloud LLM inference |
| **Document Ingestion & OCR**| PyTesseract, EasyOCR, PyMuPDF (`fitz`), `pdf2image`, Pillow | Text extraction from PDF & image medical reports |
| **Analytics & Data Science**| Pandas, NumPy, SciPy, Scikit-Learn | Linear regression trends & Pearson correlation matrices |
| **Chart Generation** | Matplotlib, Seaborn | Server-side correlation heatmap rendering |
| **Frontend Framework** | React 18, Vite, React Router v6 | Fast single-page web application frontend |
| **State & Data Fetching** | TanStack React Query v5 | Client-side query caching, refetching & mutation state |
| **Styling & UI Components** | Tailwind CSS, Framer Motion, Radix UI | Dark/light theme styling, animations & dialog modals |
| **Data Visualizations** | Recharts | Interactive time-series trends & correlation heatmaps |
| **Icons & Micro-UI** | Lucide React, Heroicons, React Hot Toast | Icon sets & toast notifications |
| **Testing** | Pytest, HTTPX | Automated backend & AI test execution |

---

## 📁 Complete Project Structure

```text
medical-report-analyzer/
├── README.md                      # Primary comprehensive project documentation
├── QUICKSTART.md                  # Concise setup & quickstart guide
├── IMPLEMENTATION_NOTES.md        # Technical implementation & fallback notes
├── docs.txt                       # Consolidated documentation reference
│
├── backend/                       # Python FastAPI Backend Architecture
│   ├── main.py                    # Application entrypoint & primary REST API endpoints
│   ├── database.py                # Database connection lifecycle & session setup
│   ├── models.py                  # SQLAlchemy ORM database tables & relationships
│   ├── schemas.py                 # Pydantic request/response validation models
│   ├── auth.py                    # JWT authentication dependency & password hashing
│   ├── logging_config.py          # Centralized rotating file & console logger
│   ├── .env                       # Environment configuration file
│   ├── .env.example               # Example environment variable template
│   ├── requirements.txt           # Python dependencies manifest
│   ├── medical_reports.db         # SQLite database file (autogenerated on startup)
│   │
│   ├── ai/                        # AI Assistant & LangGraph Subsystem
│   │   ├── agent.py               # LangGraph ClinicalAssistantAgent & StateGraph workflow
│   │   ├── llm_service.py         # Provider abstraction for Ollama & Groq LLMs
│   │   ├── rag_service.py         # Grounded patient context & medical glossary retrieval
│   │   ├── suggestion_service.py  # Follow-up question suggestion generator
│   │   └── config.py              # AI configuration parameters & default models
│   │
│   ├── mcp/                       # Model Context Protocol (MCP) Layer
│   │   ├── tools.py               # MCPToolRegistry & SecurityContext (18 security tools)
│   │   └── client.py              # MCPClient wrapper for safe tool execution
│   │
│   ├── routes/                    # Modular API Routers
│   │   ├── ai_routes.py           # /api/ai/chat and /api/ai/compare-reports
│   │   └── dashboard.py           # /api/dashboard data endpoints
│   │
│   ├── services/                  # Core Business Logic & Analytics Engines
│   │   ├── ocr_service.py         # Multi-engine OCR (Tesseract, EasyOCR, PyMuPDF, Poppler)
│   │   ├── report_parser.py       # Regex lab parameter extraction engine
│   │   ├── normalizer.py          # Unit & reference range normalization
│   │   ├── extractor.py           # Lab value parsing & status classification
│   │   ├── analytics_service.py   # Trend analysis & Pearson correlation heatmaps
│   │   ├── comparison_service.py  # Report comparison & parameter delta engine
│   │   ├── risk_engine.py         # Patient health risk evaluation engine
│   │   ├── insights.py            # Automated clinical observations engine
│   │   └── doctor_taxonomy_seed.py# Medical categories & specialties database seeder
│   │
│   └── tests/                     # Automated Test Suite
│       ├── test_agent_security_and_tools.py # MCP tools & security context tests
│       ├── test_ai_security.py             # Unauthorized doctor access tests
│       ├── test_ollama_langgraph.py        # LangGraph execution & node tests
│       └── test_suggested_questions.py     # Follow-up question generator tests
│
└── frontend/                      # React 18 Frontend Architecture
    ├── index.html                 # Main HTML document template
    ├── vite.config.js             # Vite build & proxy configuration
    ├── tailwind.config.js         # Tailwind CSS styling configuration
    ├── postcss.config.js          # PostCSS processor configuration
    ├── package.json               # Frontend dependencies manifest
    │
    └── src/
        ├── App.jsx                # Router, Auth Provider & Protected Routes
        ├── main.jsx               # React DOM entrypoint
        ├── index.css              # Global styles & Tailwind directives
        │
        ├── contexts/
        │   └── AuthContext.jsx    # User session state, JWT token storage & login/logout
        │
        ├── pages/                 # Full-Page React Components (14 Views)
        │   ├── Login.jsx          # Login view
        │   ├── Register.jsx       # Registration view with Patient/Doctor role selection
        │   ├── PatientDashboard.jsx # Executive patient health dashboard
        │   ├── DoctorDashboard.jsx  # Doctor practice dashboard & patient list
        │   ├── DoctorInterface.jsx  # Doctor patient inspection view & notes manager
        │   ├── Reports.jsx        # Report upload drag-and-drop & report catalog
        │   ├── ReportViewer.jsx   # Single report details, lab table & document view
        │   ├── HealthSummaryPage.jsx # Health metrics & parameter status overview
        │   ├── HealthTrendsPage.jsx # Longitudinal health trends & parameter trajectory view
        │   ├── MedicalDashboard.jsx# Multi-parameter comparative health view
        │   ├── Medicines.jsx      # Current & past medication tracker
        │   ├── FindDoctors.jsx    # Doctor directory & access request interface
        │   ├── PatientProfile.jsx # Patient medical history & profile editor
        │   └── DoctorProfile.jsx  # Doctor professional credentials & clinic profile
        │
        └── components/            # Reusable UI Components (11 Components)
            ├── AIAssistantModal.jsx # Floating AI Assistant chat modal with citations
            ├── Layout.jsx         # Sidebar navigation & header container
            ├── TrendChart.jsx     # Recharts lab value time-series chart
            ├── ParameterCard.jsx  # Individual lab parameter status display
            ├── InsightsPanel.jsx  # AI clinical insights & observation card
            ├── RiskBadge.jsx      # Color-coded risk status badges
            ├── FormComponents.jsx # Reusable form fields & selectors
            ├── EnhancedCards.jsx  # Styled summary & metrics display cards
            ├── Skeletons.jsx      # Loading skeleton components
            ├── Toast.jsx          # Toast notification provider & alerts
            └── RoleRoute.jsx      # Route protection guard by user role
```

---

## 🗄️ Data Architecture & Database Models

The database schema (SQLAlchemy ORM) defines 11 interlinked tables enforcing strict data integrity:

| Table Name | Model Class | Key Fields & Relationships |
| :--- | :--- | :--- |
| `users` | `User` | `id`, `email`, `password_hash`, `full_name`, `role` (`patient`/`doctor`), `doctor_category_id`, `doctor_specialty_id`, `created_at`. Relates to: `reports`, `medicines`, `doctor_profile`, `patient_profile`. |
| `patient_profiles` | `PatientProfile` | `user_id`, `age`, `gender`, `height_cm`, `weight_kg`, `bmi`, `blood_group`, `allergies`, `chronic_conditions`, `emergency_contact`. |
| `doctor_profiles` | `DoctorProfile` | `user_id`, `degrees`, `specialization`, `experience_years`, `license_number`, `clinic_name`, `clinic_address`, `clinic_phone`, `clinic_email`, `bio`. |
| `doctor_categories`| `DoctorCategory` | `id`, `name`, `description`. Categorizes doctor specialties (e.g., General Medicine, Cardiology, Endocrinology). |
| `doctor_specialties` | `DoctorSpecialty` | `id`, `category_id`, `name`, `description`. Specific medical sub-specialty. |
| `patient_doctor_access` | `PatientDoctorAccess` | `patient_id`, `doctor_id`, `status` (`pending`, `approved`/`accepted`, `rejected`, `revoked`), `requested_by`, `request_date`, `response_date`. |
| `report_categories`| `ReportCategory` | `id`, `name`, `description`. Report types (e.g., Blood Test, Lipid Profile, Thyroid Panel). |
| `reports` | `Report` | `id`, `user_id`, `category_id`, `file_name`, `file_path`, `ocr_status`, `extracted_text`, `ai_summary`, `report_date`, `upload_date`. |
| `lab_values` | `LabValue` | `id`, `report_id`, `parameter_name`, `value`, `unit`, `reference_range`, `is_abnormal`. |
| `medicines` | `Medicine` | `id`, `user_id`, `name`, `dosage`, `frequency`, `start_date`, `end_date`, `status` (`current`/`past`), `notes`. |
| `doctor_notes` | `DoctorNote` | `id`, `doctor_id`, `patient_id`, `report_id`, `note_text`, `note_type` (`consultation`, `examination`, `followup`), `created_at`. |

---

## 🤖 AI Agent & MCP Architecture

### LangGraph Workflow Execution
When a user query is sent to `/api/ai/chat`, the `ClinicalAssistantAgent` builds a `StateGraph` state container and runs through execution nodes:

```text
[Input Query] ➔ [Security Scoping] ➔ [Intent Router] ➔ [MCP Tool Resolution] ➔ [LLM Generation] ➔ [Citations & Suggestions]
```

1. **Security Scoping Node:** Resolves requesting user credentials (`SecurityContext`) and enforces that doctor queries target only authorized patient IDs.
2. **Intent Router Node:** Evaluates query intent (`CLINICAL`, `MY_DOCTORS`, `DOCTOR_DIRECTORY`, `MY_PATIENTS`, `APPLICATION_HELP`).
3. **MCP Tool Resolution Node:** Dynamically binds and executes relevant tools from `MCPToolRegistry`.
4. **LLM Generation Node:** Sends formatted prompt with grounded context to active LLM (`Ollama` or `Groq`).
5. **Citations & Suggestions Node:** Formats final response with citations (`[Patient Profile]`, `[Lab Parameter: Glucose]`, etc.) and appends 3 follow-up question suggestions via `SuggestionService`.

---

## 🔌 Complete Model Context Protocol (MCP) Tool Suite

The platform includes **18 security-scoped MCP tools** implemented in `backend/mcp/tools.py`:

| Tool Name | Scope / Role | Description |
| :--- | :--- | :--- |
| `get_patient_history` | Patient / Doctor | Retrieves full grounded patient history (profile, lab parameters, medicines, notes). |
| `get_health_summary` | Patient / Doctor | Fetches overall health metrics, report counts, and flagged abnormal lab values. |
| `get_lab_trend` | Patient / Doctor | Calculates time-series linear regression trend for a specific lab parameter. |
| `compare_reports` | Patient / Doctor | Deterministically compares two medical reports and calculates parameter deltas. |
| `calculate_health_risk` | Patient / Doctor | Evaluates health risk levels, risk scores, and confidence metrics. |
| `search_medical_guidelines` | General | Searches medical terminology, definitions, and standard reference ranges. |
| `check_drug_interactions` | General | Checks list of active/prescribed medications for known drug interactions. |
| `search_doctors` | General | Searches doctor directory by name, specialty, clinic, or experience level. |
| `get_doctor_profile` | General | Retrieves detailed profile information for a specific doctor by ID. |
| `get_doctor_specialties` | General | Fetches all medical categories and sub-specialties available on the platform. |
| `get_my_patient_count` | Doctor | Counts active authorized patients connected to the authenticated doctor. |
| `get_my_patients` | Doctor | Lists all authorized patients with profile details for the authenticated doctor. |
| `search_my_patients` | Doctor | Searches by name or email within the doctor's authorized active patients. |
| `resolve_my_patient` | Doctor | Resolves patient name ambiguity strictly within doctor's authorized list. |
| `get_my_doctors` | Patient | Lists all doctors with access status connected to the authenticated patient. |
| `get_my_reports` | Patient / Doctor | Retrieves list of uploaded medical reports for the target patient. |
| `get_my_medicines` | Patient / Doctor | Lists active and past medications for the target patient. |
| `get_website_help` | General | Provides grounded instructions for using website features and workflows. |

---

## 🔒 Security & Access Control Matrix

Data access is strictly enforced by FastAPI authorization dependencies (`auth.py` and `check_doctor_access`):

| Requester Role | Target Data | Status | Access Granted? | Rule / Enforcement |
| :--- | :--- | :---: | :---: | :--- |
| **Patient** | Self Data | Any | ✅ Granted | Patients can always access their own reports, trends, and profile. |
| **Patient** | Other Patient | Any | ❌ Denied | Target patient ID is forced to requesting user's own ID. |
| **Doctor** | Patient Data | `approved`/`accepted` | ✅ Granted | Allowed if an approved `PatientDoctorAccess` record exists. |
| **Doctor** | Patient Data | `pending`/`rejected`/`revoked` | ❌ Denied | Throws `403 Forbidden` error immediately. |
| **Unauthenticated**| Any | None | 开启 Denied | Throws `401 Unauthorized` token missing/expired error. |

---

## 🔌 Exhaustive API Reference

### 1. Authentication Endpoints
- `POST /api/auth/register` — Register new user (Patient or Doctor with category/specialty selection).
- `POST /api/auth/login` — Authenticate user and receive JWT access token.

### 2. Medical Reports & OCR Endpoints
- `POST /api/reports/upload` — Upload medical report PDF or image file (triggers OCR & AI summary).
- `GET /api/reports` — Fetch all reports for authenticated patient (or authorized target patient).
- `GET /api/reports/summary` — Get overall summary of patient's reports and lab count.
- `GET /api/reports/{report_id}` — Get single report details with extracted lab values table.
- `DELETE /api/reports/{report_id}` — Delete a specific medical report.
- `GET /api/reports/{report_id}/download` — Download original uploaded report file.
- `GET /api/lab-values` — Fetch raw extracted lab values across reports.

### 3. AI Clinical Assistant Endpoints
- `POST /api/ai/chat` — Submit query to AI Assistant (supports `patient_id` targeting).
- `POST /api/ai/compare-reports` — Request side-by-side longitudinal report comparison data.

### 4. Health Analytics & Visualizations Endpoints
- `GET /api/analytics/trend/{parameter_name}` — Time-series linear regression trend for a lab parameter.
- `GET /api/analytics/comparison` — Compare two reports via query parameters `old_id` and `new_id`.
- `GET /api/analytics/health-summary` — HTML summary of health metrics.
- `GET /api/analytics/correlation` — Rendered correlation heatmap image response.
- `GET /api/analytics/health-summary-json` — JSON health metrics and flagged parameters.
- `GET /api/analytics/correlation-json` — Pearson correlation matrix in JSON format.
- `GET /api/dashboard` — Unified dashboard metrics endpoint.
- `GET /api/export/csv` — Export all lab values and report data to downloadable CSV.

### 5. Doctor Discovery & Access Control Endpoints
- `GET /api/doctors` — Search doctors by specialty, category, or experience.
- `GET /api/categories` / `GET /api/specialties` — Fetch doctor specialties and taxonomy.
- `POST /api/specialties` — Create a new doctor specialty.
- `GET /api/patient/discovery-stats` — Statistics on available doctors and categories.
- `GET /api/doctor/assignment-stats` — Doctor statistics on active patients and pending requests.
- `POST /api/patient/doctor-access` — Request doctor access.
- `GET /api/patient/doctor-access` — List patient's doctor access requests.
- `GET /api/doctor/patient-access-requests` — List doctor's incoming access requests.
- `POST /api/doctor/patient-access-requests/{request_id}/accept` — Accept patient access request.
- `POST /api/doctor/patient-access-requests/{request_id}/reject` — Reject patient access request.
- `POST /api/patient/doctor-access/{request_id}/revoke` — Revoke doctor access.
- `GET /api/users/patients` — Doctor endpoint to fetch authorized patient list.

### 6. User Profiles, Notes & Medication Endpoints
- `GET /api/patient/profile` / `POST /api/patient/profile` / `PUT /api/patient/profile` — Manage patient biometric profile.
- `GET /api/doctor/profile` / `POST /api/doctor/profile` / `PUT /api/doctor/profile` — Manage doctor professional profile.
- `GET /api/doctor/statistics` — Fetch practice metrics for doctor dashboard.
- `GET /api/doctor/patient/{patient_id}` — Inspect approved patient details, reports, and history.
- `GET /api/medicines` / `POST /api/medicines` / `PUT /api/medicines/{id}` / `DELETE /api/medicines/{id}` — Medication regimen management.
- `GET /api/doctor-notes` / `POST /api/doctor-notes` — Clinical doctor consultation notes management.

---

## 🎨 Frontend Component & Page Inventory

### Pages (`frontend/src/pages/`)
1. **`Login.jsx`**: User authentication view with JWT handling.
2. **`Register.jsx`**: Role-based registration for Patients and Doctors with taxonomy selectors.
3. **`PatientDashboard.jsx`**: Main patient landing hub with quick stats, recent reports, flagged values, and trends.
4. **`DoctorDashboard.jsx`**: Practice dashboard showing connected patients, pending access requests, and quick stats.
5. **`DoctorInterface.jsx`**: Detailed doctor inspection page for authorized patient records, report comparisons, and doctor notes.
6. **`Reports.jsx`**: Report library with file drag-and-drop upload interface (`react-dropzone`).
7. **`ReportViewer.jsx`**: In-depth report viewer displaying extracted lab value table, OCR status, AI summary, and document download link.
8. **`HealthSummaryPage.jsx`**: Dedicated health summary analytics view with parameter status breakdown.
9. **`CorrelationPage.jsx`**: Interactive lab parameter correlation matrix heatmap.
10. **`MedicalDashboard.jsx`**: Multi-parameter health overview dashboard.
11. **`Medicines.jsx`**: Medication tracking manager with current/past tabs and prescription details.
12. **`FindDoctors.jsx`**: Doctor discovery directory with category/specialty filters and access request buttons.
13. **`PatientProfile.jsx`**: Patient biometric profile editor (age, height, weight, BMI, blood group, allergies).
14. **`DoctorProfile.jsx`**: Doctor professional profile editor (degrees, license, experience, clinic details).

### UI Components (`frontend/src/components/`)
1. **`AIAssistantModal.jsx`**: Floating AI Assistant modal featuring grounded citations, tool badges, and suggested follow-ups.
2. **`Layout.jsx`**: Global application shell with responsive navigation header and role-based sidebar links.
3. **`TrendChart.jsx`**: Interactive Recharts time-series chart component for lab parameter values over time.
4. **`ParameterCard.jsx`**: Parameter display card showing latest value, unit, reference range, and status tag.
5. **`InsightsPanel.jsx`**: Notification card rendering AI clinical observations and warnings.
6. **`RiskBadge.jsx`**: Color-coded risk status badges (`Normal`, `Moderate Risk`, `High Risk`).
7. **`FormComponents.jsx`**: Standardized text inputs, select dropdowns, and button controls.
8. **`EnhancedCards.jsx`**: Glassmorphic summary cards with numerical statistics and icons.
9. **`Skeletons.jsx`**: Animated content skeleton loaders for asynchronous API calls.
10. **`Toast.jsx`**: Application-wide toast alert provider.
11. **`RoleRoute.jsx`**: Route protection wrapper enforcing `patient` or `doctor` role access.

---

## ⚙️ Setup & Installation Guide

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** v18.0 or higher (with npm)
- **Tesseract OCR:** Installed on system (optional but recommended for image OCR)
- **Poppler Utilities / PyMuPDF:** PDF text extraction (PyMuPDF `fitz` is installed via PyPI as zero-dependency fallback)

#### Installing OCR System Dependencies
- **Windows:**
  - Tesseract OCR: Download installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) or install via Chocolatey: `choco install tesseract`
  - Poppler (Optional): Download binary release from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) and extract to `C:/poppler/Library/bin`.
- **macOS:** `brew install python node tesseract poppler`
- **Linux (Ubuntu/Debian):** `sudo apt-get install python3 python3-venv nodejs npm tesseract-ocr poppler-utils`

---

### Step 1: Clone Repository & Configure Backend

```bash
cd medical-report-analyzer/backend
```

Create a Python virtual environment and activate it:
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables

Create or edit `backend/.env`:

```ini
# Database Configuration (SQLite default; PyMySQL optional)
DB_USER=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=medical_report_analysis

# Security & JWT Token Config
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# External Binaries (Adjust path for Windows Poppler installation)
POPPLER_PATH=C:/poppler/Library/bin

# Active LLM Provider: "ollama" (Local) or "groq" (Cloud API)
LLM_PROVIDER=ollama

# Ollama Settings (When LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:3b

# Groq Settings (When LLM_PROVIDER=groq)
GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-8b-instant

# AI Generation Parameters
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=1024
AI_TIMEOUT_SECONDS=30
```

---

### Step 3: Set Up Ollama Local LLM (Optional for Offline Execution)

If `LLM_PROVIDER=ollama`:
1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Pull your model:
   ```bash
   ollama pull qwen2.5:3b
   ```
3. Start Ollama service (`http://localhost:11434`).

---

### Step 4: Run Backend Development Server

Start the FastAPI server:
```bash
python main.py
```
*The FastAPI backend will start at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.*

---

### Step 5: Configure & Run Frontend Application

Open a new terminal window:

```bash
cd medical-report-analyzer/frontend
npm install
npm run dev
```
*The React frontend dev server will launch at `http://localhost:5173` (or `http://localhost:3000`).*

---

## 🧪 Testing & Quality Assurance

The backend contains a test suite in `backend/tests/` using `pytest`.

Run all tests from `backend/`:

```bash
cd backend
pytest tests/ -v
```

### Key Test Files:
- `test_agent_security_and_tools.py`: Tests MCP tool registration, execution logic, and security scoping.
- `test_ai_security.py`: Tests role-based access control and unauthorized doctor query blocking.
- `test_ollama_langgraph.py`: Verifies LangGraph agent initialization and execution nodes.
- `test_suggested_questions.py`: Tests follow-up query suggestion generation logic.

---

## 🚀 Limitations & Future Roadmap

### Current System Boundaries
- **Local SQLite default:** SQLite database enabled by default for rapid local deployment; PyMySQL supported for MySQL production instances.
- **English Language OCR:** Extraction rules optimized primarily for English medical lab reports.

### Future Roadmap
- [ ] **HIPAA Audit Logging:** Cryptographic append-only log tracking every patient record viewing event.
- [ ] **DICOM Radiological Imaging:** Built-in viewer for X-ray, CT, and MRI scans.
- [ ] **Multi-Language OCR Support:** Support for international lab report formats and languages.
- [ ] **HL7 FHIR Interoperability:** Native import and export of FHIR clinical resources.
