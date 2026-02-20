# =============================================================================
# Auto Pilot — Dockerfile (Streamlit on python:3.11-slim)
# Optimised for Zeabur container deployment.
# =============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Streamlit listens on 8501
EXPOSE 8501

# Streamlit config: disable the browser-open prompt and CORS check
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["streamlit", "run", "V2_Engine/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
