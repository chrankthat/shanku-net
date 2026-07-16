# /resume/ - generated dossier page

**`index.html` and `chris-shanku-resume.pdf` are GENERATED. Never hand-edit them.**
Edit `resume.json` (or the templates), then rerun the generator. Both artifacts are
committed because Cloudflare Pages is a pure static host - the repo must contain the
exact bytes served.

```
python3 resume/build.py              # render index.html + PDF; exits 1 on any TODO: sentinel
python3 resume/build.py --check      # verify committed artifacts match resume.json (CI-style gate)
python3 resume/build.py --allow-todo # dev escape hatch; never in the committed flow
python3 resume/build.py --no-pdf     # skip chromium (fast loop)
python3 resume/verify.py             # browser gates: headless chromium + webkit + JS-off + PDF
```

## Rules that look arbitrary but are not

- **Do NOT import `css/main.css` here.** It pulls `base.css` + `layout.css`, which
  silently destroy this layout (`p{max-width:65ch}`, the `h1` clamp, `a{color:accent}`,
  `section{padding-block:6rem}`). The page imports `../css/tokens.css` + `resume.css`
  only. See TheGrove `wiki/decisions/ad192.md`.
- **The `16` in the iLink Tools ledger is hand-curated and must never be automated.**
  It is an editorial roster (13 public + iExpense + Ascent + OnePager), not derivable
  from ilink-tools `tools.json`. `ledger.tools_built.automated` is pinned `false` and
  `build.py` fails the build if anything flips it. Do not "correct" the count.
- **`last_updated` comes from `resume.json`, never `datetime.now()`.** Determinism is
  what keeps `--check` alive; the day it fails on a clean run, the divergence gate dies.
- **The ship log + rail sparkline are disabled** (`ship_log.enabled: false`) until the
  entries are real, repo-derived facts. Sprint 2 populates them.
- The page ships `noindex, nofollow` and is unlinked from the site nav. Live-but-unlisted
  is a deliberate posture during a job search.

## Layout provenance

Ported from TheGrove `docs/design/2026-07-16-dynamic-resume/direction-b.html`
("The Dossier"): sticky desktop rail carries pedigree; ventures are a hairline-ruled
native `<details>` ledger, all collapsed by default, readable with JS off.
Design record: TheGrove `docs/design/2026-07-16-dynamic-resume/decision.md`.
