# Changelog

All notable changes to this project are recorded here. Dates are absolute (YYYY-MM-DD).

## 2026-06-27

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
