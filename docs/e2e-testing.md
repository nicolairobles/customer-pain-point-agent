# E2E Testing with Playwright

This document describes how to run the end-to-end (E2E) browser tests for the Customer Pain Point Discovery Agent.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install pytest-playwright playwright
   ```

2. **Install Chromium browser:**
   ```bash
   playwright install chromium
   ```

## Running Tests

### Quick smoke tests (< 10 seconds)
```bash
pytest tests/e2e/test_smoke.py -v
```

### Full E2E suite (may take 2+ minutes due to LLM calls)
```bash
pytest tests/e2e/ -v
```

### Run with visible browser (for debugging)
```bash
pytest tests/e2e/ -v --headed
```

### Run specific test
```bash
pytest tests/e2e/test_analyst_report.py::TestAnalystReport::test_analyst_report_has_conclusion -v
```

## Test Files

| File | Purpose |
|------|---------|
| `test_smoke.py` | Quick verification that app loads correctly |
| `test_query_flow.py` | Tests query submission and results display |
| `test_analyst_report.py` | Validates Analyst Report completeness (not truncated) |
| `test_error_states.py` | Tests error handling and recovery |

## Troubleshooting

### Port conflicts
The test fixture automatically finds an available port. If you see connection errors, ensure no other Streamlit instances are running.

### Slow tests
E2E tests that hit the LLM can take 60-120 seconds. Use `--timeout 300` for extra buffer:
```bash
pytest tests/e2e/ -v --timeout 300
```

### Test isolation
Each test gets a fresh browser page. The Streamlit server is shared across all tests in a session.

## CI/CD Integration

In GitHub Actions, install browsers before running tests:
```yaml
- name: Install Playwright browsers
  run: playwright install chromium

- name: Run E2E tests
  run: pytest tests/e2e/ -v --headless
```
