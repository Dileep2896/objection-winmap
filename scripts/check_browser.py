"""Optional real-browser smoke checks. Run against an already running local server."""

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)
BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
CHROME = os.getenv(
    "CHROME_EXECUTABLE", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


def run():
    errors = []
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until="networkidle")
        assert page.locator(".objection-row:visible").count() == 6
        page.screenshot(path=str(ARTIFACTS / "winmap-desktop.png"), full_page=True)
        page.get_by_role("searchbox", name="Find an objection").fill("price")
        assert page.locator(".objection-row:visible").count() == 1
        page.get_by_role("searchbox").fill("unmatched")
        assert page.locator("#empty-search").is_visible()
        page.get_by_role("searchbox").fill("")
        page.get_by_role("button", name="Enough data", exact=True).click()
        assert page.locator(".objection-row:visible").count() == 3
        page.get_by_role("button", name="See price evidence").click()
        assert page.locator("#response-3").get_attribute("open") is not None
        page.select_option("#rep-select", "ben")
        page.get_by_role("button", name="Open brief").click()
        page.wait_for_url("**/reps/ben")
        assert page.get_by_role("heading", name="Spouse / partner").is_visible()
        page.get_by_role("button", name="Start practicing").click()
        assert "Pause practice" in page.locator("#practice-start").inner_text()
        page.locator("#practice-start").click()
        assert "paused" in page.locator("#practice-status").inner_text()
        page.clock.install()
        page.get_by_role("button", name="Start practicing").click()
        page.clock.fast_forward(31000)
        assert "Drill complete" in page.locator("#practice-status").inner_text()
        page.locator(".practice-section .source-link").click()
        page.wait_for_url("**/meetings/**")
        assert page.locator(":target").count() == 1
        checks.append(
            "Search, empty filter, minimum-n filter, evidence, rep selection, drill, citation"
        )
        context.close()

        for width in (320, 375, 768, 1280):
            ctx = browser.new_context(viewport={"width": width, "height": 720})
            tab = ctx.new_page()
            tab.on("pageerror", lambda error: errors.append(str(error)))
            for route, name in (("/", "winmap"), ("/reps/ben", "brief"), ("/story", "story")):
                tab.goto(BASE + route, wait_until="networkidle")
                if not tab.evaluate("document.documentElement.scrollWidth <= innerWidth"):
                    tab.screenshot(path=str(ARTIFACTS / "overflow.png"), full_page=True)
                    offenders = tab.evaluate("""[...document.querySelectorAll('body *')]
                        .filter(el => el.getBoundingClientRect().right > innerWidth + 1
                            && !el.closest('.table-scroll'))
                        .map(el => [el.tagName, el.className, el.getBoundingClientRect().right])""")

                    raise AssertionError(f"Overflow at {width}, {route}: {offenders}")
                if route == "/story":
                    assert tab.evaluate("Boolean(window.Motion?.animate)"), (
                        "Motion CDN did not load"
                    )
                    for section in tab.locator(".story-section").all():
                        section.scroll_into_view_if_needed()
                        tab.wait_for_timeout(1700)
                    assert tab.locator(".impact-number").inner_text() == "+$184,000"
                    tab.locator("#hook").scroll_into_view_if_needed()
                    tab.wait_for_timeout(800)
                if width in (375, 1280):
                    tab.screenshot(path=str(ARTIFACTS / f"{name}-{width}.png"), full_page=True)
            ctx.close()
            checks.append(f"Desktop/mobile layouts and Motion playback at {width}px")

        ctx = browser.new_context(viewport={"width": 375, "height": 720}, reduced_motion="reduce")
        tab = ctx.new_page()
        tab.on("pageerror", lambda error: errors.append(str(error)))
        tab.goto(BASE + "/story", wait_until="networkidle")
        assert tab.locator('[data-target="72"]').inner_text() == "72"
        assert tab.locator(".impact-number").inner_text() == "+$184,000"
        assert (
            tab.evaluate("document.getAnimations().filter(a => a.playState === 'running').length")
            == 0
        )
        assert tab.locator("#growing-gap").evaluate(
            "el => Math.abs(Number(getComputedStyle(el).transform.split(',')[0].slice(7)) "
            "- Number(el.dataset.to)) < .001"
        )
        checks.append("Reduced motion: final counters, full diagram, zero running animations")
        ctx.close()

        ctx = browser.new_context(java_script_enabled=False, viewport={"width": 375, "height": 720})
        tab = ctx.new_page()
        tab.goto(BASE + "/story", wait_until="networkidle")
        assert tab.locator(".impact-number").inner_text() == "+$184,000"
        assert tab.get_by_role("heading", name="of sales still happen face-to-face.").is_visible()
        checks.append("No-JavaScript final story content")
        ctx.close()
        browser.close()
    assert not errors, errors
    (ARTIFACTS / "browser-results.json").write_text(
        json.dumps({"checks": checks, "errors": errors}, indent=2)
    )
    print("Browser checks passed:")
    print("\n".join(checks))


if __name__ == "__main__":
    run()
