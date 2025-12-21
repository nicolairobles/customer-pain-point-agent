# Streamlit Hero Layout – Story 1.4.1

## Goals
- Translate the design mock (purple hero screen with logo + query pill) into a Streamlit-ready specification.
- Capture tokens, layout rules, and accessibility notes so 1.4.2+ implementation is straightforward.
- Provide hooks for future agent integration (1.3.3+) and multi-source filters (Phase 2).

## Layout Structure
1. **Hero Container (`st.container`)**
   - Background: solid `#48285d` (matching the design).
   - Vertical spacing: 15% viewport height top padding on desktop; 10% on mobile.
2. **Logo Row**
   - Centered image (`st.image`) sized 240 px wide desktop / 160 px mobile.
   - Alt text: `"Pain Point logo"` for accessibility.
3. **Tagline**
   - `st.markdown` block with the copy: *“What’s eating you? Enter your pain point in the prompt below…”*
   - Typography: `Lato` regular, 20 px (desktop) / 18 px (mobile), line height 1.6, color `#efeaf2`.
4. **Query Input Zone**
   - Wrap `st.text_area` inside `st.columns([0.15, 0.7, 0.15])` so the pill stays centered at large widths.
   - Use custom CSS (in 1.4.2) to style:
     - Background `#efeaf2`
     - Border radius `999px`
     - Left icon slot (paperclip) using `st.markdown` + absolute positioning
     - Right submit icon (arrow) acting as button (initially decorative; 1.4.2 will wire it to form submit)
   - Provide explicit label `"Describe your pain point"` (visually hidden for screen readers).
5. **Future Results Area Placeholder**
   - Reserve `st.container` below the hero for results. Copy for spec: “Results render here once the agent returns data.”
   - Include collapsible diagnostics/observability panel per best practices (LangChain Streamlit callback handler).

## Design Tokens
| Token | Value | Usage |
|-------|-------|-------|
| `color.background.primary` | `#48285d` | Page background |
| `color.text.primary` | `#efeaf2` | Tagline, default text on dark background |
| `color.input.bg` | `#efeaf2` | Query input fill |
| `color.input.icon` | `#7a708b` | Paperclip + arrow icons |
| `font.primary` | `"Lato", "Helvetica Neue", sans-serif` | All text |
| `spacing.section` | `48px` | Vertical gap between logo → tagline, tagline → input |

## Accessibility Notes
- Provide hidden `<label>` linked to the text input.
- Ensure placeholder text contrast: `#7a708b` on `#efeaf2` gives 4.0:1 contrast (acceptable for large text).
- Keyboard flow: logo (skip), tagline, input field, submit arrow (button), results container.
- Add ARIA labels to icon buttons once implemented.

## Integration Hooks
- **Agent Calls**: input submission triggers LangChain agent executor (1.3.3). `st.session_state` can store query, response, cost metrics.
- **Observability**: left align a collapsible `st.expander("Agent trace")` to display callback handler output.
- **Source Filters**: for Phase 2, plan sidebar using `st.sidebar` with checkboxes/toggles; document here for stakeholders.
- **Error Messaging**: reserve `st.empty()` below input to render alerts (rate limits, validation).

## Styling System (1.4.4)
- Global tokens/overrides live in `app/theme.py`; `apply_global_styles()` injects CSS that aligns typography, background gradient, and button styling with the hero mock.
- Components should rely on CSS variables (`--color-surface`, `--color-text-secondary`, etc.) rather than hard-coded hex values to stay consistent across light/dark modes.
- Responsive tweaks are handled via `@media` blocks in the theme plus component-level styles (`results_display.py`); reuse the variables when extending tabs/metrics.
- To preview styling without the full agent, run `streamlit run scripts/dev_results_preview.py` which renders the results card layout with sample data.

## Developer UX Exercise Checklist
1. **Launch the app**
   - `source .venv/bin/activate`
   - `streamlit run app/streamlit_app.py`
   - App serves at `http://localhost:8501`.
2. **Desktop verification**
   - Test empty input, valid query (<= 50 words), and over-limit state.
   - Confirm info/error/success feedback banners and word counter updates.
   - Select each preset—text area should populate and preset selector should reset.
3. **Responsive sweep**
   - Use browser dev tools device mode (e.g., iPhone 14, iPad, 1280‑px desktop).
   - Ensure input pill remains centered, caption legible, and preset dropdown accessible.
   - Check that virtual keyboards do not hide banners on mobile widths.
4. **Capture findings**
   - Record deviations, screenshots, or follow-up tasks in the story issue before checking off UX review.

## Deliverables for Story 1.4.1
- This document stored under `docs/ui`.
- Story/issue checklists updated to mark wireframes/spec prepared, accessibility documented, feasibility confirmed with developers.
- Product owner sign-off recorded in story markdown once they review this spec.

