# Inside the Model — interactive arguments about what AI is really doing

> Small, rigorous, **playable** demos about what's actually happening inside neural networks.
> No hand-waving, no unreadable math — things you can *see* and *poke*, backed by reproducible evidence.
> Everything runs in your browser. No server. No tracking.

**Live:** [ankur-chr.github.io](https://ankur-chr.github.io/) · by [Ankur Chrungoo](https://www.linkedin.com/in/ankurchrungoo) — principal engineer & AI architect, MSc AI (QMUL)

---

## The flagship: **The World Inside**

A **155,000-parameter** transformer is trained to do exactly one thing — predict the next move-symbol of an agent
wandering a grid (`↑ ↑ → ↓ …`). It is **never** shown a grid, a map, or a coordinate.

Yet to do its job, it secretly **builds a model of the world** and stores it in its activations. This demo:

1. **Reads its mind** — a linear probe lifts the agent's position straight out of the hidden activations, live.
2. **Proves it's used** — the model only ever predicts *legal* moves; it won't "walk through walls."
3. **Edits the belief** — you click a cell to overwrite its sense of place (activation patching), and it
   **acts on the lie** — refusing exits that are only walls *where it thinks it is*, and **hallucinating** a
   landmark that isn't there.

▶ **[Open the live demo](https://ankur-chr.github.io/inside-the-model/web/world-inside.html)** — runs entirely client-side.

## Is it real? (measured on the shipped model)

Every claim is backed by a test that runs **before** any UI was built. Reproduce them with the offline pipeline.

| Question | Result | (chance) |
|---|---|---|
| Did a "blind" next-token model build a world model? | position decodable **98.8%** | 2.0% |
| Does it actually *use* that world model? | predicts only legal moves **100%** | — |
| Does it sense the landmark? | predicts "lamp" when near **100%** | — |
| Can we edit its belief and change behavior? | belief-edit success **100%** | — |
| Can we make it hallucinate on command? | phantom landmark **99.7%** | — |
| Does the in-browser forward pass match PyTorch? | max logit error **1.8e-6** | — |

## Also in here

- **The Glass Aquarium** — two neural agents start with no shared language and **invent one, live**, to win a
  referential game (speaker via REINFORCE, listener via cross-entropy). Emergent communication, trained in your browser.
- **ÆTHER** — a reversible "machine-native" glyph language: lossless to a machine, unreadable to a human.

## How it works (and the science it stands on)

The phenomenon — *next-token predictors spontaneously learn internal world models* — is documented up to frontier scale:

- **Othello-GPT** builds the board from move sequences; a linear probe recovers it and *causal intervention* changes
  its play — [Li et al.](https://arxiv.org/abs/2210.13382), [Neel Nanda](https://www.neelnanda.io/mechanistic-interpretability/othello).
- **Llama-class models** hold a literal, linear **map of Earth** and a timeline of history —
  [Gurnee & Tegmark, "Language Models Represent Space and Time"](https://arxiv.org/abs/2310.02207).
- **Activation patching** is a standard causal-interpretability method for editing internal state.

We use a *tiny* model on purpose: small enough to **prove** end-to-end, and to run **live** in a browser with no server.

## Reproduce it

```bash
cd inside-the-model/offline
pip install -r requirements.txt
python build_model.py        # trains, verifies all gates, exports ../web/model.json
node ../web/runtime_test.js   # Gate 4: JS forward pass == PyTorch (err ~1e-6)
```

- `prove_core.py` — the original P1 proof (world model emerges & is decodable).
- `gate3b_diagnose.py` — the causal-edit (activation-patching) experiments.
- `build_model.py` — trains the shipped model + landmark, verifies gates, exports weights/probe/cell-signatures.

## Tech

Pure static files. The transformer's forward pass is **reimplemented in vanilla JS** (`world-inside.html`) and runs the
exported weights client-side — no backend, no API calls, no dependencies. Hostable on any static host (this repo ships
for GitHub Pages).

## License

[MIT](LICENSE) © 2026 Ankur Chrungoo.
