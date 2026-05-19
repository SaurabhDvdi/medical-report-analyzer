# Medical Report Analyzer

A comprehensive full-stack application for uploading, analyzing, and visualizing medical reports. The system features a Python/FastAPI backend for all data processing, analytics, and visualization, and a React frontend for the user interface.

## Features

- **Role-based Access Control**: Separate interfaces for patients and doctors with explicit access approval workflow
- **Report Upload & Processing**: Drag-and-drop file upload with background OCR processing
- **AI-Powered Analysis**: Automatic text extraction using Tesseract/EasyOCR and NLP summarization using Hugging Face Transformers
- **Structured Data Extraction**: Automatic parsing of lab values with reference ranges and abnormality detection
- **Comprehensive Analytics**: Time-series trend analysis, parameter comparisons, health summaries, and correlation heatmaps
- **Medicine Tracking**: Track current and past medications with timeline visualization
- **Doctor Interface**: Rich text notes editor for doctors to add patient consultation notes
- **Dynamic Category Detection**: Automatic report type detection with dynamic category expansion
- **CSV Export**: Export lab values data for external analysis
- **Patient-Doctor Matching**: Doctor discovery by category and specialty with access request workflow
- **Health Risk Assessment**: AI-powered health risk calculation based on lab values
- **Comprehensive Profiles**: Patient health profiles (age, weight, BMI, allergies, chronic conditions) and doctor credentials
- **Doctor Taxonomy**: Hierarchical doctor specialization system (Category → Specialty)
- **AI-Generated Insights**: Automatic generation of health insights from medical data

## Architecture

### Backend (Python/FastAPI)

- **Database**: MySQL with SQLAlchemy ORM (port 3306, database: `medical_report_analysis`)
- **Framework**: FastAPI with Uvicorn server
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **OCR**: EasyOCR and Tesseract for text extraction from PDFs and images
- **PDF Processing**: pdf2image for PDF to image conversion
- **NLP**: Hugging Face Transformers (BART/T5) for summarization
- **ML/Analytics**: PyTorch, Pandas, NumPy, scikit-learn for data processing and analysis
- **Visualization**: Matplotlib, Seaborn for chart generation
- **File Storage**: Local file system for uploaded reports and generated charts

### Frontend (React)

- **Framework**: React 18 with Vite (dev server port 5173)
- **Styling**: Tailwind CSS with PostCSS and autoprefixer
- **UI Components**: Radix UI, Heroicons, Lucide React
- **State Management**: React Context API with TanStack React Query v5
- **Routing**: React Router v6
- **Visualization**: Recharts for interactive charts
- **Animations**: Framer Motion
- **HTTP Client**: Axios (`src/utils/api.js`)
  - `baseURL`: `http://localhost:8000`
  - Request interceptor: `Authorization: Bearer <token>` from `localStorage` on every request; `FormData` uploads do not force `application/json` so multipart boundaries are correct
  - Response interceptor: HTTP **401** clears stored credentials and sends the browser to `/login`
- **Utilities**: date-fns, clsx, tailwind-merge, react-dropzone, react-hot-toast, react-loading-skeleton, react-quill

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- Tesseract OCR (for OCR functionality)
- Poppler (for PDF processing)

#### Install Tesseract OCR

**Windows:**

```bash
# Download from https://github.com/UB-Mannheim/tesseract/wiki
# Or use chocolatey: choco install tesseract
```

**macOS:**

```bash
brew install tesseract
```

**Linux:**

```bash
sudo apt-get install tesseract-ocr
```

#### Install Poppler (for PDF processing)

**Windows:**

```bash
# Download from https://github.com/oschwartz10612/poppler-windows/releases
```

**macOS:**

```bash
brew install poppler
```

**Linux:**

```bash
sudo apt-get install poppler-utils
```

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the backend server:

```bash
python main.py
# OR using uvicorn directly:
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

**Note**: On first run, the system will:

- Create all required MySQL tables automatically
- Seed the doctor taxonomy (categories and specialties)
- Initialize the database schema

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Register/Login**: Create an account as either a patient or doctor
2. **Upload Reports**: Drag and drop medical report files (PDF, PNG, JPG)
3. **View Analysis**: Reports are automatically processed with OCR and AI summarization
4. **Track Medicines**: Add and manage current and past medications
5. **View Analytics**: Access trend charts, multi-parameter comparisons, health summaries, and correlation heatmaps (PNG charts from the API)
6. **Export data**: Download lab values as CSV from the Reports or Report Viewer pages
7. **Doctor Portal**: Doctors can view all patients, add notes, and analyze reports (patient list uses `/api/users/patients` only for doctor accounts)

## Database Schema

- **Users**: User accounts with role-based access (patient/doctor) and doctor specialization references
- **Reports**: Uploaded medical reports with OCR status and AI summaries
- **LabValues**: Structured lab test results with parameters, values, units, and abnormality flags
- **Medicines**: Medication tracking with dates and status
- **DoctorNotes**: Consultation notes added by doctors
- **ReportCategories**: Dynamic categories for different report types
- **DoctorProfile**: Extended doctor information (credentials, license, clinic details, experience)
- **PatientProfile**: Extended patient information (health metrics, allergies, chronic conditions, lifestyle)
- **DoctorCategory**: Clinical specialty categories (Cardiologist, Dermatologist, etc.)
- **DoctorSpecialty**: Specific specialties within categories (Heart, Blood Vessels, etc.)
- **PatientDoctorAccess**: Access control system for doctor-patient relationships with approval workflow (pending, accepted, approved, rejected)

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user (patient or doctor)
- `POST /api/auth/login` - Login user and get JWT token

### Reports

- `POST /api/reports/upload` - Upload medical report (PDF/Image)
- `GET /api/reports` - Get all reports (filtered by role)
- `GET /api/reports/{id}` - Get report details
- `DELETE /api/reports/{id}` - Delete report
- `GET /api/reports/{id}/download` - Download report file
- `GET /api/report-categories` - Report type categories

### Doctor Discovery & Clinical Taxonomy

- `GET /api/categories` - Get all doctor clinical categories
- `GET /api/specialties` - Get all specialties (with optional `category_id` filter)
- `POST /api/specialties` - Create new specialty (doctor only)
- `GET /api/doctors` - Search/filter doctors by name, category, or specialty
- `GET /api/patient/discovery-stats` - Patient dashboard statistics
- `GET /api/doctor/assignment-stats` - Doctor dashboard statistics

### Patient-Doctor Access Management

- `POST /api/patient/doctor-access` - Patient requests access to doctor
- `GET /api/patient/doctor-access` - Get patient's doctor access requests
- `GET /api/doctor/patient-access-requests` - Get doctor's pending access requests
- `POST /api/doctor/patient-access-requests/{id}/accept` - Doctor accepts patient request
- `POST /api/doctor/patient-access-requests/{id}/reject` - Doctor rejects patient request

### Lab Values

- `GET /api/lab-values` - Get lab values with optional parameter filtering
- `POST /api/lab-values` - Create lab value

### Medicines

- `POST /api/medicines` - Add medicine
- `GET /api/medicines` - Get all medicines
- `PUT /api/medicines/{id}` - Update medicine
- `DELETE /api/medicines/{id}` - Delete medicine

### Patient & Doctor Profiles

- `GET /api/patient/profile` - Get patient profile
- `PUT /api/patient/profile` - Update patient profile
- `GET /api/doctor/profile` - Get doctor profile
- `PUT /api/doctor/profile` - Update doctor profile

### Dashboard & Analytics

- `GET /api/dashboard` - Get comprehensive dashboard with analytics, risk, and insights
- `GET /api/analytics/trend/{parameter_name}` - Get trend chart for parameter
- `GET /api/analytics/comparison` - Get parameter comparison chart
- `GET /api/analytics/health-summary` - Get health summary chart
- `GET /api/analytics/correlation` - Get correlation heatmap

### Doctor Notes & Consultation

- `POST /api/doctor-notes` - Create consultation note
- `GET /api/doctor-notes` - Get doctor notes (filtered by role)
- `PUT /api/doctor-notes/{id}` - Update note
- `DELETE /api/doctor-notes/{id}` - Delete note

### Data Export

- `GET /api/export/csv` - Export lab values as CSV

## Development Notes

- The system runs completely locally without external API dependencies
- OCR processing happens synchronously after file upload
- Charts are generated server-side using Matplotlib/Seaborn and served as PNG images
- All analytics and data processing happens in the Python backend
- The frontend is purely presentational, consuming API endpoints
- Doctor taxonomy is seeded on first database initialization
- Patient-doctor access is explicit: doctors can only see approved patients' data
- Both patients and doctors can be the same user (dual-role support)

## Security Considerations

- Passwords are hashed with bcrypt (72-byte limit enforced)
- **⚠️ IMPORTANT**: Change the JWT secret key in `backend/auth.py` for production (currently hardcoded)
- JWT token expiration: 30 minutes
- CORS currently allows `localhost:3000` and `localhost:5173` - update for production
- Implement rate limiting for API endpoints in production
- Add input validation and sanitization for all endpoints
- Use environment variables for sensitive configuration (DB credentials, API keys)
- Patient-Doctor access requires explicit approval (prevents unauthorized data access)
- All passwords are bcrypt-hashed before storage

## Environment Variables

Create a `.env` file in the backend directory:

```env
# MySQL Database
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=medical_report_analysis
```

## Troubleshooting

### MySQL Connection Issues

- Ensure MySQL is running on localhost:3306
- Verify database credentials in `.env` file
- Check that the database user has CREATE TABLE privileges

### OCR Issues

- Ensure Tesseract OCR is installed and in system PATH
- Install Poppler for PDF processing
- For GPU support, install PyTorch with CUDA support

### Frontend Issues

- Clear `node_modules` and reinstall: `npm install`
- Clear Vite cache: `npm run dev` with `--force` flag
- Ensure backend is running on port 8000

