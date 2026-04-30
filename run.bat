@echo off
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
uvicorn app.main:app --reload
