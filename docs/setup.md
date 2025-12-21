# Project Setup Guide

1. Verify you are using Python 3.11.x (the project now targets LangChain 0.0.340 which ships wheels for CPython 3.11):
   ```bash
   python --version  # or python3 --version
   ```
   The output should be `Python 3.11.x`. If you are on Apple Silicon/Intel macOS and need a binary installer, you can bootstrap Miniforge and create an environment with `conda create -n cppagent-py311 python=3.11`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   After installation, confirm the core packages are available:
   ```bash
   python -m pip list | grep -E "langchain|streamlit|praw"
   ```
4. Copy `.env.example` to `.env` and populate API credentials.
5. Run the Streamlit app:
   ```bash
   streamlit run app/streamlit_app.py
   ```
6. Execute the test suite:
   ```bash
   pytest
   ```
7. When finished working, deactivate the virtual environment:
   ```bash
   deactivate
   ```
