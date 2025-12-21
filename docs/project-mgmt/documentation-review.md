# Documentation Review Checklist

Use this checklist before merging changes that affect users, contributors, or production operations.

## Basics
- [ ] All docs are written for the intended audience (user vs developer vs ops).
- [ ] No secrets or sensitive data in screenshots or examples.
- [ ] Commands are copy/paste ready and reference correct paths.
- [ ] Environment variables are named consistently with `.env.example` and `config/settings.py`.

## Setup & local development
- [ ] `docs/setup.md` reflects current Python version and `requirements.txt` pins.
- [ ] Common install errors have troubleshooting steps (missing secrets, missing packages, port conflicts).

## Deployment & operations
- [ ] `docs/deployment/production-deployment.md` references the current workflow and rollback steps.
- [ ] `docs/deployment/streamlit-community-cloud.md` includes Streamlit secrets configuration.
- [ ] Healthcheck expectations are documented (required secrets depend on tool flags).

## Product/UI docs
- [ ] `docs/user-guide.md` exists and includes a quickstart + limitations.
- [ ] Screenshots are current and readable.

## Architecture
- [ ] `docs/project-mgmt/architecture-diagram.md` matches current modules and execution flow.
- [ ] Major modules are linked (UI, orchestrator, tools, aggregation, extractors).

## Verification
- [ ] Run a markdown link check (at minimum, internal relative links resolve).
- [ ] Spot-check the most important pages: `README.md`, `docs/setup.md`, `docs/user-guide.md`.
