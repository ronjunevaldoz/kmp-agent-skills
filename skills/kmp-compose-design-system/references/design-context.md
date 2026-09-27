# Design Context: PRODUCT.md and DESIGN.md

Part of `kmp-compose-design-system`. Load this file when working on: design context,
PRODUCT.md, DESIGN.md, or before designing or changing any screen.

The idea is adapted from Impeccable ([pbakaus/impeccable](https://github.com/pbakaus/impeccable),
Apache-2.0): durable product and design context lives in files the agent reads before UI
work, instead of being re-explained in every prompt.

---

## Read before UI work

Before designing a new screen or changing an existing one, read:

| File | Answers | Owner |
|---|---|---|
| `PRODUCT.md` (project root) | Who uses it, for what, under which conditions, which principles break ties | Product/team; kept current by `kmp-project-docs-maintainer` |
| `docs/design-system.md` | Component prefix, token names and values, known deviations | This skill (`references/design-system-template.md`) |
| `:core:designsystem` `tokens/` | The normative token values | Code — always wins over any doc |

If `PRODUCT.md` is missing, ask at most three focused questions and write it. Don't invent
users or principles; if you must infer a fact, mark it `(inferred)` so the team confirms it.

## PRODUCT.md template

Durable facts only — no feature specs, page copy, or roadmap. Keep it under a page.

```markdown
# Product

## Platform
android, ios, desktop, web (wasm) — only the targets that ship.

## Users
Who uses it, where, on which device, how often. One paragraph.

## Product Purpose
The job the product does for them, in one or two sentences.

## Operating Context
Conditions that shape the UI: one-handed on a phone, glanced at between tasks,
hours at a desk, poor connectivity.

## Brand Commitments
Constraints the visual system must keep, e.g. "sharp corners", "one accent color",
"no gradients".

## Product Principles
3–5 tie-breakers, e.g. "One primary action per screen." "Never hide the price."

## Accessibility & Inclusion
Contrast target, font scaling to 200%, reduced motion, languages and RTL.
```

How it changes design decisions:
- **Operating Context** sets density and target size: glanced-at mobile flows get fewer,
  larger controls; desk-bound admin tools can be denser.
- **Product Principles** decide conflicts ("one primary action" settles which button is
  primary).
- **Accessibility & Inclusion** feeds `kmp-compose-accessibility` and
  `rememberReduceMotion()` in `kmp-compose-animation`.

## DESIGN.md — export only, never a second source

[DESIGN.md](https://github.com/google-labs-code/design.md) (Google, Apache-2.0) is a
portable format that design tools and agents read: YAML frontmatter with tokens
(`colors`, `typography`, `rounded`, `spacing`, `components`), then up to eight body
sections in fixed order — Overview, Colors, Typography, Layout, Elevation & Depth,
Shapes, Components, Do's and Don'ts.

This skill already has two sources — the Kotlin tokens (normative) and
`docs/design-system.md` (human reference). Don't hand-maintain a third copy.

- **Create DESIGN.md only if the team uses a DESIGN.md-aware tool** (Google Stitch,
  Impeccable, another agent that reads it).
- **Generate it from `tokens/`**, and regenerate whenever tokens change. First line:
  `<!-- Generated from :core:designsystem tokens — edit the tokens, not this file. -->`
- **Units:** the spec has no `dp`/`sp`; write them as `px` (each is its platform's
  density-independent unit).
- **Colors:** hex from `Color(0xAARRGGBB)` as `#RRGGBB`, or `#RRGGBBAA` when alpha isn't `FF`.
- **Scale keys keep project names** (`surfaceVariant`, `onPrimary`) — don't rename to
  another system's defaults.
