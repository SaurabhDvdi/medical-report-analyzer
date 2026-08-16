# 🏥 Medical Report Analyzer & AI Clinical Intelligence Platform

> An enterprise-grade, full-stack medical intelligence platform combining automated OCR document ingestion, longitudinal lab analytics, role-based doctor-patient collaboration, and a **LangGraph-orchestrated AI Clinical Assistant** powered by **Model Context Protocol (MCP)** tools and hybrid LLM support (Ollama & Groq).

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Key Capabilities & Features](#-key-capabilities--features)
3. [System Architecture](#-system-architecture)
4. [Tech Stack](#-tech-stack)
5. [Project Structure](#-project-structure)
6. [Data Architecture & Database Models](#-data-architecture--database-models)
7. [AI Agent & MCP Architecture](#-ai-agent--mcp-architecture)
8. [Security & Access Control Matrix](#-security--access-control-matrix)
9. [API Reference](#-api-reference)
10. [Setup & Installation Guide](#-setup--installation-guide)
11. [Environment Configuration (`.env`)](#-environment-configuration-env)
12. [Testing & Quality Assurance](#-testing--quality-assurance)
13. [Limitations & Future Roadmap](#-limitations--future-roadmap)

---

## 🎯 Project Overview

Modern medical care is often fragmented. Patients receive diagnostic laboratory reports in physical or unstructured PDF formats, making it difficult to detect long-term health trends or abnormal lab value shifts over time. Healthcare providers also face challenges when retrieving grounded patient histories, analyzing multi-report deltas, and providing clinical decision support.

The **Medical Report Analyzer** bridges this gap by transforming static, unstructured medical documents into structured, actionable intelligence:

- **For Patients:** Upload medical reports (PDF/images), track lab parameters over time with interactive time-series charts, manage current/past medication regimens, assess overall health risks, find specialized doctors, and interact with an AI Assistant grounded in their own personal medical data.
- **For Healthcare Providers (Doctors):** Request and manage patient access, view structured medical timelines, compare historical reports side-by-side with calculated percentage deltas, review AI summaries, add clinical consultation notes, and utilize an AI Assistant scoped to approved patient records.

---

## 🔥 Key Capabilities & Features

### 🧠 1. LangGraph AI Clinical Assistant
- **Intent Recognition & State Orchestration:** Utilizes a custom LangGraph `StateGraph` to evaluate user intent (patient history retrieval, health summary, lab trend analysis, report comparison, health risk scoring, drug interaction check, doctor discovery, or medical guidelines).
- **Hybrid Multi-LLM Backend:** Supports offline local execution via **Ollama** (e.g., `qwen2.5:3b`, `llama3`) and cloud execution via **Groq Cloud API** (`llama-3.1-8b-instant`).
- **Grounding & Transparency:** All AI responses include inline source citations (`[Patient Profile]`, `[Lab Parameter: HbA1c]`, `[Medical Glossary]`), list of tools executed, and context-aware follow-up question suggestions.

### 🔌 2. Model Context Protocol (MCP) Tool Suite
- **18+ Security-Scoped Tools:** Standardized MCP tool registry enforcing strict role boundaries (`SecurityContext`):
  - `get_patient_history`, `get_health_summary`, `get_lab_trend`, `compare_reports`, `calculate_health_risk`
  - `search_medical_guidelines`, `check_drug_interactions`
  - `search_doctors`, `get_doctor_profile`, `get_doctor_specialties`
  - `get_my_patients`, `search_my_patients`, `resolve_my_patient`, `get_my_patient_count`
  - `get_my_doctors`, `get_my_reports`, `get_my_medicines`, `get_website_help`

### 📄 3. Document Processing Pipeline (OCR & NLP)
- **Multi-Engine OCR:** Automatic text extraction from PDF and image files using PyTesseract and EasyOCR with Poppler fallback.
- **Structured Lab Extraction:** Automated normalization of lab parameters, units, reference ranges, and abnormal value flag assignment (`is_abnormal`).
- **NLP Summarization:** Hugging Face Transformers (`facebook/bart-large-cnn`, `t5-small`) or LLM integration to generate clinical summaries of extracted text.

### 📈 4. Advanced Health Analytics & Report Comparison
- **Linear Regression Trends:** Time-series tracking of lab parameter trajectory over multiple report dates.
- **Pearson Correlation Heatmaps:** Multi-parameter correlation matrices highlighting relationships between blood values.
- **Side-by-Side Longitudinal Comparison:** Deterministic report comparison calculating absolute values, parameter deltas, percentage changes, and status shifts (e.g., `Normal` ➔ `Elevated`).

### 👨‍⚕️ 5. Consent-Driven Doctor-Patient Access System
- **Taxonomy & Discovery:** Doctor categorization by clinical specialty (`DoctorCategory`, `DoctorSpecialty`) with custom specialty creation on registration.
- **Patient Sovereignty:** Access must be explicitly requested by patients or requested by doctors and approved by patients. Access can be granted or revoked at any time.

---

## 🏗️ System Architecture

```text
                                  +---------------------------------------+
                                  |         React 18 Frontend             |
                                  |  (Vite + TailwindCSS + Recharts)       |
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
                           |  (OCR, Analytics, DB)  |  |   (LangGraph Engine)   |
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
                           |  (MySQL / SQLite)      |  | Analytics Services     |  | (Ollama / Groq Cloud)  |
                           +------------------------+  +------------------------+  +------------------------+
```

---

## 💻 Tech Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn | High-performance asynchronous REST backend |
| **Database & ORM** | SQLAlchemy, SQLite / PyMySQL | Relational database mapping and persistence |
| **Authentication** | JWT (`python-jose`), `bcrypt` | Role-based authorization & password security |
| **AI Orchestration** | LangGraph, LangChain Core / Community | State graph workflow & agent orchestration |
| **Tool Architecture** | Model Context Protocol (MCP) | Standardized, security-scoped tool execution |
| **LLM Inference** | Ollama (`langchain-ollama`), Groq (`langchain-openai`) | Local offline or cloud LLM reasoning |
| **OCR & Parsing** | PyTesseract, EasyOCR, `pdf2image`, Pillow | Text extraction from medical PDFs and images |
| **NLP & ML** | Hugging Face Transformers, Pandas, SciPy | Document summarization & time-series regression |
| **Frontend** | React 18, Vite, TailwindCSS, Lucide Icons | Responsive UI with rich interactive components |
| **Data Viz** | Recharts, Chart.js, Seaborn, Matplotlib | Time-series charts & correlation heatmaps |

---

## 📁 Project Structure

```text
medical-report-analyzer/
├── README.md                      # Primary project documentation
├── QUICKSTART.md                  # Concise quickstart guide
├── package.json                   # Root package definition
│
├── backend/                       # Python FastAPI Backend Architecture
│   ├── main.py                    # Application entrypoint & REST API endpoints
│   ├── database.py                # Database connection & session lifecycle
│   ├── models.py                  # SQLAlchemy ORM database models
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── auth.py                    # JWT token creation & authentication dependency
│   ├── logging_config.py          # Centralized rotating logger setup
│   ├── .env                       # Environment configuration (LLM, DB, Poppler)
│   ├── requirements.txt           # Python dependencies manifest
│   │
│   ├── ai/                        # AI Assistant & LangGraph Subsystem
│   │   ├── agent.py               # LangGraph ClinicalAssistantAgent & graph construction
│   │   ├── llm_service.py         # LLM provider wrapper (Ollama & Groq integration)
│   │   ├── rag_service.py         # Patient context retrieval & medical glossary RAG
│   │   ├── suggestion_service.py  # Follow-up question suggestion generator
│   │   └── config.py              # AI configuration parameters
│   │
│   ├── mcp/                       # Model Context Protocol Layer
│   │   ├── tools.py               # MCPToolRegistry & SecurityContext implementation
│   │   └── client.py              # MCPClient wrapper mapping tool invocations
│   │
│   ├── routes/                    # API Router Modules
│   │   ├── ai_routes.py           # /api/ai/chat and /api/ai/compare-reports endpoints
│   │   ├── dashboard.py           # Dashboard data endpoints
│   │   ├── upload.py              # Report file upload endpoints
│   │   └── analytics.py           # Advanced analytics endpoints
│   │
│   ├── services/                  # Business Logic & Analytics Services
│   │   ├── ocr_service.py         # Multi-engine OCR text extraction
│   │   ├── nlp_service.py         # Medical document summarization
│   │   ├── report_parser.py       # Regex & pattern report parser
│   │   ├── normalizer.py          # Unit & range normalization
│   │   ├── extractor.py           # Lab value extraction logic
│   │   ├── analytics_service.py   # Trend analysis & correlation matrix generation
│   │   ├── comparison_service.py  # Report comparison & delta calculation engine
│   │   ├── risk_engine.py         # Health risk evaluation engine
│   │   ├── insights.py            # Clinical insights generation engine
│   │   └── doctor_taxonomy_seed.py# Specialty taxonomy database seeder
│   │
│   └── tests/                     # Automated Test Suite
│       ├── test_agent_security_and_tools.py
│       ├── test_ai_security.py
│       ├── test_ollama_langgraph.py
│       └── test_suggested_questions.py
│
└── frontend/                      # React 18 Frontend Architecture
    ├── index.html                 # Main HTML entrypoint
    ├── vite.config.js             # Vite development server configuration
    ├── tailwind.config.js         # Tailwind CSS theme configuration
    ├── package.json               # Frontend dependencies
    │
    └── src/
        ├── App.jsx                # Application router & layout controller
        ├── pages/                 # Full-Page React Components
        │   ├── PatientDashboard.jsx   # Patient overview dashboard
        │   ├── DoctorDashboard.jsx    # Doctor overview dashboard
        │   ├── DoctorInterface.jsx    # Doctor patient inspection view
        │   ├── Reports.jsx            # All reports list & upload interface
        │   ├── ReportViewer.jsx       # Single report viewer & parameter breakdown
        │   ├── HealthSummaryPage.jsx  # Health metrics & parameter status
        │   ├── CorrelationPage.jsx    # Parameter correlation heatmap
        │   ├── Medicines.jsx          # Current & past medicine tracker
        │   ├── FindDoctors.jsx        # Doctor discovery & access request
        │   ├── PatientProfile.jsx     # Patient medical profile editor
        │   └── DoctorProfile.jsx      # Doctor professional profile editor
        │
        └── components/            # Reusable UI Components
            ├── AIAssistantModal.jsx   # Floating AI Assistant modal with suggested queries
            ├── TrendChart.jsx         # Time-series parameter charts
            ├── InsightsPanel.jsx      # AI insight notification card
            ├── RiskBadge.jsx          # Color-coded risk status badges
            └── Layout.jsx             # Navigation header & sidebar wrapper
```

---

## 🗄️ Data Architecture & Database Models

The relational database model (SQLAlchemy ORM) enforces high integrity across user roles, medical records, and access permissions:

| Table | Model Class | Key Fields & Relationships |
| :--- | :--- | :--- |
| `users` | `User` | `id`, `email`, `password_hash`, `full_name`, `role` (`patient`/`doctor`), `doctor_category_id`, `doctor_specialty_id`. Relationships: `reports`, `medicines`, `doctor_profile`, `patient_profile`. |
| `patient_profiles` | `PatientProfile` | `user_id`, `age`, `gender`, `height_cm`, `weight_kg`, `bmi`, `blood_group`, `allergies`, `chronic_conditions`, `emergency_contact`. |
| `doctor_profiles` | `DoctorProfile` | `user_id`, `degrees`, `specialization`, `experience_years`, `license_number`, `clinic_name`, `clinic_address`, `clinic_phone`. |
| `doctor_categories`| `DoctorCategory` | `id`, `name`, `description`. Organizes doctor specialties into broader clinical areas (e.g., Cardiology, Endocrinology). |
| `doctor_specialties` | `DoctorSpecialty` | `id`, `category_id`, `name`, `description`. Specific medical sub-specialty. |
| `patient_doctor_access` | `PatientDoctorAccess` | `patient_id`, `doctor_id`, `status` (`pending`, `approved`/`accepted`, `rejected`, `revoked`). Enforces doctor-patient data sharing boundaries. |
| `report_categories`| `ReportCategory` | `id`, `name`, `description`. Report types (e.g., Blood Test, Lipid Profile, Thyroid Panel). |
| `reports` | `Report` | `id`, `user_id`, `file_name`, `file_path`, `ocr_status`, `extracted_text`, `ai_summary`, `report_date`. |
| `lab_values` | `LabValue` | `id`, `report_id`, `parameter_name`, `value`, `unit`, `reference_range`, `is_abnormal`. |
| `medicines` | `Medicine` | `id`, `user_id`, `name`, `dosage`, `frequency`, `start_date`, `end_date`, `status` (`current`/`past`). |
| `doctor_notes` | `DoctorNote` | `id`, `doctor_id`, `patient_id`, `report_id`, `note_text`, `note_type` (`consultation`, `examination`, `followup`). |

---

## 🤖 AI Agent & MCP Architecture

### LangGraph Workflow Execution
When a query is dispatched to `/api/ai/chat`, the `ClinicalAssistantAgent` initializes an `AgentState` object and executes the state graph:

```text
[Input Query] ➔ [Security Scoping] ➔ [Intent Classification Node] ➔ [MCP Tool Resolution] ➔ [LLM Generation Node] ➔ [Response + Sources + Follow-up Questions]
```

1. **Security Context Creation:** Resolves the requesting user's identity and checks whether doctor access to the target patient is approved.
2. **Intent Classification:** Determines if the query requires specific tools (e.g., `lab_trend`, `compare_reports`, `patient_history`, `check_drug_interactions`).
3. **MCP Tool Execution:** Executes tools via `MCPToolRegistry` with target patient filters strictly bound to authorized IDs.
4. **Context Assembly & Grounding:** Combines retrieved database context, medical glossary entries, and tool results into the prompt context.
5. **Response & Suggestions:** Formats the final clinical answer with structured citations and automatically generates 3 contextual follow-up questions.

---

## 🔒 Security & Access Control Matrix

Data access is guarded by backend middleware (`auth.py`) and authorization dependencies (`check_doctor_access`):

| Requester Role | Target Data Owner | Access Granted? | Validation Rule |
| :--- | :--- | :---: | :--- |
| **Patient** | Self | ✅ Granted | Always allowed to query personal reports, history, and medicines. |
| **Patient** | Other Patient | ❌ Denied | Patient ID in query payload is overridden with the user's own ID. |
| **Doctor** | Approved Patient | ✅ Granted | Access allowed if `PatientDoctorAccess` record has status `approved` or `accepted`. |
| **Doctor** | Unapproved Patient | ❌ Denied | Throws `403 Forbidden` error immediately. |
| **Unauthenticated**| Any | ❌ Denied | Throws `401 Unauthorized` token error. |

---

## 🔌 API Reference

### 1. Authentication Endpoints
- `POST /api/auth/register` — Register new user (Patient or Doctor with taxonomy selection).
- `POST /api/auth/login` — Authenticate and obtain JWT access token.

### 2. AI Clinical Assistant Endpoints
- `POST /api/ai/chat` — Submit query to AI Agent (supports patient ID targeting, report comparison parameters).
- `POST /api/ai/compare-reports` — Request side-by-side longitudinal report comparison data.

### 3. Report & File Endpoints
- `POST /api/upload` — Upload medical report PDF or image file (triggers asynchronous OCR).
- `GET /api/reports` — Fetch all reports for the authenticated patient or requested patient.
- `GET /api/reports/{id}` — Fetch details, extracted lab values, and summary of a specific report.

### 4. Doctor Discovery & Access System Endpoints
- `GET /api/doctors` — Search doctors by specialty, category, or experience.
- `GET /api/doctors/categories` — List available clinical categories and sub-specialties.
- `POST /api/access/request` — Patient requests access to a doctor.
- `POST /api/access/approve` — Patient approves a doctor's access request.
- `POST /api/access/revoke` — Patient revokes access from a doctor.
- `GET /api/access/my-patients` — Doctor fetches list of authorized active care patients.

### 5. Health Analytics & Dashboard Endpoints
- `GET /api/dashboard/patient` — Get summary metrics (total reports, flagged parameters, recent values).
- `GET /api/dashboard/doctor` — Get doctor overview dashboard (active patient list, recent activity).
- `GET /api/analytics/trends` — Fetch time-series values and linear regression data for a parameter.
- `GET /api/analytics/correlations` — Fetch parameter correlation heatmap matrix.

### 6. Profile & Medicine Endpoints
- `GET /api/profile/patient` / `POST /api/profile/patient` — Manage patient medical profile.
- `GET /api/profile/doctor` / `POST /api/profile/doctor` — Manage doctor professional profile.
- `GET /api/medicines` / `POST /api/medicines` — Manage active and past medications.

---

## ⚙️ Setup & Installation Guide

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** v18.0 or higher
- **Tesseract OCR:** Installed on system (and added to system PATH)
- **Poppler Utilities:** Required for PDF to image conversion (`pdf2image`)

#### Installing System Dependencies
- **Windows:**
  - Tesseract OCR: Download installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) or install via Chocolatey: `choco install tesseract`
  - Poppler: Download binary release from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) and extract to `C:/poppler/Library/bin`.
- **macOS:** `brew install python node tesseract poppler`
- **Linux (Ubuntu/Debian):** `sudo apt-get install python3 python3-venv nodejs npm tesseract-ocr poppler-utils`

---

### Step 1: Clone Repository & Configure Backend

```bash
cd medical-report-analyzer/backend
```

Create a virtual environment and activate it:
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

# Security
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

# AI Generation Control
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=1024
AI_TIMEOUT_SECONDS=30
```

---

### Step 3: Set Up Ollama Local LLM (Optional for Offline Inference)

If using `LLM_PROVIDER=ollama`:
1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull your desired model:
   ```bash
   ollama pull qwen2.5:3b
   ```
3. Verify Ollama is running at `http://localhost:11434`.

---

### Step 4: Run Backend Server

Start the FastAPI development server:
```bash
python main.py
```
*The backend API will be live at `http://localhost:8000`. Interactive OpenAPI documentation will be accessible at `http://localhost:8000/docs`.*

---

### Step 5: Configure & Run Frontend

Open a new terminal window:

```bash
cd medical-report-analyzer/frontend
npm install
npm run dev
```
*The React frontend dev server will launch at `http://localhost:5173` (or `http://localhost:3000`).*

---

## 🧪 Testing & Quality Assurance

The backend repository includes an extensive test suite verifying AI agent execution, MCP tool boundaries, role-based security, and fallback behaviors.

Run all tests from the `backend/` directory:

```bash
cd backend
pytest tests/ -v
```

### Key Test Suites:
- `test_agent_security_and_tools.py`: Tests MCP tool registration, execution, and security scoping.
- `test_ai_security.py`: Tests role-based access control and unauthorized doctor query rejection.
- `test_ollama_langgraph.py`: Verifies LangGraph agent initialization and execution nodes.
- `test_suggested_questions.py`: Tests automatic follow-up query recommendation logic.

---

## 🚀 Limitations & Future Roadmap

### Current System Boundaries
- **Local SQLite/MySQL default:** Configured for development and single-server deployments.
- **Language Support:** Primary OCR patterns optimized for English-language medical laboratory reports.

### Future Roadmap
- [ ] **HIPAA-Compliant Audit Logging:** Append-only cryptographic audit logs for every patient record access.
- [ ] **DICOM & Radiological Image Viewing:** Integration of DICOM image previewers for X-ray and MRI scan reports.
- [ ] **Multi-Language OCR & Parsing:** Multilingual extraction support for global medical lab standards.
- [ ] **HL7 / FHIR Interoperability:** Native export and import of healthcare records adhering to HL7 FHIR standards.
