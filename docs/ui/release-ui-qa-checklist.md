# UI Release QA Checklist

Use this checklist before cutting a release to confirm the Streamlit UI is stable, consistent, and production-ready.

## Cross-Browser
- [ ] Chrome: first load → Analyze → results (no flicker/legacy styling)
- [ ] Safari (or Firefox): first load → Analyze → results (no flicker/legacy styling)

## Responsive
- [ ] ≤480px (mobile): input, buttons, and results remain readable and usable
- [ ] ~768px (tablet): layout spacing and tabs/cards behave correctly
- [ ] ≥1280px (desktop): layout uses available width and stays visually consistent

## Rerun / State
- [ ] Submit Analyze multiple times; UI styling and component hierarchy remain consistent
- [ ] Query presets behave as expected and don’t produce stale input on submit

## Validation / Empty / Error States
- [ ] Empty input shows clear guidance
- [ ] Over-limit input shows clear guidance
- [ ] Agent unavailable shows a helpful warning and no broken UI
- [ ] Partial results (simulated) show warnings without breaking the layout

## Production Gating
- [ ] Debug UI is hidden by default (`UI_PRODUCTION_MODE=true`)
- [ ] Debug UI only appears intentionally (set `UI_PRODUCTION_MODE=false` or `SHOW_DEBUG_PANEL=true`)
