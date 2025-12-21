# Build a production-ready image for the Streamlit dashboard
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python scripts/healthcheck.py --url "http://localhost:8501/" || exit 1

EXPOSE 8501

ENTRYPOINT sh -c 'streamlit run app/streamlit_app.py --server.port=${STREAMLIT_SERVER_PORT} --server.address=0.0.0.0'
