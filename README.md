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

### 🔔 8. Doctor-Side Notification System for Access Requests
- **Real-Time Notification Bell & Badge:** Header notification bell displaying dynamic unread count (`Dashboard 🔔 ② API Connected`). Unread badge automatically hides when count is zero.
- **Access Request Popover Panel:** Responsive dropdown presenting patient name, patient age, request description, and relative timestamp.
- **Transactional Decision Controls:** Doctor can `[Accept]` or `[Reject]` requests directly from the panel with loading states preventing double-submission.
- **Privacy & Minimum Disclosure Invariant:** Notifications strictly convey access requests without exposing sensitive medical reports, lab values, or medications.
- **IDOR Protection & Authoritative Scoping:** Strict JWT-bound identity validation preventing cross-doctor data access or status manipulation (HTTP 403).
- **Background Polling & Cache Invalidation:** Automated 15-second React Query background refetching paired with instant cache synchronization across dashboards.

### 💬 9. Context-Aware AI Assistant & Multi-Role Clear Chat
- **Automatic Patient Scoping:** Authenticated patients have their medical context automatically bounded to their own profile without needing manual ID entry.
- **Doctor Active Patient Context:** Healthcare providers select an active patient context (`active_patient_id`) validated through approved `PatientDoctorAccess` relationships.
- **Prompt Injection Defense:** Strict authorization barriers prevent adversarial user prompts from crossing patient isolation boundaries or accessing unauthorized patient files.
- **Non-Destructive Clear Conversation:** Patients and doctors can clear active AI conversation history on demand without modifying or deleting any underlying medical reports, lab values, or clinical notes.

---

## 🏗️ System Architecture

```text
User
  ↓
Authentication / JWT (Role: Patient / Doctor)
  ↓
SecurityContext (Enforces RBAC & Patient-Doctor Access)
  ↓
Jev System-1 Triage (~80ms Multi-Head Intent & Safety Gate)
  ↓
Emergency & Medication Safety Gates (Zero-LLM Emergency Short-Circuit in <1ms)
  ↓
Three-Tier Routing Architecture
  │
  ├── High Confidence (≥0.70)
  │       ↓
  │     MCP Direct Fast-Path (Single LLM synthesis call)
  │
  ├── Medium Confidence (0.40–0.69)
  │       ↓
  │     LangGraph Agent Workflow (Multi-turn tool resolution)
  │
  └── Low Confidence (<0.40 / Ambiguous)
          ↓
        Safe Clarification / Conversational Education
  ↓
ContextSanitizer (Strips internal DB/ORM IDs; bounds synthesis context to ~350 tokens)
  ↓
qwen2.5:1.5b (Primary local model, CPU 8 threads)
      ↓ (failure / timeout failover - max 2 attempts bounded)
qwen2.5:3b (Fallback local model)
  ↓
ResponseValidator (Scrubs leaked IDs, secrets, prompt echoes; neutralizes dosage/diagnosis claims)
  ↓
FastAPI SSE Streaming Endpoint (/api/ai/chat/stream)
  ↓
React 18 Modal UI (AIAssistantModal with progressive token rendering)
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
│   │   ├── ai_routes.py           # /api/ai/chat, /api/ai/chat/stream, /api/ai/chat/clear
│   │   ├── dashboard.py           # /api/dashboard data endpoints
│   │   ├── doctor.py              # /api/doctor profile, access requests & notifications
│   │   └── patient.py             # /api/patient profile, doctor access requests & discovery
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
│   └── tests/                     # Automated Test Suite (182 tests, 100% pass)
│       ├── test_doctor_notifications.py    # Doctor notification bell, IDOR & access lifecycle tests
│       ├── test_context_aware_ai_and_clear_chat.py # Context-aware AI & multi-user clear chat tests
│       ├── test_agent_security_and_tools.py # MCP tools & security context tests
│       ├── test_ai_security.py             # Unauthorized doctor access tests
│       ├── test_ollama_langgraph.py        # LangGraph execution & node tests
│       ├── test_suggested_questions.py     # Follow-up question generator tests
│       ├── test_three_tier_and_streaming.py# Jev triage & SSE streaming tests
│       ├── test_deployment_hardening.py    # Hardening, rate limiting & leak defense tests
│       ├── test_cbc_coordinate_and_normalization.py # CBC coordinate extraction tests
│       ├── test_medical_classifier_and_rejection.py # Document classifier & rejection tests
│       └── test_pre_deployment_audit.py    # Pre-deployment health & configuration audit
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
        └── components/            # Reusable UI Components (12 Components)
            ├── DoctorNotificationBell.jsx # Doctor header bell, dynamic badge & request popover
            ├── AIAssistantModal.jsx # Floating AI Assistant chat modal with citations & clear chat
            ├── Layout.jsx         # Sidebar navigation, header container & notification bell
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

The database schema (SQLAlchemy ORM) defines 12 interlinked tables enforcing strict data integrity:

| Table Name | Model Class | Key Fields & Relationships |
| :--- | :--- | :--- |
| `users` | `User` | `id`, `email`, `password_hash`, `full_name`, `role` (`patient`/`doctor`), `doctor_category_id`, `doctor_specialty_id`, `created_at`. Relates to: `reports`, `medicines`, `doctor_profile`, `patient_profile`. |
| `patient_profiles` | `PatientProfile` | `user_id`, `age`, `gender`, `height_cm`, `weight_kg`, `bmi`, `blood_group`, `allergies`, `chronic_conditions`, `emergency_contact`. |
| `doctor_profiles` | `DoctorProfile` | `user_id`, `degrees`, `specialization`, `experience_years`, `license_number`, `clinic_name`, `clinic_address`, `clinic_phone`, `clinic_email`, `bio`. |
| `doctor_categories`| `DoctorCategory` | `id`, `name`, `description`. Categorizes doctor specialties (e.g., General Medicine, Cardiology, Endocrinology). |
| `doctor_specialties` | `DoctorSpecialty` | `id`, `category_id`, `name`, `description`. Specific medical sub-specialty. |
| `patient_doctor_access` | `PatientDoctorAccess` | `patient_id`, `doctor_id`, `status` (`pending`, `approved`/`accepted`, `rejected`, `revoked`), `requested_by`, `granted_at`, `revoked_at`, `created_at`, `updated_at`. |
| `notifications` | `Notification` | `id`, `recipient_doctor_id`, `patient_id`, `access_request_id`, `notification_type` (`PATIENT_ACCESS_REQUEST`), `title`, `message`, `is_read`, `created_at`, `resolved_at`. Relates to: `doctor` (`User`), `patient` (`User`), `access_request` (`PatientDoctorAccess`). |
| `report_categories`| `ReportCategory` | `id`, `name`, `description`. Report types (e.g., Blood Test, Lipid Profile, Thyroid Panel). |
| `reports` | `Report` | `id`, `user_id`, `category_id`, `file_name`, `file_path`, `ocr_status`, `extracted_text`, `ai_summary`, `report_date`, `upload_date`. |
| `lab_values` | `LabValue` | `id`, `report_id`, `parameter_name`, `value`, `unit`, `reference_range`, `is_abnormal`. |
| `medicines` | `Medicine` | `id`, `user_id`, `name`, `dosage`, `frequency`, `start_date`, `end_date`, `status` (`current`/`past`), `notes`. |
| `doctor_notes` | `DoctorNote` | `id`, `doctor_id`, `patient_id`, `report_id`, `note_text`, `note_type` (`consultation`, `examination`, `followup`), `created_at`. |

---

## 🤖 AI Agent, Jev Routing & Inference Architecture

### Pipeline Workflow Execution
When a user query is sent to `/api/ai/chat` or `/api/ai/chat/stream`, the platform executes a deterministic-first, bounded-inference architecture:

```text
User Query ➔ SecurityContext (JWT/RBAC) ➔ Jev System-1 Multi-Head Triage ➔ Safety Gates ➔ Three-Tier Routing ➔ ContextSanitizer ➔ Bounded LLM Failover ➔ ResponseValidator ➔ SSE Streaming
```

1. **Security Context Scoping:** Resolves requesting user credentials from verified JWT (`SecurityContext`). Enforces RBAC: patients can never query other patients' IDs; doctors can only query authorized patients with active approved consent.
2. **Jev System-1 Multi-Head Triage:** Evaluates query intent, direct tool recommendation, tool confidence, acute emergency probability, and medication alteration flags in a single atomic classification pass.
   - *Remote Cloud Jev API Latency:* ~80–290 ms (HTTPS round-trip to remote TypeSafe System-1 inference service; p50 ≈ 257 ms, p95 ≈ 290 ms).
   - *Local In-Process Triage Latency:* ~0.03–0.12 ms (instantaneous deterministic regex and in-memory rule-based triage fallback).
3. **Emergency Short-Circuit Safety Net (0 LLM Calls, <1ms):** If acute emergency symptoms are detected (crushing chest pain, severe dyspnea, stroke signs), the system immediately returns a calibrated, calm emergency notice with 0 normal LLM calls.
4. **Medication Safety Gate:** Detects requests to alter, start, stop, double, or replace prescriptions, prepending a mandatory clinical prescription notice and preventing the LLM from issuing individualized dosage instructions.
5. **Three-Tier Routing Architecture:**
   - **EMERGENCY (Safety Short-Circuit):** Deterministic zero-LLM short-circuit (<1ms) directing users to urgent care contacts.
   - **HIGH Tier (Confidence ≥ 0.70):** Direct authorized MCP fast-path. Executes verified MCP tool via `SecurityContext` followed by a single grounded synthesis LLM call (reduces fast-path latency from 52s down to ~9–14s).
   - **MEDIUM Tier (Confidence 0.40–0.69):** Agent/tool reasoning via LangGraph `StateGraph` workflow for multi-turn tool discovery, patient disambiguation, and comparative reasoning.
   - **LOW Tier (Confidence < 0.40 / Conversational / Ambiguous):** Defined strictly as **"no privileged tool execution"** (zero privileged database/patient tools are executed):
     - *Conversational / General Medical Queries:* Routes to informational LLM path with strict Clinical Safety Rules (no medical diagnosis, no medication changes, general educational guidance only).
     - *Ambiguous Queries Without Context:* Intercepts vague queries ("what about that?") with deterministic 0-LLM safe clarification prompts.
6. **ContextSanitizer:** Recursively strips internal primary keys, ORM metadata, timestamps, and internal system IDs (`user_id`, `patient_id`, `doctor_id`, `report_id`, `file_path`) while strictly preserving clinical biomarkers, values, reference ranges, units, and flags. Bounds synthesis prompt context to ~350 tokens.
7. **Bounded Model Failover (Max 2 Attempts, Zero Loops):**
   - **Primary Model:** `qwen2.5:1.5b` (Q4_K_M, 8 CPU threads, max 160 tokens).
   - **Fallback Model:** `qwen2.5:3b` (activated on primary timeout, Ollama failure, or invalid response).
   - **Loop Protection:** Strictly bounded to 2 inference attempts maximum (`primary -> fallback -> STOP`). If both models fail, the system activates a deterministic fallback response without crashing or fabricating medical data.
8. **ResponseValidator (Post-Generation Secondary Net):** Validates UTF-8 encoding, ensures non-empty response, scrubs leaked internal IDs or secrets, strips prompt echoes, neutralizes individualized medication change commands, and distinguishes abnormal findings from definitive diagnoses without rewriting already-safe statements.
9. **FastAPI SSE Streaming & React Progressive UX:** Tokens stream progressively over Server-Sent Events (`/api/ai/chat/stream`) with keep-alive headers. Emergency notices render immediately without waiting for generation. Technical tool names are visible only to healthcare providers for auditability.

---

### 💻 Tested Hardware Class & Local Execution Profile

The local inference benchmarks and production configurations were measured on the following hardware class:
- **Processor:** AMD Ryzen 5 3500U (4 Cores / 8 Threads, base 2.1 GHz, boost up to 3.7 GHz)
- **Host Memory:** ~10 GB Usable DDR4 RAM (~1.19 GB available at test initialization)
- **Graphics / Acceleration:** Integrated AMD Radeon Vega 8 Mobile Graphics (2 GB shared VRAM). **Note:** ROCm is not supported for Vega 8 mobile APUs under Windows Ollama; inference runs **100% on CPU** using 8 threads (`num_thread=8`, `size_vram=0`). GPU acceleration is NOT available on this hardware class.

### 📊 Measured Engineering Benchmark Results

*Note: The following values represent engineering benchmarks on the tested hardware class, not clinical validation studies.*

| Metric | Baseline (LangGraph + qwen2.5:3b) | Jev + qwen2.5:3b | Jev + qwen2.5:1.5b (Current) | Delta vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Fast-Path p50 Latency** | 340.74 s | 18.05–21.20 s | **~12.10–12.61 s** | **−96.3%** |
| **Fast-Path p95 Latency** | ~355.00 s | ~23.50 s | **~14.20 s** | **−96.0%** |
| **Perceived TTFT** | ~28.00 s | ~2.70 s | **~1.13–1.95 s** | **−93.2%** |
| **Generation Throughput** | ~5.8 tok/s | ~7.19 tok/s | **~9.4–10.3 tok/s** | **+77.6%** |
| **Emergency Short-Circuit** | ~340 s (multi-turn LLM) | 0.06 ms (0 LLM calls) | **0.75 ms (0 LLM calls)** | **Instant (<1ms)** |
| **Emergency Recall** | N/A | 100% (30/30) | **100% (30/30)** | **Zero False Negatives** |
| **Medication Safety Recall**| Variable | 100% (8/8) | **100% (8/8)** | **100% Intercept** |
| **Model Memory Footprint** | ~2.3 GB RAM | ~2.3 GB RAM | **~1.3 GB RAM** | **−43.5% RAM** |
| **Regression Tests** | 31/31 passing | 49/49 passing | **52/52 passing (100%)**| **Zero Failures** |

---

### ⚖️ Regulatory & Compliance Notice

> **Important Disclosure on Data Handling:**
> Local inference keeps model processing on the host and avoids sending report content or personal health data to an external inference provider.
> While local inference provides enhanced data-control and host residency characteristics, **it does not automatically grant "HIPAA compliant" or "GDPR compliant" status.** Full regulatory compliance depends on the complete operational system, environment hardening, contractual agreements, access control policies, audit logging, retention rules, and applicable jurisdictional legal review.
>
> The platform is designed strictly as an **informational medical report assistant** and clinical workflow tool. It is **not** a diagnostic device, medical prescribing system, or emergency medical service. Deterministic engines (`LabValidator`, `RiskEngine`) remain authoritative for structured lab data.

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
- `POST /api/ai/chat` — Submit query to AI Assistant (supports automatic patient scoping and doctor `active_patient_id` targeting).
- `POST /api/ai/chat/stream` — SSE streaming endpoint for Progressive Response generation with real-time tokens and keep-alive events.
- `POST /api/ai/chat/clear` — Clear AI conversation history for patient or active doctor patient context without altering clinical records.
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

### 6. Doctor Notification & Access Decision Endpoints
- `GET /api/doctor/notifications` (or `/api/notifications`) — Retrieve notifications for the authenticated doctor (minimal disclosure: patient name, age, and timestamp; zero clinical records).
- `GET /api/doctor/notifications/unread-count` (or `/api/notifications/unread-count`) — Get count of pending access requests and unread notifications scoped to the authenticated doctor.
- `POST /api/doctor/notifications/mark-read` (or `/api/notifications/mark-read`) — Mark all unread notifications as read for authenticated doctor.
- `POST /api/doctor/access-requests/{request_id}/accept` — Accept patient access request, approve access, and resolve notification with IDOR protection.
- `POST /api/doctor/access-requests/{request_id}/reject` — Reject patient access request, mark rejected, and resolve notification with IDOR protection.

### 7. User Profiles, Notes & Medication Endpoints
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
1. **`DoctorNotificationBell.jsx`**: Doctor header notification bell featuring dynamic unread count badge (`Dashboard 🔔 ② API Connected`), responsive dropdown popover, minimal disclosure patient summary (name & age only), and transactional Accept/Reject controls.
2. **`AIAssistantModal.jsx`**: Floating AI Assistant modal featuring automatic patient scoping, doctor active patient context, grounded citations, follow-up suggestions, and non-destructive Clear Conversation.
3. **`Layout.jsx`**: Global application shell with responsive navigation header, doctor notification bell integration, and role-based sidebar links.
4. **`TrendChart.jsx`**: Interactive Recharts time-series chart component for lab parameter values over time.
5. **`ParameterCard.jsx`**: Parameter display card showing latest value, unit, reference range, and status tag.
6. **`InsightsPanel.jsx`**: Notification card rendering AI clinical observations and warnings.
7. **`RiskBadge.jsx`**: Color-coded risk status badges (`Normal`, `Moderate Risk`, `High Risk`).
8. **`FormComponents.jsx`**: Standardized text inputs, select dropdowns, and button controls.
9. **`EnhancedCards.jsx`**: Glassmorphic summary cards with numerical statistics and icons.
10. **`Skeletons.jsx`**: Animated content skeleton loaders for asynchronous API calls.
11. **`Toast.jsx`**: Application-wide toast alert provider.
12. **`RoleRoute.jsx`**: Route protection wrapper enforcing `patient` or `doctor` role access.

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

# Active LLM Provider: "groq" (Production Default), "ollama" (Local Offline), or "gemini" (Cloud)
LLM_PROVIDER=groq

# Production Cloud LLM (Groq API)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
GROQ_BASE_URL=https://api.groq.com
GROQ_FALLBACK_MODEL=openai/gpt-oss-20b

# Ollama Local Offline Settings (Preserved for local development when LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_FALLBACK_MODEL=qwen2.5:3b
OLLAMA_THREADS=8

# Alternate Cloud Providers (Optional)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# AI Generation & Bounded Context Settings
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=160
AI_TIMEOUT_SECONDS=30.0
BOUNDED_CONTEXT_TOKENS=350
MAX_MODEL_ATTEMPTS=2
MAX_CHAT_INPUT_LENGTH=1000
RATE_LIMIT_AI_PER_MINUTE=30

# TypeSafe Jev System-1 Triage
JEV_ENABLED=true
TYPESAFE_API_KEY=your_typesafe_api_key_here
JEV_MODEL=jev-1.13.0
JEV_TOOL_CONFIDENCE_HIGH=0.70
JEV_TOOL_CONFIDENCE_MEDIUM=0.40
```

---

### Step 3: Set Up Ollama Local Models

If `LLM_PROVIDER=ollama`:
1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Pull the primary and fallback models:
   ```bash
   ollama pull qwen2.5:1.5b
   ollama pull qwen2.5:3b
   ```
3. Start the Ollama local daemon (`http://localhost:11434`).

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

## 🐳 Docker Containerization & Multi-Service Compose

The platform is fully containerized across 6 orchestrated services running on an isolated bridge network (`app-network`):

```text
Internet
   │
   ▼
Frontend Nginx (Port 5173) ──► Reverse Proxy /api ──► FastAPI Backend (Port 8000)
                                                             │
                              ┌──────────────────────────────┼──────────────────────────────┐
                              ▼                              ▼                              ▼
                        MySQL 8.0                      Redis 7.0                     Ollama Service
                       (Port 3306)                    (Port 6379)                    (Port 11434)
                              │                              │                              │
                              ▼                              ▼                              │
                        mysql_data              queue:report_processing                     │
                          Volume                             │                              │
                                                             ▼                              │
                                                      Worker Container <────────────────────┘
                                                   (OCR & Clinical NLP)
                                                             │
                                                             ▼
                                                    reports_data Volume
```

### Services Overview

| Service | Container Name | Base Image / Context | Exposed Ports | Persistent Volume | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `frontend` | `medical_frontend` | `./frontend` (`nginx:alpine`) | `5173:80` | N/A | React SPA static asset delivery, SPA client routing fallback, reverse proxy `/api/`, and unbuffered SSE stream handling. |
| `backend` | `medical_backend` | `./backend` (`python:3.11-slim`) | `8000:8000` | `reports_data`, `charts_data` | Modular Monolith API running under `gunicorn` + `uvicorn` workers (UID 1000). Handles auth, RBAC, Jev triage, and report CRUD. |
| `mysql` | `medical_mysql` | `mysql:8.0` | `3306:3306` | `mysql_data` | Relational persistence for 12 domain tables. Automated health check via `mysqladmin ping`. |
| `redis` | `medical_redis` | `redis:7-alpine` | `6379:6379` | `redis_data` | AOF-persisted queue broker for decoupling CPU-intensive OCR and PDF extraction from HTTP requests. |
| `ollama` | `medical_ollama` | `ollama/ollama:latest` | `11434:11434` | `ollama_data` | Offline CPU clinical inference hosting `qwen2.5:1.5b` (primary) and `qwen2.5:3b` (fallback). |
| `worker` | `medical_worker` | `worker/Dockerfile` | Internal | `reports_data`, `charts_data` | Background daemon listening on Redis queue `medical:queue:report_processing` for OCR, table extraction, and normalization. |

### Running with Docker Compose

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
2. **Build and Start All Containers:**
   ```bash
   docker compose build
   docker compose up -d
   ```
3. **Verify Container Health:**
   ```bash
   docker compose ps
   ```
4. **Pull Local Clinical LLM Models into Persistent Volume:**
   - **Linux / macOS:**
     ```bash
     chmod +x scripts/init-ollama.sh
     ./scripts/init-ollama.sh
     ```
   - **Windows:**
     ```cmd
     scripts\init-ollama.bat
     ```
5. **Inspect Streaming Logs:**
   ```bash
   docker compose logs -f backend
   docker compose logs -f worker
   ```

---

## ☸️ Kubernetes Production Architecture & Manifests

The `k8s/` directory contains declarative manifests organized under the dedicated `medical-analyzer` namespace:

```text
k8s/
├── namespace.yaml                  # Dedicated 'medical-analyzer' namespace
├── configmap.yaml                  # Unified application environment settings
├── secrets.example.yaml            # Secret template for DB password, JWT secret, and API keys
├── reports-pvc.yaml                # Shared ReadWriteMany PVC for medical report storage
├── ingress.yaml                    # Nginx Ingress with upload limits & unbuffered SSE streaming
├── network-policy.yaml             # Zero-trust network isolation for MySQL, Redis, and Ollama
├── hpa.yaml                        # HorizontalPodAutoscalers for backend and worker pods
├── backend/
│   ├── deployment.yaml             # 2 stateless replicas, liveness/readiness probes, non-root user 1000
│   └── service.yaml                # ClusterIP service on port 8000
├── frontend/
│   ├── deployment.yaml             # 2 replicas serving Nginx SPA bundle
│   └── service.yaml                # ClusterIP service on port 80
├── worker/
│   ├── deployment.yaml             # Background worker deployment with reports-storage PVC mount
│   └── service.yaml                # Headless ClusterIP service
├── redis/
│   ├── deployment.yaml             # 1 replica Redis instance with healthcheck
│   └── service.yaml                # ClusterIP service on port 6379
├── ollama/
│   ├── deployment.yaml             # 1 replica Ollama instance with CPU limits & health probe
│   ├── service.yaml                # ClusterIP service on port 11434 (never exposed publicly)
│   └── pvc.yaml                    # 20Gi PVC persisting Ollama models
└── mysql/
    ├── statefulset.yaml            # StatefulSet with automated health probes and volume mount
    ├── service.yaml                # ClusterIP service on port 3306
    └── pvc.yaml                    # 20Gi PVC persisting MySQL relational data
```

### Local Kubernetes Deployment Workflow (Minikube / Kind)

```bash
# 1. Apply Namespace, ConfigMap, Secrets, and Storage Claims
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.example.yaml
kubectl apply -f k8s/reports-pvc.yaml

# 2. Deploy Internal Data Infrastructure
kubectl apply -f k8s/mysql/
kubectl apply -f k8s/redis/
# (Note: Standard production uses Groq API via ConfigMap/Secrets; k8s/ollama/ is optional for offline/air-gapped only)

# 3. Deploy Application Services
kubectl apply -f k8s/backend/
kubectl apply -f k8s/worker/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/network-policy.yaml

# 4. Verify Rollout Status
kubectl get pods -n medical-analyzer
kubectl get svc -n medical-analyzer
kubectl get pvc -n medical-analyzer
kubectl get ingress -n medical-analyzer
```

### Production Cloud Migration (EKS, GKE, AKS)
To transition from local Kubernetes to Managed Cloud Kubernetes:
1. **Managed Database:** Point `DB_HOST` in `k8s/configmap.yaml` to an AWS RDS, Google Cloud SQL, or Azure Database for MySQL instance. Delete `k8s/mysql/` manifests.
2. **Object Storage:** Set `STORAGE_BACKEND=s3` and configure `S3_BUCKET_NAME`, `S3_ACCESS_KEY`, and `S3_SECRET_KEY` in `k8s/secrets.example.yaml`. This replaces the local `reports-pvc` with cloud-native S3 / GCS.
3. **Ingress & TLS:** Replace `nginx.ingress.kubernetes.io/ssl-redirect: "false"` with `cert-manager` annotations (`cert-manager.io/cluster-issuer: "letsencrypt-prod"`).
4. **Secret Management:** Wire secrets via AWS Secrets Manager, Google Secret Manager, or HashiCorp Vault using the Kubernetes External Secrets Operator.

---

## 💾 Storage Architecture (`StorageService`)

Report persistence is decoupled from ephemeral container filesystems via [`backend/services/storage_service.py`](file:///d:/medical-report-analyzer/backend/services/storage_service.py):
- **`LocalStorageService`**: Default provider. Stores reports on a persistent volume mount (`/app/uploads`), sanitizing filenames against path traversal attacks.
- **`S3StorageService`**: Cloud provider. Streams report uploads to S3-compatible object stores (AWS S3, MinIO, GCP Storage) with local caching for instant OCR/PyMuPDF coordinate parsing.
- Factory function `get_storage_service()` dynamically selects the backend based on `STORAGE_BACKEND` (`local` or `s3`).

---

## ⚡ Asynchronous Processing Architecture (`QueueService` & `worker.py`)

To prevent multi-second OCR extraction from blocking user uploads, the system introduces a queue architecture:
- **`ASYNC_PROCESSING_ENABLED=true`**: `/api/reports/upload` validates the user and file, writes the report to persistent storage, records a `processing` row in MySQL, pushes a task to Redis list `medical:queue:report_processing`, and immediately returns HTTP 200.
- **`ASYNC_PROCESSING_ENABLED=false`**: Automatically falls back to in-process background task execution, ensuring full backward compatibility and zero external dependencies during offline test execution.
- **Worker Daemon ([`backend/worker.py`](file:///d:/medical-report-analyzer/backend/worker.py))**: Consumes tasks using blocking `BRPOP`, runs deterministic coordinate extraction, normalizes CBC/lab values, flags critical findings, triggers non-blocking clinical summaries, and updates MySQL to `completed`.

---

## 🩺 Health Check Probes & Observability

Three standardized endpoints provide fine-grained health status for Kubernetes and Docker orchestrators:

| Endpoint | HTTP Status | Probe Type | Description |
| :--- | :--- | :--- | :--- |
| `GET /health` | 200 OK | General | Verifies process responsiveness. |
| `GET /health/live` | 200 OK | Liveness | Lightweight probe determining solely whether the process is alive. **0 database calls, 0 LLM calls, 0 OCR**. |
| `GET /health/ready` | 200 OK / 503 Service Unavailable | Readiness | Verifies database connectivity (`SELECT 1`). Returns 503 if MySQL is unreachable. Does not invoke LLM. |
| `GET /ready` | 200 OK / 503 | Legacy Alias | Backward compatibility alias for existing monitors. |

---

## 🗄️ Database Migrations (`Alembic`)

The application includes an Alembic migration system configured in `backend/alembic.ini` and `backend/alembic/env.py`:
- **Initial Migration:** [`backend/alembic/versions/001_initial_schema.py`](file:///d:/medical-report-analyzer/backend/alembic/versions/001_initial_schema.py) covers all 12 platform tables.
- **Safe Existing Database Upgrades:** Employs SQLAlchemy `Inspector` checks to verify table existence before execution, preventing duplicate table creation errors on existing databases.
- **Run Migrations:**
  ```bash
  cd backend
  alembic upgrade head
  ```

---

## 🛡️ Production Logging & Secret Scrubbing

Configured in [`backend/logging_config.py`](file:///d:/medical-report-analyzer/backend/logging_config.py):
- **Container Output:** Streams directly to `sys.stdout` (and `sys.stderr` for errors) for compatibility with `docker logs` and `kubectl logs`.
- **Sensitive Data Scrubber (`SanitizedFormatter`):** Uses regex pattern matching to automatically redact:
  - Passwords: `***REDACTED***`
  - JWT Bearer Tokens: `***REDACTED_JWT***`
  - API Keys: `***REDACTED_KEY***`
  - Secrets: `***REDACTED_SECRET***`
- Medical report contents and patient identifiable identifiers are excluded from system log streams.

---

## 🧪 Testing & Quality Assurance

The platform includes a comprehensive test suite in `backend/tests/` running on `pytest`.

Run all tests from `backend/`:
```bash
cd backend
pytest tests/ -v
```

### 📊 Test Suite Status & Coverage:
- **Total Tests:** **195 passed** (100% pass rate, 0 failures, 0 skipped, 0 regressions)
- **Execution Time:** ~238 seconds across all security, clinical extraction, OCR, AI, and containerization suites.

### Key Test Suites:
- **`test_deployment_k8s_docker.py` (13 tests):** Validates Kubernetes readiness/liveness probes, database connectivity failover, `StorageService` path traversal prevention, `QueueService` Redis enqueueing, logging secret scrubbing, and report download IDOR protection.
- **`test_doctor_notifications.py` (14 tests / 24 scenarios):** Validates patient access request notifications, minimal disclosure privacy, IDOR defense, and transactional approvals.
- **`test_context_aware_ai_and_clear_chat.py` (11 tests):** Verifies patient JWT scoping, doctor active patient verification, and non-destructive chat clearing.
- **`test_deployment_hardening.py`:** Tests bounded failover, rate limiting, request size limits, and ID scrubbing.
- **`test_three_tier_and_streaming.py`:** Tests Jev System-1 multi-head triage, emergency short-circuits (<1ms), and SSE token streaming.
- **`test_medical_classifier_and_rejection.py`:** Tests document classification and non-medical document rejection.
- **`test_cbc_coordinate_and_normalization.py`:** Tests PyMuPDF coordinate grouping and extraction idempotency.
- **`test_pre_deployment_audit.py`:** Tests pre-deployment health endpoints and audit checks.

---

## 🔄 Troubleshooting & Rollback

### Common Operational Issues

1. **Ollama Connection Timeout inside Container:**
   - Verify `OLLAMA_BASE_URL=http://ollama:11434` is set (not `localhost`).
   - Test connectivity from backend container:
     ```bash
     docker compose exec backend curl -s http://ollama:11434/api/tags
     ```
2. **Worker Not Processing Jobs:**
   - Verify Redis is healthy: `docker compose exec redis redis-cli ping`
   - Check pending queue length: `docker compose exec redis redis-cli llen medical:queue:report_processing`
   - Inspect worker logs: `docker compose logs -f worker`
3. **Database Migration Desynchronization:**
   - Verify migration state: `cd backend && alembic current`
   - Stamp existing database: `cd backend && alembic stamp head`

### Rollback Procedures
- **Docker Compose:**
  ```bash
  docker compose down
  git checkout <previous_commit>
  docker compose up -d --build
  ```
- **Kubernetes Rollback:**
  ```bash
  kubectl rollout undo deployment/backend -n medical-analyzer
  kubectl rollout undo deployment/worker -n medical-analyzer
  kubectl rollout undo deployment/frontend -n medical-analyzer
  ```

---

## 🚀 Limitations & Future Roadmap

### Current System Boundaries
- **In-Cluster Ollama:** CPU-based inference; response latency depends on host CPU core allocation. GPU passthrough supported by adding NVIDIA container runtime.
- **English Language OCR:** Extraction rules optimized primarily for English medical lab reports.

### Future Roadmap
- [ ] **GPU Operator Integration:** NVIDIA GPU device plugin support for sub-second Ollama inference in Kubernetes.
- [ ] **DICOM Radiological Imaging:** Built-in viewer for X-ray, CT, and MRI scans.
- [ ] **HL7 FHIR Interoperability:** Native import and export of FHIR clinical resources.

