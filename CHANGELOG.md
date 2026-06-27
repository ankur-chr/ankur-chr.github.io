# Changelog

All notable changes to this project are recorded here. Dates are absolute (YYYY-MM-DD).

## 2026-06-27

### Renamed `essay.html` → `writing.html` for a more professional URL

The long-form piece now lives at `https://ankur-chr.github.io/writing.html`, matching its
"Writing" nav label. `git mv` plus repointed every inbound link (nav across `index.html`,
`aether.html`, `aquarium.html`, `inside-the-model/index.html`, the two home-page CTAs), and
updated the page's own `og:url` and active self-link. Verified live: `writing.html` resolves 200
from every page; no stale `essay.html` references remain. (Pre-launch, so the old URL was never
public — it now 404s rather than redirecting.)

Also fixed the page's top-left masthead: it read the bare word "Writing", which duplicated the
active "Writing" nav pill and looked off. It now shows the author wordmark **"Ankur Chrungoo"**
(linking home), matching the site convention where the masthead carries identity, not the section
label.

### Clean flagship URL + launch-readiness fixes (demo relocation, `og:url`, runbook)

Prep for the Hacker News / social launch: gave the flagship demo a clean, shareable URL and
removed the rough edges that would have hurt link previews and the publish flow.

- **Relocated the demo to a clean path.** `inside-the-model/web/world-inside.html` →
  `inside-the-model/index.html`, so the canonical URL is now
  `https://ankur-chr.github.io/inside-the-model/` instead of the deep
  `…/inside-the-model/web/world-inside.html`. This is a *real* relocation (not a redirect) so
  social scrapers see the `og:` tags directly — a redirected URL would have rendered a blank
  X/LinkedIn card. The model fetch is now `./web/model.json` (weights stay in `web/`, alongside
  `runtime_test.js`); the demo's own nav/byline links rebased from `../../` to `../`.
- **Old URL still resolves.** `inside-the-model/web/index.html` now redirects up to the clean
  path (with a `rel=canonical`), so any pre-existing `…/web/` link lands on the demo.
- **Added the missing `og:url`** (+ `og:type`) to the demo page — it was the only page lacking a
  canonical URL, which would have broken link-preview cards on X/LinkedIn.
- **Repointed every inbound link** to the clean path: nav + hero CTAs + the home iframe across
  `index.html`, `essay.html`, `aether.html`, `aquarium.html`, plus the `README.md` demo link.
- **Rewrote the stale `PUBLISH.md` runbook** to match reality: the repo is the user-pages repo
  `ankur-chr.github.io` (serves at root, no custom domain / no `CNAME`), placeholders are already
  resolved, and the HN submit URL is the clean `inside-the-model/` path.
- **Verified live** (local preview): both clean and old `/web/` URLs return 200, the model loads
  with a clean console, and every cross-page link resolves 200 in both directions
  (root ⇄ demo one folder deep).

### Credibility pass on copy — grounded the over-stated claims (`index.html`, `essay.html`, `world-inside.html`)

Aligned the on-page wording with the tightened launch copy, removing anthropomorphic
intent and over-claims while keeping the copy approachable for non-technical readers:

- **Dropped "secretly"** — the demo lede now reads the model "built a map of its world inside —
  all on its own," which describes emergence without implying the model *intended* to hide anything.
- **"acts on the lie" → "acts on the false belief"** in the demo's main claim paragraph and the
  essay's "Now lie to it" section, and the demo lede's "follow the lie" → "follow the false belief."
  The playful uses of "lie" (the essay's *"Now lie to it"* heading, the interactive flash microcopy,
  and a JS code comment) are intentionally kept.
- **Stopped over-stating Gurnee & Tegmark** — "hold a literal, linear map of Earth" / "literal, linear
  map of the Earth" → "carry linear maps of real-world place and time," framed as a research finding.
  The "next in series" teasers (`index.html`, `world-inside.html`) follow the same wording.

Text-only edits; verified the demo still boots and runs (no console errors, model reaches ACT I).

### Privacy-friendly visitor analytics (GoatCounter)

**Cookieless page-visit tracking added to all five pages** — `index.html`, `essay.html`,
`aether.html`, `aquarium.html`, and `inside-the-model/web/world-inside.html` each load the
GoatCounter snippet (endpoint `https://ankur-chr.goatcounter.com/count`). GoatCounter is
open-source, cookie-free, and needs no GDPR consent banner — a better fit for the HN/privacy
audience than Google Analytics. Stats are viewed at the `ankur-chr.goatcounter.com` dashboard.

**Self-exclusion built in** — the snippet sets `no_onload` (skips the auto pageview) when the
host is `localhost`/`127.0.0.1` *or* when `localStorage` key `skipgc === 't'`. Local dev is
never counted; setting the `skipgc` flag once per browser on the live origin excludes the owner
across the whole site (localStorage is shared per-origin, so one flag covers all pages).

The `inside-the-model/web/index.html` redirect stub is intentionally left untracked — it does an
instant `meta refresh` to `world-inside.html` (which is tracked), so counting it would double-count.

### Demo intro clarity + masthead (`world-inside.html`)

**Lede that leads the page** — replaced the H1 sub-line with a left-aligned `.lede` intro
paragraph matching the ÆTHER / Aquarium pattern, so the demo opens with a single descriptive
line a first-time visitor reads before anything else: *"A model that only ever read an agent's
movement symbols secretly built a map of its world inside. Here you read what it sees, decode
that map from its mind, then edit it — and watch its behavior follow the lie."* Plain prose with
two bold anchors (movement symbols, map of its world) — no decorative chips, low cognitive load.

**Masthead kicker bridges the naming** — added an `INSIDE THE MODEL · #1` eyebrow above the
`The World Inside` title. The page title and its nav tab share no words ("The World Inside" vs
"Inside the Model"); the kicker surfaces the series name so the active tab and the masthead agree,
and it matches the footer's "Inside the Model #1". Removed the old subtitle that duplicated the lede.

### Site-wide navigation + responsiveness

**Unified nav across all five pages** — one consistent bar everywhere:
`Home · Inside the Model · ÆTHER · Aquarium · Writing`, with the current page marked
via `aria-current="page"` and a subtle active style.
- `aether.html` had **no nav at all** — added it (in a new `.hdr-right` group beside the
  CHANNEL OPEN pill).
- `aquarium.html` linked only Home + ÆTHER; `world-inside.html` was missing itself +
  Writing; `index.html` and `essay.html` were brought onto the same pattern.

**Consistent header alignment across all pages** — every page now uses the same
`header.top` structure: page-relevant brand on the left, nav right-aligned to the container
edge on the same row. `essay.html` previously had a lone left-aligned nav with no header —
it now has a "Writing" brand + right-aligned nav like the rest. `aether.html`'s CHANNEL OPEN
status pill moved under the brand subtitle so the nav sits top-right (was sharing the right
edge with the pill). Standardized `.nav` flex container (gap 8, wrap, right-justify) and the
`aria-current` active style site-wide. Branding stays page-relevant: personal name on Home
only, project names on the demos, "Writing" on the essay.

**Quiet personal byline on demo pages** — `world-inside`, `aether`, `aquarium` each gained
a footer byline `Built by Ankur Chrungoo · more projects` (links to Home). Project title
stays the headline so the demos read artifact-first (HN-safe), not promotional.

**Demo first-impression clarity** (`world-inside.html`) — for the HN front door:
- **Grounded the scenario in Act I.** The narration now states the toy world up front — an
  agent wandering a tiny grid with a hidden lamp, and that the model only ever sees the
  move-trail (↑ ↓ → ←) plus a 🔦 blip when the lamp is in view — instead of leaving a
  first-time visitor to infer it. Also explains the 🔦 stream symbol that was previously
  unexplained.
- **Unified the lamp glyph.** The lamp was rendered as 👁 (eye) in the move-stream and
  lamp-sense readout but as 🔦 (flashlight) on the grid and in all narration — two faces for
  one concept. Now 🔦 everywhere (`TOKCH.LAMP`, lamp-sense readout, tooltip).

**Title aligned to the theme** — `world-inside.html`'s `<title>` and `og:title` now lead
with "Inside the Model" (was "The World Inside") so the HN tab + link preview match the
submission and the nav/brand. The on-page H1 stays "The World Inside" (the demo's own name;
footer frames it as "Inside the Model #1").

**Navigation responsiveness fix** — the demo pages run continuous heavy loops
(`world-inside`: a pure-JS transformer on `setInterval`; `aquarium`: a live training loop)
that saturated the main thread and made clicking away feel "stuck." Added `pagehide` +
`visibilitychange` handlers that stop those loops the instant you leave or background the
tab, so navigation responds immediately. `aether`'s work is on-demand (per keystroke), so
it needed no loop teardown.

### Pre-launch cleanup
- Removed a stale `TODO: replace with your real profiles` comment in `index.html`;
  the GitHub/LinkedIn profile links beneath it were already correct.

### Brand assets — logo, favicon, social card

**New "Inside the Model" logo** (`assets/inside-the-model-logo.svg` / `.png`, 512×512)
- A dark "model" chip containing the world it builds: a coordinate grid, a cyan→violet
  belief-trail, and a reticle-ringed agent node. Works on light/dark and circular crops.
  PNG is the upload for the Buttondown newsletter image.

**Favicon** (`favicon.svg` + `favicon-32.png` + `apple-touch-icon.png`)
- Tab-optimized simplified mark (trail + node, no grid) so it stays legible at 16–32px.
- Wired into all five pages (`index`, `essay`, `aether`, `aquarium`, `world-inside`) via
  absolute root paths, plus `theme-color`.

**Social-share card** (`assets/og-image.svg` / `.png`, 1200×630)
- Branded link-preview image (logo + "Inside the Model" + tagline) for LinkedIn / X / Slack.
- Added `og:image` (+ width/height), `twitter:card=summary_large_image`, and `twitter:image`
  to all five pages. Demo pages (`aether`, `aquarium`, `world-inside`) also gained
  `meta description` + `og:title`/`og:description` so their shares render properly.

### Home (`index.html`) — newsletter & positioning

**Newsletter rebrand → "Inside the Model"**
- The subscribe box is now a named publication ("THE NEWSLETTER · Inside the Model") with a
  clear promise, rather than a generic "get the next one" form. People subscribe to a named
  thing, not to ungrouped personal updates.

**State-of-the-art subscribe flow (no more bare Buttondown page)**
- The form now posts into a hidden iframe (`target="bd-iframe"`) instead of doing a full-page
  POST / popup, so the visitor never leaves the branded site.
- On submit, the form is swapped in-place for a styled confirmation panel that explicitly tells
  the subscriber to **check their inbox and click the confirmation link** (surfaces Buttondown's
  double-opt-in step, which the default flow does not).
- NOTE: the confirmation copy assumes double-opt-in is enabled in the Buttondown dashboard.

**Positioning (umbrella + flagship series)**
- Lightly broadened the hero lede so the *site* reads as the broad practice ("I turn frontier AI
  ideas into things you can see and poke") with **"Inside the Model" as the first series** —
  preserving room for future series without diluting the current focus.
- Added `id="subscribe"` anchor to the newsletter panel so other pages can deep-link to it.

### Essay (`essay.html`)
- Renamed the closing CTA from "Subscribe on the homepage" to **"Subscribe to Inside the Model"**,
  now deep-linking to `index.html#subscribe`, for consistent newsletter branding across pages.


### Essay (`essay.html`)
- Reviewed against the shipped model — every figure (155K params, 98.8% / 100% / 100% /
  99.7%) and all three external citations verified accurate and correctly linked.
- Added a contextual inline link to the live demo inside the "Now lie to it" section, so the
  interactive experience is offered at the moment of peak reader interest (in addition to the
  existing nav link and demo card — all demo links preserved).
- Aligned the regulated-domains line with the homepage's finance-forward framing
  ("In finance, in healthcare, in anything regulated…").

### The World Inside (`inside-the-model/web/world-inside.html`)

**Legibility & explainers**
- Added on-demand explainer tooltips (hover / tap / keyboard-focus) on the key terms —
  "decoded live", the two legend markers, and "lamp-sense" — so the demo can be understood
  without external context and without adding permanent on-screen clutter.

**Grid layout fix**
- Pinned the mind-grid to uniform rows (`grid-template-rows: repeat(7,1fr)`). Previously the
  lamp emoji stretched its row taller than the others, so the percentage-positioned markers and
  arrows drifted off their cells near the lamp. Markers now sit dead-center on every cell.

**Accurate belief read-out**
- The on-screen belief is now decoded by the shipped **49-way linear position classifier**
  (rendered at its expected position), instead of the weaker Ridge regression probe. Live
  accuracy is ~99% exact / 100% within one cell, so the circle genuinely tracks the true square
  and matches the headline "position decodable 98.8%" claim. The classifier is exported from
  `build_model.py` into `model.json`.

**Act III — causal belief edit, live**
- The implanted false memory is now **live dead-reckoning**: the believed cell = true position +
  the implanted offset, so the red belief marker travels alongside the true (blue) agent, offset
  by the lie, as the model keeps navigating.
- The live walk is constrained to keep both the true and believed cells on the grid (offset capped
  so it is always satisfiable), which eliminates the earlier "belief sticks in a corner" artifact.
- The lamp hallucination is now explicit: a pulsing phantom lamp plus a "hallucinating" tag when
  the believed path nears the lamp while the agent is truly far away.
- Belief marker positioned at the continuous (smoothed) coordinate so it glides rather than
  snapping between cells.

**Copy consistency**
- Narration, hints, the legend tooltip, and flash messages updated to describe the live
  dead-reckoning behavior and the classifier-based read-out.

### Offline pipeline (`inside-the-model/offline/build_model.py`)
- Export the linear position classifier (`coef_`, `intercept_`, `classes_`) into `model.json`
  for the in-browser belief read-out. Model weights are unchanged (deterministic seed-0 rebuild);
  all gates re-pass (position 98.8%, legal-moves 100%, belief-edit 100%, hallucination 99.7%).
