# Project Setup Guide

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and populate API credentials.
4. Run the Streamlit app:
   ```bash
   streamlit run app/streamlit_app.py
   ```
5. Execute the test suite:
   ```bash
   pytest
   ```
