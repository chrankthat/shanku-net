# code-demo — Grove Sprint Close

HyperFrames composition showing an animated terminal sequence of a TheGrove sprint close. 10-second scene, 1920x1080, no audio.

## Quick render

```bash
cd shanku-net/templates/code-demo
npx hyperframes render
# output: renders/code-demo_<timestamp>.mp4
```

For final delivery quality:
```bash
npx hyperframes render --quality high --fps 60 --output renders/final.mp4
```

## Brand tokens used

| Token | Value | Role |
|-------|-------|------|
| `--bg` | `#0D1F1C` | Canvas background |
| `--accent` | `#C28A05` | Grove Gold — brand watermark, gate lines, close line |
| `--text` | `#F0EDE6` | Terminal body text |
| Terminal chrome | `#070F0E` | Window background |
| Success green | `#3DB065` | Checkmarks |

Fonts: JetBrains Mono (auto-embedded by HyperFrames), system-ui (sans headings/watermark).

## Customization

- **Sprint name**: edit line `l1` content (`/sprint shanku-hyperframes-foundation`)
- **Work items**: edit `l3-l8` pairs (amber arrow + green check)
- **Gate results**: edit `l9` and `l10` (amber `.l-gate` lines)
- **Close line**: edit `l11` - sprint number and date
- **Duration**: change `data-duration="10"` on the scene div; adjust GSAP timeline positions accordingly

## Lint and inspect

```bash
npx hyperframes lint          # 0 errors expected; 2 warnings are known/acceptable
npx hyperframes inspect       # visual layout check
```
