# Validation record

Validated locally on 2026-10-21 using Python 3.12.

- **44 pytest tests pass**, covering core statistics, cohorts, objection detection, ingestion, persistence across restarts, response ranking, personalized briefs, synthetic evaluation and pages.
- **Ruff passes.** One upstream Starlette/AnyIO deprecation warning appears in pytest; no application test failures.
- **`uv build` passes**, producing a source distribution and production wheel.
- **Installed-wheel smoke passes:** installed into a separate virtual environment and run from outside the source package; all 72 fixture meetings, API responses, HTML routes, styles, JavaScript, tokens and health check work.
- **Browser checks pass:** real headless Chrome at 320, 375, 768 and 1280px. Search, empty results, sufficient-data filter, expandable evidence, rep selection, practice timer completion, transcript deep links and animated story verified. Reduced motion has final counter/bar states and zero running animations. No-JavaScript story remains readable. No browser JavaScript errors.
- **Synthetic detector evaluation:** 406/406 utterances classified correctly (100%), including all 118 positive objection utterances; per-class recall also passes 90%. This is synthetic fixture accuracy, not a production model claim.
- **Docker build passes (verified by Claude Code):** the Codex sandbox could not reach the Docker daemon, so the Claude Code verifier ran `docker build` on the host. The image builds, and the container serves `/health`, `/`, `/story`, `/reps/ben` and `/api/winmap` with all 72 seeded meetings.

Reproduce the browser checks using the optional `browser` dependency group described in README.md. Ignored screenshots and the machine-readable browser report are in `artifacts/`.

## Independent verification (Claude Code)

Re-ran from a clean `uv sync`: 44 pytest tests pass, Ruff is clean, `uv build` passes and `docker build .` passes. The app was booted live, and `/`, `/story`, `/reps/ben` and `/meetings/ethan-04` all returned 200. An unknown rep returns 404 and a malformed payload returns 422. Headless Chromium at 1280x720 and 375px showed no horizontal overflow and no console errors. A manual review of the FastAPI routes, the statistics and the templates found no critical or high-severity issues.
