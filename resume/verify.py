#!/usr/bin/env python3
"""Browser verification harness for /resume/ (Sprint 1, EC-21).

Headless ONLY, driven directly through playwright's Python API. The
Playwright MCP launches Chrome HEADED, which SIGTRAPs over SSH
(CVDisplayLinkCreateWithCGDisplay failed, CVReturn: -6670) - three
prior agents misdiagnosed that as "Playwright is broken."

Serves the REPO ROOT over http so /images/ and /css/ resolve exactly
as Cloudflare Pages will. curl 200s and clean diffs prove nothing
user-visible; these gates are the user-layer verification.

Gates:
  desktop 1280x900 chromium - console/network/layout/rail/skim-path
  mobile  375x812  WEBKIT   - sticky handoff, cred no-clip, tap targets
  JS-off  chromium          - all content present without JS
  PDF                       - ATS text assertions via pdftotext
"""

import functools
import json
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

RESUME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RESUME_DIR.parent
PORT = 8471
BASE = f"http://127.0.0.1:{PORT}/resume/"

DATA = json.loads((RESUME_DIR / "resume.json").read_text(encoding="utf-8"))
PDF_PATH = RESUME_DIR / DATA["meta"]["pdf_filename"]

failures = []
passes = []


def check(name, ok, detail=""):
    if ok:
        passes.append(name)
        print(f"  PASS  {name}")
    else:
        failures.append(name)
        print(f"  FAIL  {name}  {detail}")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def start_server():
    handler = functools.partial(QuietHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def new_instrumented_page(context):
    page = context.new_page()
    errors = []
    bad_responses = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("response", lambda r: bad_responses.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    return page, errors, bad_responses


def desktop_gates(p):
    print("== desktop 1280x900 chromium ==")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page, errors, bad = new_instrumented_page(context)
    page.goto(BASE, wait_until="networkidle")

    check("desktop: zero console errors", len(errors) == 0, "; ".join(errors[:5]))
    check("desktop: zero responses >= 400", len(bad) == 0, "; ".join(bad[:5]))
    check("desktop: details.venture count == 5", page.locator("details.venture").count() == 5)
    check("desktop: details.venture[open] count == 0", page.locator("details.venture[open]").count() == 0)

    rail_pos = page.eval_on_selector(".rail", "el => getComputedStyle(el).position")
    check("desktop: rail position sticky", rail_pos == "sticky", f"got {rail_pos}")
    rail_frac = page.eval_on_selector(".rail", "el => el.getBoundingClientRect().width / 1280")
    check("desktop: rail width/1280 in [0.29,0.33]", 0.29 <= rail_frac <= 0.33, f"got {rail_frac:.3f}")

    # v2 skim path is AI Portfolio (5 collapsed rows) before Storytelling, not Skills.
    ventures_top = page.eval_on_selector("#ventures", "el => el.getBoundingClientRect().top")
    check("desktop: #ventures (AI Portfolio) top < 900 (skim path above the fold)", ventures_top < 900, f"got {ventures_top:.0f}px")

    # v2 content-completeness (the v1 rejection was thin content):
    check("desktop: details.career-item count == 6", page.locator("details.career-item").count() == 6,
          f"got {page.locator('details.career-item').count()}")
    check("desktop: contact email link rendered on page", page.locator("a[href^='mailto:']").count() >= 1)
    check("desktop: contact tel link rendered on page", page.locator("a[href^='tel:']").count() >= 1)
    check("desktop: 3 Moth YouTube links", page.locator(".story-win .w-yt").count() == 3,
          f"got {page.locator('.story-win .w-yt').count()}")
    check("desktop: speaking statline present (4 stat pairs)", page.locator(".stat-row .stat-pair").count() == 4,
          f"got {page.locator('.stat-row .stat-pair').count()}")
    check("desktop: signature-strengths Top-5 strip present", page.locator(".sig-skills .sig-row").count() == 5,
          f"got {page.locator('.sig-skills .sig-row').count()}")

    # Index-based targeting from resume.json order: has_text matches body
    # text too (the iLink thesis contains "WayFact"), so name filters collide.
    names = [v["name"] for v in DATA["ventures"]]
    wayfact_meta = page.locator("details.venture").nth(names.index("WayFact")).locator("summary .venture-meta").inner_text()
    check("desktop: WayFact meta == [private beta]", wayfact_meta.strip() == "[private beta]", f"got {wayfact_meta!r}")
    ilink_meta = page.locator("details.venture").nth(names.index("iLink Tools")).locator("summary .venture-meta").inner_text()
    check("desktop: iLink meta contains 16", "16" in ilink_meta, f"got {ilink_meta!r}")

    check("desktop: .m-bar hidden at >= 1024", page.locator(".m-bar").is_hidden())

    page.evaluate("document.querySelectorAll('details.venture').forEach(d => d.open = true)")
    page.wait_for_timeout(400)
    check("desktop expanded: zero console errors", len(errors) == 0, "; ".join(errors[:5]))
    no_h_overflow = page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    check("desktop expanded: no horizontal overflow", no_h_overflow)

    browser.close()


def webkit_launch_or_fallback(p):
    """Launch local webkit, or fall back to the official Playwright Linux
    container. On Trunk (macOS 26), headless webkit hangs forever in the
    NSApp event loop when launched from an SSH session - both cached
    builds, sandboxed or not. The gate exists to exercise the WebKit
    ENGINE (backdrop-filter, sticky handoff, safe-area quirks), so the
    Linux build of the same engine is an honest substitute. Returns a
    browser or None (None = the container run already reported results).
    """
    try:
        return p.webkit.launch(headless=True, timeout=20000)
    except Exception as exc:
        print(f"  note: local webkit unusable ({str(exc).splitlines()[0][:80]}); "
              "falling back to Playwright Linux container")
        result = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{REPO_ROOT}:/repo", "-w", "/repo",
             "-e", "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
             "mcr.microsoft.com/playwright/python:v1.58.0-noble",
             "bash", "-c",
             "pip install --quiet --break-system-packages playwright==1.58.0 >/dev/null 2>&1 "
             "&& python3 resume/verify.py --webkit-only"],
        )
        check("mobile: webkit leg (containerized)", result.returncode == 0,
              f"container exit {result.returncode}")
        return None


def mobile_gates(p):
    print("== mobile 375x812 WEBKIT ==")
    browser = webkit_launch_or_fallback(p)
    if browser is None:
        return
    context = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=3, is_mobile=True)
    page, errors, bad = new_instrumented_page(context)
    page.goto(BASE, wait_until="networkidle")

    check("mobile: zero console errors", len(errors) == 0, "; ".join(errors[:5]))
    check("mobile: .m-identity visible", page.locator(".m-identity").is_visible())
    check("mobile: .rail display none", page.locator(".rail").is_hidden())

    identity_h = page.eval_on_selector(".m-identity", "el => el.getBoundingClientRect().height")
    page.evaluate(f"window.scrollTo(0, {int(identity_h) + 300})")
    page.wait_for_timeout(300)
    mbar_top = page.eval_on_selector(".m-bar", "el => el.getBoundingClientRect().top")
    check("mobile: .m-bar sticky handoff (top == 0 after scroll)", abs(mbar_top) < 1, f"got {mbar_top:.1f}px")

    cred_fits = page.eval_on_selector(".m-bar .cred", "el => el.scrollWidth <= el.clientWidth")
    check("mobile: .m-bar .cred not clipped (scrollWidth <= clientWidth)", cred_fits)

    no_h_overflow = page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    check("mobile: no horizontal overflow", no_h_overflow)

    heights = page.eval_on_selector_all(
        "details.venture > summary", "els => els.map(el => el.getBoundingClientRect().height)"
    )
    check(
        "mobile: all 5 summaries >= 44px tap target",
        len(heights) == 5 and all(h >= 44 for h in heights),
        f"got {[round(h) for h in heights]}",
    )

    browser.close()


def js_off_gates(p):
    print("== JS disabled, chromium ==")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900}, java_script_enabled=False)
    page = context.new_page()
    page.goto(BASE, wait_until="load")

    check("js-off: all 5 venture details present", page.locator("details.venture").count() == 5)
    check("js-off: all 6 career details present", page.locator("details.career-item").count() == 6)

    content = page.content()
    missing = [v["name"] for v in DATA["ventures"] if v["body"] not in content]
    check("js-off: every venture body text in DOM source", not missing, f"missing: {missing}")

    mantra = DATA["storytelling"]["mantra"]
    check("js-off: storytelling mantra in DOM source", mantra in content)

    # text_content, not inner_text: .thesis sits inside a closed <details>,
    # and inner_text of layout-hidden content is empty by spec.
    thesis = page.locator(".thesis").text_content().strip()
    check(
        "js-off: .thesis == 'SignalScope graduated into WayFact.'",
        thesis == "SignalScope graduated into WayFact.",
        f"got {thesis!r}",
    )

    browser.close()


def pdf_gates():
    print("== PDF (ATS twin) ==")
    if not PDF_PATH.exists():
        check("pdf: file exists", False, str(PDF_PATH))
        return
    text = subprocess.run(
        ["pdftotext", "-layout", str(PDF_PATH), "-"], capture_output=True, text=True, check=True
    ).stdout

    # Case-insensitive: the PDF header renders the name uppercase (CHRIS J SHANKU)
    # to match the source doc; the ATS-relevant fact is the text is present.
    for needle in ["Chris J Shanku", "Microsoft", "iLink", "Valorem", "Avanade",
                   "University of Georgia", "WayFact", "16", "private beta",
                   "SignalScope graduated into WayFact."]:
        check(f"pdf: contains {needle!r}", needle.lower() in text.lower())
    check("pdf: does NOT contain bracketed '[private beta]'", "[private beta]" not in text)
    check(
        "pdf: 'Experience' appears before 'AI Portfolio' (ATS DOM order)",
        "Experience" in text and "AI Portfolio" in text and text.index("Experience") < text.index("AI Portfolio"),
    )
    check("pdf: no em dash", "—" not in text)
    check("pdf: no en dash", "–" not in text)

    pages = int(
        [l for l in subprocess.run(["pdfinfo", str(PDF_PATH)], capture_output=True, text=True, check=True)
         .stdout.splitlines() if l.startswith("Pages:")][0].split()[-1]
    )
    check("pdf: page count >= 2 (full-classic)", pages >= 2, f"got {pages}")


def main():
    webkit_only = "--webkit-only" in sys.argv
    server = start_server()
    try:
        with sync_playwright() as p:
            if webkit_only:
                mobile_gates(p)
            else:
                desktop_gates(p)
                mobile_gates(p)
                js_off_gates(p)
        if not webkit_only:
            pdf_gates()
    finally:
        server.shutdown()

    print(f"\n{len(passes)} passed, {len(failures)} failed")
    if failures:
        print("FAILED gates:")
        for f in failures:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
