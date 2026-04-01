# Quick Start Guide

## Prerequisites Installation

### Windows
1. Install Python 3.8+ from https://www.python.org/downloads/
2. Install Node.js from https://nodejs.org/
3. Install Tesseract OCR:
   - Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Or use Chocolatey: `choco install tesseract`
4. Install Poppler (for PDF processing):
   - Download from https://github.com/oschwartz10612/poppler-windows/releases
   - Add to PATH

### macOS
```bash
brew install python3 node tesseract poppler
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv nodejs npm tesseract-ocr poppler-utils
```

## Setup & Run

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run backend:**
   ```bash
   python main.py
   ```
   
   Backend will start at `http://localhost:8000`

### Frontend Setup

1. **Open a new terminal and navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   
   Frontend will start at `http://localhost:3000`

## First Steps

1. **Open browser:** Navigate to `http://localhost:3000`

2. **Register an account:**
   - Click "Create a new account"
   - Fill in your details
   - Choose role: Patient or Doctor

3. **Login** with your credentials

4. **Upload a medical report:**
   - Go to Reports page
   - Drag and drop a PDF or image file
   - Wait for processing (OCR and AI analysis)

5. **View your dashboard:**
   - See health summary charts
   - View recent reports
   - Track medicines

## Troubleshooting

### OCR Not Working
- Ensure Tesseract is installed and in PATH
- For Windows, you may need to set TESSDATA_PREFIX environment variable
- Check that Poppler is installed for PDF processing

### NLP Models Not Loading
- First run will download models (may take time)
- Ensure you have internet connection for initial setup
- Models are cached locally after first download

### Port Already in Use
- Backend: Change port in `backend/main.py` (line with `uvicorn.run`)
- Frontend: Change port in `frontend/vite.config.js`

### Database Issues
- Delete `backend/medical_reports.db` to reset database
- Tables will be recreated on next startup

## Notes

- All processing happens locally - no external API calls
- First OCR/NLP processing may be slow (models loading)
- Charts are generated server-side and served as images
- Password hashing uses bcrypt (secure for development)

