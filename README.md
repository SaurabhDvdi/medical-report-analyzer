# Medical Report Analyzer

A comprehensive full-stack application for uploading, analyzing, and visualizing medical reports. The system features a Python/FastAPI backend for all data processing, analytics, and visualization, and a React frontend for the user interface.

## Features

- **Role-based Access Control**: Separate interfaces for patients and doctors
- **Report Upload & Processing**: Drag-and-drop file upload with background OCR processing
- **AI-Powered Analysis**: Automatic text extraction using Tesseract/EasyOCR and NLP summarization using Hugging Face Transformers
- **Structured Data Extraction**: Automatic parsing of lab values with reference ranges and abnormality detection
- **Comprehensive Analytics**: Time-series trend analysis, parameter comparisons, health summaries, and correlation heatmaps
- **Medicine Tracking**: Track current and past medications with timeline visualization
- **Doctor Interface**: Rich text notes editor for doctors to add patient notes
- **Dynamic Category Detection**: Automatic report type detection with dynamic category expansion
- **CSV Export**: Export lab values data for external analysis

## Architecture

### Backend (Python/FastAPI)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT-based authentication
- **OCR**: Tesseract/EasyOCR for text extraction
- **NLP**: Hugging Face Transformers (BART/T5) for summarization
- **Analytics**: Pandas, NumPy, Matplotlib, Seaborn for data processing and visualization
- **File Storage**: Local file system for uploaded reports

### Frontend (React)
- **Framework**: React with Vite (dev server port 3000)
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with shadcn/ui patterns
- **State Management**: React Context API
- **HTTP Client**: Axios (`src/utils/api.js`)
  - `baseURL`: `http://localhost:8000`
  - Request interceptor: `Authorization: Bearer <token>` from `localStorage` on every request; `FormData` uploads do not force `application/json` so multipart boundaries are correct
  - Response interceptor: HTTP **401** clears stored credentials and sends the browser to `/login`

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
```

The backend will be available at `http://localhost:8000`

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

The frontend will be available at `http://localhost:3000`

## Usage

1. **Register/Login**: Create an account as either a patient or doctor
2. **Upload Reports**: Drag and drop medical report files (PDF, PNG, JPG)
3. **View Analysis**: Reports are automatically processed with OCR and AI summarization
4. **Track Medicines**: Add and manage current and past medications
5. **View Analytics**: Access trend charts, multi-parameter comparisons, health summaries, and correlation heatmaps (PNG charts from the API)
6. **Export data**: Download lab values as CSV from the Reports or Report Viewer pages
7. **Doctor Portal**: Doctors can view all patients, add notes, and analyze reports (patient list uses `/api/users/patients` only for doctor accounts)

## Database Schema

- **Users**: User accounts with role-based access (patient/doctor)
- **Reports**: Uploaded medical reports with OCR status and AI summaries
- **LabValues**: Structured lab test results with parameters, values, units, and abnormality flags
- **Medicines**: Medication tracking with dates and status
- **DoctorNotes**: Rich text notes added by doctors
- **ReportCategories**: Dynamic categories for different report types

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Reports
- `POST /api/reports/upload` - Upload medical report
- `GET /api/reports` - Get all reports
- `GET /api/reports/{id}` - Get report details
- `DELETE /api/reports/{id}` - Delete report
- `GET /api/reports/{id}/download` - Download report file
- `GET /api/report-categories` - Report type categories (OCR)

### Doctor discovery & clinical taxonomy
- `GET /api/categories` - Doctor clinical categories
- `GET /api/specialties?category_id=` - Specialties (optional filter)
- `POST /api/specialties` - Create specialty (doctor only; used from profile tools)
- `GET /api/doctors` - Search/filter doctors (`name`, `category_id`, `specialty_id` query params)
- `GET /api/patient/discovery-stats`, `GET /api/doctor/assignment-stats` - Dashboard counts
- `POST /api/patient/doctor-access`, `GET /api/patient/doctor-access` - Patient access requests
- `GET /api/doctor/patient-access-requests`, `POST .../accept`, `POST .../reject` - Doctor workflow

### Lab Values
- `GET /api/lab-values` - Get lab values with filters

### Medicines
- `POST /api/medicines` - Add medicine
- `GET /api/medicines` - Get all medicines
- `PUT /api/medicines/{id}` - Update medicine
- `DELETE /api/medicines/{id}` - Delete medicine

### Analytics
- `GET /api/analytics/trend/{parameter_name}` - Get trend chart
- `GET /api/analytics/comparison` - Get parameter comparison chart
- `GET /api/analytics/health-summary` - Get health summary chart
- `GET /api/analytics/correlation` - Get correlation heatmap

### Doctor Notes
- `POST /api/doctor-notes` - Create doctor note
- `GET /api/doctor-notes` - Get doctor notes

### Export
- `GET /api/export/csv` - Export lab values as CSV

## Development Notes

- The system runs completely locally without external API dependencies
- OCR processing happens in the background after file upload
- Charts are generated server-side and served as PNG images
- All analytics and data processing happens in the Python backend
- The frontend is purely presentational, consuming API endpoints

## Security Considerations

- Passwords are hashed with bcrypt on the backend; never log or expose raw passwords
- Change the JWT secret key in `backend/auth.py` for production
- Implement rate limiting for API endpoints
- Add input validation and sanitization
- Use environment variables for sensitive configuration

## License

This project is for educational purposes.

