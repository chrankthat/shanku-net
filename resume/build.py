#!/usr/bin/env python3
"""Generate resume/index.html + the ATS PDF twin from resume/resume.json.

Both outputs are GENERATED and committed - never hand-edit them.
Cloudflare Pages is a dumb static host; the repo must contain the exact
bytes served, so the generator runs at edit time, not deploy time.

Usage:
    python3 resume/build.py              # render index.html + PDF; exit 1 on any TODO:
    python3 resume/build.py --check      # render to memory, diff vs disk; exit 1 on divergence
    python3 resume/build.py --allow-todo # dev escape hatch; never in the committed flow
    python3 resume/build.py --no-pdf     # skip chromium (fast loop)

Determinism is load-bearing: --check is the divergence gate and it dies
the day it fails on a clean run. last_updated comes from resume.json,
NEVER datetime.now(). PDF is compared by extracted text, never bytes
(chromium stamps /CreationDate). No set() in any render path.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "resume.json"
SCHEMA_PATH = ROOT / "resume.schema.json"

# Voice gate: no em dashes, no en dashes, no emoji, anywhere.
# U+2192 (->, the Microsoft career role arrow) is the one deliberate
# allowlisted arrow - it is a designed glyph, not prose punctuation.
BANNED_DASHES = {"—": "em dash (U+2014)", "–": "en dash (U+2013)"}
ALLOWED_ARROWS = {"→"}
EMOJI_RANGES = (
    (0x1F000, 0x1FFFF),  # emoji, symbols, pictographs
    (0x2600, 0x27BF),    # misc symbols + dingbats
    (0x2B00, 0x2BFF),    # misc symbols and arrows (block includes emoji stars)
    (0xFE00, 0xFE0F),    # variation selectors
)


def walk_strings(node, path="$"):
    """Yield (json_path, string_leaf) pairs, depth-first, insertion order."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk_strings(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def gate_todo(data):
    offenders = [p for p, s in walk_strings(data) if s.startswith("TODO:")]
    if offenders:
        print("TODO gate FAILED - resume.json still contains sentinel facts:", file=sys.stderr)
        for p in offenders:
            print(f"  {p}", file=sys.stderr)
        print("Chris fills these. Never invent replacements. (--allow-todo is the dev escape hatch.)", file=sys.stderr)
        return False
    return True


def _char_offenses(text):
    for ch in text:
        if ch in BANNED_DASHES:
            yield BANNED_DASHES[ch]
        elif ch in ALLOWED_ARROWS:
            continue
        else:
            cp = ord(ch)
            for lo, hi in EMOJI_RANGES:
                if lo <= cp <= hi:
                    yield f"emoji/symbol U+{cp:04X}"
                    break


def gate_voice(data, rendered_html=None):
    failures = []
    for path, s in walk_strings(data):
        for offense in _char_offenses(s):
            failures.append(f"  {path}: {offense}")
    if rendered_html is not None:
        for offense in _char_offenses(rendered_html):
            failures.append(f"  <rendered index.html>: {offense}")
    if failures:
        print("Voice gate FAILED - banned characters found:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return False
    return True


def gate_ledger(data):
    ledger = data["ledger"]["tools_built"]
    if ledger["automated"] is not False:
        print("Ledger gate FAILED: ledger.tools_built.automated must be exactly false. "
              "The 16 is a hand-curated editorial roster - see TheGrove wiki/decisions/ad192.md. "
              "Do not automate it. Do not 'correct' it to 17.", file=sys.stderr)
        return False
    # Only the iLink Tools venture is bound to the tools ledger. Other
    # ventures may carry their own count signals (e.g. HITL episode count).
    ilink = [v for v in data["ventures"] if v["name"] == "iLink Tools"]
    if not ilink:
        print("Ledger gate FAILED: no 'iLink Tools' venture found; its ledger total is a design requirement.", file=sys.stderr)
        return False
    signal = ilink[0]["signal"]
    if signal["type"] != "count" or signal["value"] != ledger["count"]:
        print(f"Ledger gate FAILED: iLink Tools signal {signal!r} does not carry "
              f"ledger.tools_built.count {ledger['count']}.", file=sys.stderr)
        return False
    return True


def gate_rail_ceiling(data):
    ok = True
    creds = data["credentials"]
    motto = data["identity"]["motto"]
    if len(creds) > 3:
        print(f"Rail ceiling gate FAILED: {len(creds)} credential rows (max 3). "
              "A fourth row changes the rail math the design was verified against.", file=sys.stderr)
        ok = False
    if len(motto) > 40:
        print(f"Rail ceiling gate FAILED: motto is {len(motto)} chars (max 40).", file=sys.stderr)
        ok = False
    # AC-3: the contact block is designed for exactly 3 rows (email/phone/linkedin).
    # A sweep never touches contact, but assert the designed shape so the rail math
    # the design was verified against cannot silently drift.
    contact = data["contact"]
    for field in ("email", "phone", "linkedin"):
        if not contact.get(field):
            print(f"Rail ceiling gate FAILED: contact.{field} is empty; the rail contact block "
                  "is designed for exactly 3 rows (email, phone, linkedin).", file=sys.stderr)
            ok = False
    return ok


def gate_content(data, rendered_html):
    """Content-completeness gates (dynamic-resume-v2, EC-2..EC-6).

    v1 shipped 28 green ECs with placeholder-depth content: 2 career roles,
    one-line venture bodies, no education/certs/storytelling. Chris rejected
    it as junior-analyst weak. These predicates make "countable but thin"
    fail loud - a gate must prove real depth, not mere non-emptiness.
    """
    ok = True

    # EC-2: 6 career roles; recency-weighted bullets; every bullet >= 60 chars.
    rows = data["career"]["rows"]
    if len(rows) != 6:
        print(f"Content gate FAILED: career has {len(rows)} rows (expected exactly 6). "
              "The real resume is 16 years / 6 roles - the v1 miss was 2 roles.", file=sys.stderr)
        ok = False
    for idx, r in enumerate(rows):
        need = 3 if idx < 3 else 2  # 3 most-recent roles fuller; condensed roles >= 2
        nb = len(r.get("bullets", []))
        if nb < need:
            print(f"Content gate FAILED: career[{idx}] {r.get('company')!r} has {nb} bullets "
                  f"(needs >= {need}; 'non-empty' alone was gameable by one 4-word bullet).", file=sys.stderr)
            ok = False
        for b in r.get("bullets", []):
            if len(b) < 60:
                print(f"Content gate FAILED: career[{idx}] {r.get('company')!r} bullet is "
                      f"{len(b)} chars (min 60): {b!r}", file=sys.stderr)
                ok = False

    # Professional summary present (sourced from resume.shanku.net; renders in the PDF).
    if not data.get("summary"):
        print("Content gate FAILED: summary is empty.", file=sys.stderr)
        ok = False

    # EC-3: education, certifications, storytelling non-empty.
    if not data.get("education"):
        print("Content gate FAILED: education is empty.", file=sys.stderr)
        ok = False
    if not data.get("certifications"):
        print("Content gate FAILED: certifications is empty.", file=sys.stderr)
        ok = False
    st = data.get("storytelling") or {}
    if not (st.get("moth") and st.get("speaking") and st.get("mantra")):
        print("Content gate FAILED: storytelling must carry moth + speaking + mantra.", file=sys.stderr)
        ok = False

    # EC-4: every venture body is a real paragraph (>= 200 chars), not an inherited one-liner.
    for v in data["ventures"]:
        body = v.get("body", "")
        if len(body) < 200:
            print(f"Content gate FAILED: venture {v.get('name')!r} body is {len(body)} chars "
                  "(min 200). The v1 failure was one-line placeholder bodies ported as the contract.", file=sys.stderr)
            ok = False

    # ship_log enabled in v2 (entries arrive via the sweep/publisher).
    if not data["ship_log"].get("enabled"):
        print("Content gate FAILED: ship_log.enabled must be true in v2.", file=sys.stderr)
        ok = False

    # EC-5: contact email/phone/linkedin actually rendered into the page HTML,
    # not just present in resume.json (the v1 gap - contact never rendered on-page).
    if rendered_html is not None:
        for token in (data["contact"]["email"], data["contact"]["phone"], "linkedin"):
            if token not in rendered_html:
                print(f"Content gate FAILED: contact token {token!r} not found in rendered index.html.", file=sys.stderr)
                ok = False

    return ok


def _tel_href(phone):
    digits = "".join(c for c in phone if c.isdigit())
    return f"+1{digits}" if digits else ""


def _sparkline_points(entries):
    """Compressed echo of the ship log for the rail sparkline. Shape derives
    from entry count: oldest (left, low) -> newest (right, high)."""
    n = len(entries)
    if n == 0:
        return ""
    if n == 1:
        return "200,4"
    pts = []
    for i in range(n):
        x = round(200 * i / (n - 1))
        y = round(26 - 22 * i / (n - 1))
        pts.append(f"{x},{y}")
    return " ".join(pts)


def gate_schema(data):
    try:
        import jsonschema
    except ImportError:
        print("Schema gate FAILED: jsonschema is not installed, so resume.schema.json "
              "cannot be enforced. Its whole purpose is making Sprint 2 typos fail loud; "
              "a silent skip here is the 'system that lies' pattern. "
              "Install it: pip3 install jsonschema", file=sys.stderr)
        return False
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        print(f"Schema gate FAILED: {exc.message} at {'/'.join(str(p) for p in exc.absolute_path)}", file=sys.stderr)
        return False
    return True


def render(data, source_sha):
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(default=True, default_for_string=True),
        keep_trailing_newline=True,
    )
    certs = data.get("certifications", [])
    ctx = dict(
        data,
        source_sha=source_sha,
        tel_href=_tel_href(data["contact"]["phone"]),
        sparkline_points=_sparkline_points(data["ship_log"]["entries"]),
        cert_total=sum(len(g["items"]) for g in certs),
        cert_issuers=len(certs),
    )
    page_html = env.get_template("page.html.j2").render(**ctx)
    pdf_html = env.get_template("pdf.html.j2").render(**ctx)
    return page_html, pdf_html


def render_pdf(pdf_html, out_path):
    """Hermetic chromium print: set_content only - no file://, no network."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(pdf_html, wait_until="load")
        page.pdf(
            path=str(out_path),
            format="Letter",
            margin={"top": "0.6in", "bottom": "0.6in", "left": "0.6in", "right": "0.6in"},
            print_background=False,
        )
        browser.close()


def pdf_text(pdf_path):
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="diff fresh render against committed artifacts")
    parser.add_argument("--allow-todo", action="store_true", help="dev escape hatch: render with TODO sentinels present")
    parser.add_argument("--no-pdf", action="store_true", help="skip the chromium PDF render")
    args = parser.parse_args()

    raw = DATA_PATH.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    source_sha = hashlib.sha256(raw).hexdigest()

    if not gate_schema(data):
        return 1
    if not args.allow_todo and not gate_todo(data):
        return 1
    if not gate_ledger(data):
        return 1
    if not gate_rail_ceiling(data):
        return 1

    page_html, pdf_html = render(data, source_sha)

    if not gate_voice(data, rendered_html=page_html):
        return 1
    if not gate_content(data, rendered_html=page_html):
        return 1

    html_path = ROOT / "index.html"
    pdf_path = ROOT / data["meta"]["pdf_filename"]

    if args.check:
        ok = True
        if not html_path.exists():
            print("--check FAILED: index.html does not exist; run build.py first", file=sys.stderr)
            ok = False
        elif html_path.read_bytes() != page_html.encode("utf-8"):
            print("--check FAILED: index.html on disk diverges from a fresh render of resume.json", file=sys.stderr)
            ok = False
        if not args.no_pdf:
            if not pdf_path.exists():
                print(f"--check FAILED: {pdf_path.name} does not exist; run build.py first", file=sys.stderr)
                ok = False
            else:
                with tempfile.TemporaryDirectory() as tmp:
                    fresh_pdf = Path(tmp) / "fresh.pdf"
                    render_pdf(pdf_html, fresh_pdf)
                    if pdf_text(fresh_pdf) != pdf_text(pdf_path):
                        print(f"--check FAILED: {pdf_path.name} extracted text diverges from a fresh render "
                              "(compared as text, never bytes - chromium stamps /CreationDate)", file=sys.stderr)
                        ok = False
        if ok:
            print("--check OK: committed artifacts match resume.json")
            return 0
        return 1

    html_path.write_bytes(page_html.encode("utf-8"))
    print(f"wrote {html_path}")
    if not args.no_pdf:
        render_pdf(pdf_html, pdf_path)
        print(f"wrote {pdf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
