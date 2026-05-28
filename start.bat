@echo off

echo Starting Qdrant...
docker start qdrant >nul 2>&1

echo Starting FastAPI backend...
start cmd /k "cd /d E:\Python\RAGproductionApp && call .venv\Scripts\activate && uv run uvicorn main:app --reload"

timeout /t 5 >nul

echo Starting Inngest...
start cmd /k "cd /d E:\Python\RAGproductionApp && call .venv\Scripts\activate && npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery"

timeout /t 3 >nul

echo Starting Streamlit UI...
start cmd /k "cd /d E:\Python\RAGproductionApp && call .venv\Scripts\activate && streamlit run app.py"

echo All services started.