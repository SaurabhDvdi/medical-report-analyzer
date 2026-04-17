@echo off
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
python main.py

http://localhost:8000/redoc --> to see Cleaner Documentation View
http://localhost:8000/docs --> in case you want to try out each end point refere to Swagger UI