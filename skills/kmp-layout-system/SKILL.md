---
name: kmp-layout-system
description: >-
  Drafts and maintains KMP screen-layout documentation in docs/layout-system/.
  Produces one markdown spec and SVG wireframe per screen plus a shared component registry.
  Use for new screens, layout changes, layout review, or projects missing layout specs;
  create the documentation before or alongside implementation.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-08-10'
  keywords:
    - layout system
    - wireframe
    - screen layout
    - SVG wireframe
    - component registry
    - layout spec
    - docs layout-system
    - screen structure
    - layout draft
    - layout diagram
    - html wireframe
    - html to compose
    - implement wireframe
    - html mockup to jetpack compose
---

## Purpose

This skill drafts and documents app screens — it is a **living spec**, not a constraint.
Wireframes describe intent before (or alongside) implementation. They are updated as the
design evolves, not frozen once written.

Use this skill to:
- Sketch a new screen before writing a single line of Compose
- Record what a screen looks like after a layout change
- Give the team a shared visual reference that lives in the repo

The skill is **fully generic** — component names, widths, and nav labels all come from
the actual project. Templates use `<placeholders>`; fill them in from the project.

Do NOT use this skill for Compose implementation — use `kmp-compose-adaptive-layout`
for breakpoint-driven responsive layouts.

**Freshness rule:** recheck wireframes whenever a panel is added or removed, navigation
chrome changes, or a modal becomes a full screen.

---

## When to Use This Skill

- New screen being designed — draft before or alongside implementation
- Existing screen layout changes
- Layout review or audit requested
- Project has no `docs/layout-system/` yet

**Trigger automatically on project setup.** If the directory is missing, create it before
finishing any screen implementation task.

**Trigger keywords:** layout system, screen layout, wireframe, layout spec, layout docs,
draft screen, component layout, screen wireframe, layout diagram, and HTML wireframe.

---

## Directory Structure

```
docs/layout-system/
├── _components.md          <- shared component registry (read this first)
├── <screen-name>.md        <- one file per distinct screen
└── <screen-name>.md
```

- Directory: `docs/layout-system/` (kebab-case)
- Screen files: kebab-case, named after the screen (`home.md`, `profile.md`, `feed.md`)
- `_components.md` uses a leading underscore so it sorts first and is clearly a reference

---

## Creating screen files — one file per screen

**Use the script to scaffold each screen** — it writes exactly ONE file per invocation to
`docs/layout-system/<screen>.md`, bootstraps `_components.md` once, and refuses to overwrite
an existing screen file (edit those in place):

```bash
python3 ~/.agents/skills/kmp-layout-system/scripts/create_wireframe.py \
  --screen "Inbox" --pattern A
```

(From inside kmp-agent-skills, use `skills/kmp-layout-system/scripts/create_wireframe.py`.)

**One screen = one invocation = one file.** Never put two screens in one file and never
append a screen to another screen's file. The script seeds the correct section skeleton and
a starting SVG wireframe for the chosen pattern (A/B/C/D) — you then fill in the component
table and edit the SVG's `<rect>`/`<text>` regions to match the real screen.

---

## Slot-Grid Contract → Layout Scaffold

Each generated screen file carries machine-readable frontmatter — the **layout contract**:

```yaml
---
screen: inbox
pattern: A
slots: [nav, side, main]
grid: {compact: [main], medium: [nav, main], expanded: [nav, side, main]}
weights: {nav: fixed, side: 1f, main: 3f}
---
```

- `slots` — the named regions of the screen
- `grid` — which slots render at each `WindowSizeClass` breakpoint (all three required)
- `weights` — from a **closed set only**: `0.5f, 1f, 1.5f, 2f, 2.5f, 3f, 4f, fixed, overlay`.
  Arbitrary floats are rejected by the generator and flagged by the audit (`raw weight literal`).

Compile the contract into a Compose shell:

```bash
python3 ~/.agents/skills/kmp-layout-system/scripts/generate_slot_scaffold.py \
  docs/layout-system/inbox.md --group-id com.example.app --output <ui module path>
```

If the script is not at `~/.agents/skills/` (Codex CLI, Gemini CLI, or a repo-relative
install), use `skills/kmp-layout-system/scripts/generate_slot_scaffold.py`.

This emits `<Screen>Layout.kt`: one `when (windowSizeClass.widthSizeClass)` branch per
breakpoint, each slot a `@Composable () -> Unit` parameter. **You fill slot content only —
never edit the Row/weight structure.** To change the layout, edit the frontmatter and
re-run. This removes all layout guessing: the agent selects from the contract's enumerated
grid instead of judging screen space.

---

## Bootstrap (project has no layout-system yet)

1. Read the project source to identify all existing screens and persistent components.
2. Run `create_wireframe.py` once per screen — it creates `docs/layout-system/` and
   `_components.md` on the first call, then one screen file per subsequent call.
3. Fill in each screen file's component table and SVG wireframe.
4. Link to `docs/layout-system/` from `docs/architecture.md` or `README.md`.

---

## `_components.md` — Component Registry

List every persistent UI component in the project. Fill in real names and real values.

```markdown
# Component Registry

Update this file when a component's dimensions, visibility, or behavior changes.

| Component       | Width / Height | Visibility                  | Platform          | Notes                   |
|-----------------|----------------|-----------------------------|-------------------|-------------------------|
| <Component A>   | <N> dp         | <always / screen X only>    | Both / Android / iOS | <short description>  |
| <Component B>   | <N> dp         | <always / conditional>      | Both              | <short description>     |
| <Component C>   | full / <N> dp  | <phone only / always>       | Both              | <short description>     |
| <Modal / Sheet> | modal          | Overlay on <trigger>        | Both              | No canvas swap.         |
```

---

## SVG Wireframe Format

Each region is an SVG `<rect>` (border + fill, no gradients) with a `<text>`/`<tspan>`
label inside it — real proportions, no monospace-alignment upkeep, viewable inline in
any markdown renderer that supports embedded SVG (GitHub does) with no compile step.

### Rules

- **Canvas: `viewBox="0 0 760 420"`, fixed across every wireframe.** Consistent
  proportions make screens comparable at a glance; don't pick a different canvas size
  per screen.
- **XML-escape every literal `<`/`>` in a label.** A placeholder like `<primary
  content>` must be written `&lt;primary content&gt;` inside `<text>`/`<tspan>` —
  raw `<`/`>` in SVG text content parses as a tag, not text, and silently corrupts
  the wireframe. This is a real, confirmed bug class (caught live during
  `/ts-new-project`'s SVG-based sibling skill build) — `create_wireframe.py`'s `_esc()`
  helper handles this automatically for generated content; apply the same escaping by
  hand for anything you add or edit afterward.
- **Region fill:** `white` for a normal region, `#f5f5f5` for a dimmed
  still-mounted-underneath region (e.g. Pattern C's base canvas under an overlay),
  `#333` (dark, with white text) for the screen's single most important action (e.g.
  Pattern D's primary button). Don't invent additional fills — three is enough to
  read as "normal / dimmed / emphasized."
- **Border + text color:** `stroke="#333"` on every `<rect>`, `fill="#333"` on normal
  text (`fill="white"` only on the dark emphasized rect). Consistent across every
  wireframe — this is a gray-box sketch, not a themed mockup.
- Active nav item: append `*` to the label — e.g. `nav-1*` (same convention as before).
- Multi-line labels: stack `<tspan x="..." y="...">` elements inside one `<text>`
  block, one per line — see any pattern in `references/wireframe-templates.md` for
  the real spacing (18px line height).
- **Scrollable regions:** append `[scroll]` to the label of the first content region
  in a scrollable area — same bracket convention as before, just as SVG text now
  instead of a monospace grid annotation.
- **Phone variant:** if the nav chrome changes on phone (e.g. rail → bottom bar),
  add a separate `<svg>` block in the same screen file under a `## Phone variant`
  heading, same canvas size.

### Region sizing guide

Pick region widths within the 760×420 canvas that reflect real proportions:

| Region type          | Typical width | Notes                             |
|-----------------------|---------------|------------------------------------|
| Narrow nav strip      | 64px          | Icon-only side rail                |
| Secondary panel       | 140–200px     | List, mode selector, sidebar       |
| Main content area     | remainder     | Always the flex/fill region        |
| Full-width canvas     | 760px         | When the secondary panel is hidden |

Region widths in one wireframe should sum to 760 (accounting for any gaps) — the
same "hold proportions consistent across the whole screen" discipline the old
same-character-width rule enforced, just in pixels instead of characters.

---

## Wireframe Templates

Full content: `references/wireframe-templates.md`.

## Translating an External HTML/CSS Wireframe

Some projects arrive with a wireframe already drafted as a real HTML/CSS file (e.g.
`design/wireframes/*.html` — a self-contained interactive prototype with inline styles
and vanilla JS), rather than starting from a blank screen. Translate it into this
skill's standard output (`docs/layout-system/<feature>/<ScreenName>.md`) — do not
invent a second, parallel wireframe format for HTML sources. The downstream pipeline
(`kmp-compose-preview-driven-development` generating preview stubs, then real
implementation) stays exactly the same either way.

### Structural mapping

| HTML/CSS construct | Compose equivalent |
|---|---|
| `display: flex; flex-direction: column` | `Column` |
| `display: flex` (row, default) | `Row` |
| `display: grid; grid-template-columns: repeat(N, ...)` | `Row` with `.weight(1f)` per cell (small fixed N), or `LazyVerticalGrid` (large/scrolling N) |
| A `<div>` acting as a card/section container | The project's actual card component (`AppCard` / `ShadcnCard`) — not a raw `Box` with manual background+shape |
| `<button>` | `AppButton` / `ShadcnButton` — infer variant from styling (filled+colored → primary/default, bordered+transparent → outline, no border+transparent → ghost) |
| `<input type="text">` | `AppTextField` / `ShadcnTextField` (single-line) |
| `<textarea>` | **Verify which of these two shapes the project's system actually uses — they differ.** `AppTextField` (design-system) genuinely has `singleLine: Boolean = true`, so `AppTextField(singleLine = false, ...)` is correct there. `ShadcnTextField` (shadcn-compose) has **no such parameter** — the real multi-line component is the separate `ShadcnTextarea`. Assuming either shape without checking is the confirmed, real bug that motivated this row; see `kmp-shadcn-compose`'s Step 3 |
| `<select>` | `AppSelect` / `ShadcnSelect` |
| `<input type="checkbox">` | `AppCheckbox` / `ShadcnCheckbox` — verified `ShadcnCheckbox(checked, onCheckedChange, modifier, indeterminate, enabled, style)`, no `label` parameter — pair with a separate `ShadcnLabel`/text, don't assume one is built in |
| `<input type="radio">` (a group) | `AppRadioButton`-group / `ShadcnRadioGroup { ... }` wrapping individual `ShadcnRadioButton(selected, onClick, ...)` — verified shadcn-compose has **no monolithic "options list" API** here; it mirrors shadcn/ui's `RadioGroup`+`RadioGroupItem` split, so the caller lays out each row (radio + label) manually |
| `<input type="range">` | `AppSlider` / `ShadcnSlider(value, onValueChange, modifier, valueRange, enabled, style)` — verified `valueRange` is a `ClosedFloatingPointRange<Float>`, default `0f..1f` |
| `<table>` | `AppTable`/no direct design-system equivalent yet, or verified `ShadcnTable { ShadcnTableHeaderRow { ShadcnTableHeadCell(...) }; ShadcnTableRow { ShadcnTableCell(...) } }` — rows are plain `Row`s (cells receive `RowScope`), so per-column `Modifier.weight` works the same as any other `Row` |
| A JS-driven modal/`<dialog>` | `AppDialog` / verified `ShadcnDialog(visible, onDismissRequest, modifier, showCloseButton, dismissOnClickOutside, closeIcon, content)` with `ShadcnDialogHeader`/`ShadcnDialogTitle`/`ShadcnDialogDescription`/`ShadcnDialogFooter` slot composables — not a single flat parameter list |
| `<input type="file">` | No shadcn-compose equivalent found in the catalog — this needs a platform file-picker integration (`kmp-permissions` for the runtime permission, plus a platform-specific picker), not a `Shadcn*` component at all |
| Tab-strip built from styled `<button>`s with a JS "active" class toggle | The project's actual tab component (verify its real name and signature — do not assume it matches the HTML's implied shape) |
| Icon webfont classes (Tabler, Font Awesome, Material Icons, etc.) | **Not a direct mapping.** Resolve separately via `kmp-imagevector-generator` (trace the real glyph) or a Compose icon library that ships the same icon set — never assume a matching Compose icon exists automatically just because the wireframe references one |
| CSS custom properties (`--surface-1`, `--text-primary`, `--fill-brand`, etc.) | Map by **role**, not by literal hex value, to the project's actual design tokens (`AppTheme.colors.*` / `ShadcnTheme.current.colors.*`). A wireframe's exact hex codes are a starting reference for choosing the nearest token — hardcoding them directly is exactly what `hardcoded_color`/`magic color literal` findings catch |
| JS-driven view switching (`.view.active` show/hide via `classList`) | Compose state (`remember { mutableStateOf(...) }` + a `when` over the current view) if views are peers within one screen, or real navigation if they are genuinely separate destinations |
| CSS `:hover`/`.active` pseudo-states | Compose `interactionSource`/`collectIsHoveredAsState` — translate the *intent* (this element has a distinct pressed/active look), not the literal CSS mechanism |

### The rule that matters most here

**Never assume a Compose component parameter exists because the HTML wireframe implies
certain behavior.** A `<textarea>` implies "multi-line text input" — that intent is
correct, but the *real* component that provides it must be verified, not guessed by
analogy to HTML attributes or to Jetpack Compose's own `TextField` API shape. This is
the same discipline `kmp-shadcn-compose` requires for any component
call: fetch or read the real signature before writing the call, every time, for every
component — HTML-sourced wireframes don't get a shortcut. For a shadcn-compose project,
`kmp-shadcn-compose/scripts/fetch_component_signature.py <ComponentName>`
does this lookup in one command.

---

## Filled Example

Full content: `references/filled-example.md`.

## Validation Checklist

| Check | Expected |
|---|---|
| `_components.md` updated | Any new or changed component in the registry |
| Screen file exists | One `.md` per screen |
| Placeholders filled in | No `<placeholder>`-style label left un-filled in committed files (still XML-escaped if genuinely left as a placeholder) |
| SVG is valid XML | Parses cleanly — `python3 -c "import xml.etree.ElementTree as ET; ET.fromstring(open('x.svg').read())"` or equivalent |
| Labels XML-escaped | Every literal `<`/`>` in a `<text>`/`<tspan>` is `&lt;`/`&gt;` |
| Active state shown | Active nav item uses `*` suffix, e.g. `nav-1*` |
| Canvas consistent | `viewBox="0 0 760 420"` on every wireframe in the project |
| Variants present | Separate `<svg>` block per layout variant (modal, empty state, etc.) |
| Phone variant | If nav chrome differs on phone, a `Phone variant` block exists in the screen file |
| Interaction notes | Each screen file has a short notes section |

---

## Recommendation First

Default to creating `docs/layout-system/` when none exists. One file per screen, plus `_components.md`. Start with the screen that has the most shared components — it reveals the most reuse early.

Use Pattern A (3-col) for tablet/desktop, Pattern B (2-col) when the side panel is hidden, Pattern D for full-screen flows (login/onboarding/splash). Add a Phone variant block when nav chrome changes between breakpoints.

---

## Common Anti-Patterns

- Putting project-specific component names directly in the wireframe template rather than in a Filled Example section
- Skipping the phone variant when the nav layout changes at mobile breakpoints
- **Leaving a literal `<`/`>` unescaped in an SVG label** — corrupts the wireframe (parses as an XML tag, not text); always `&lt;`/`&gt;` a placeholder like `<primary content>`
- Inventing a new fill color per wireframe instead of the fixed 3-color set (white / `#f5f5f5` dimmed / `#333` emphasized) — this is a gray-box sketch, not a themed mockup
- Letting `_components.md` drift from the actual Compose component names — it is a living registry, not a snapshot
- Writing `docs/layout-system/` files that describe the current implementation rather than the intended design; the layout doc should lead the code, not follow it
- Putting more than one screen in a single file, or appending a screen to another screen's file — run `create_wireframe.py` once per screen so each gets its own file; caught in a consumer project by the audit's `combined layout screen file [MEDIUM]`
- Assuming a Compose component's parameters by analogy to the source HTML/CSS wireframe's attributes, or to Jetpack Compose's own API shape — verify the real signature for the project's actual component system every time; see "Translating an External HTML/CSS Wireframe"
- Inventing a second, parallel wireframe format for HTML-sourced designs instead of translating into this skill's standard `docs/layout-system/*.md` output

---

## Testing

This skill produces markdown documentation, not runtime code. The validation equivalent of a test is the **Validation Checklist** at the end of each screen file:

- All `<placeholder>` tags replaced with real names in committed files (or, if left
  as a placeholder, still XML-escaped)
- Every SVG block parses as valid XML — a literal unescaped `<`/`>` in a label is
  the one real, confirmed failure mode here
- Phone variant block present when nav changes at mobile breakpoints
- Canvas `viewBox="0 0 760 420"` consistent across every wireframe in the project
- `_components.md` registry lists every component that appears in any screen file
- Platform column (`Both` / `Android` / `iOS`) filled for every row

Run `python3 skills/kmp-audit/scripts/audit_skills_repo.py .` to catch line-limit and naming violations across the `docs/layout-system/` directory (this repo's own skill-authoring checks).

In a **consumer** project, run `/kmp-run-audit` (`kmp-audit/scripts/audit_project.py`) — its `combined layout screen file [MEDIUM]` detector flags any `docs/layout-system/*.md` file (other than `_components.md`) with more than one top-level heading, the backstop for a hand-edited file that merged two screens together.

---

## Output Style

When asked to create or update layout-system docs, respond in this order:
1. State which screens will be created or updated and which pattern applies to each
2. Create or update `_components.md` first — it is the registry everything else references
3. Create screen files one at a time, starting with the screen that has the most shared components
4. Show the SVG wireframe inline for each screen so the user can review the layout before committing
5. End with the Validation Checklist filled out for the files just written

Keep explanations short. The wireframe is the primary output — do not narrate what each row means unless the user asks.

---

## References

Full implementation content lives in `references/*.md`: `wireframe-templates`,
`filled-example`. Load the specific file named in the pointer under its matching heading
above, not all of them.

---

## Related Skills

- `kmp-compose-adaptive-layout` — Compose implementation of breakpoint-driven
  layouts (Compact/Medium/Expanded). Layout-system docs describe intent; this skill
  implements it in code.
- `kmp-compose-design-system` — Design tokens, colors, and typography used
  by the components listed in `_components.md`.
- `kmp-project-docs-maintainer` — Keeps `docs/` healthy. Layout-system
  files follow the same kebab-case and line-limit hygiene rules.
- `kmp-shadcn-compose` — owns the verify-real-signature discipline this
  skill's HTML-translation section applies; its Step 3 has the confirmed real bug that
  motivated the rule.
- `kmp-imagevector-generator` — resolves icons referenced by an HTML
  wireframe's icon webfont classes; never assumed to map 1:1 automatically.

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-10 | Switched wireframes from Unicode-box-drawing ASCII to SVG — `create_wireframe.py` now emits `<rect>`/`<text>` regions per pattern instead of a character grid, both reference files (`wireframe-templates.md`, `filled-example.md`) rewritten to match, `generate_slot_scaffold.py` untouched (reads the frontmatter contract, not the visual). Motivation: SVG gives real proportions with zero alignment upkeep, embeds inline in any markdown viewer with no compile step, unlike ASCII which needed a whole box-drawing-character convention just to render evenly. Caught and fixed a real bug during the rewrite: a literal `<`/`>` in a placeholder label (e.g. `<primary content>`) is invalid unescaped inside SVG/XML text content — added `create_wireframe.py`'s `_esc()` helper and the escaping rule now documented above; confirmed via `xml.etree.ElementTree` parsing all 4 generated patterns before shipping. |
| 2026-07-17 | Switched wireframe borders from plain ASCII (`+`/`-`/`|`) to Unicode box-drawing characters (`┌┐└┘├┤┬┴┼─│`) — plain ASCII renders visibly uneven at junctions in most monospace fonts; box-drawing glyphs are purpose-built single-width characters (verified: same East Asian Width class as ASCII, unlike double-width emoji) that render cleanly everywhere. Converted all 4 templates in this file and in `create_wireframe.py`'s `PATTERNS` dict programmatically (a hand-converted first attempt corrupted label hyphens like `[nav-1]` into `[nav─1]` — caught before shipping, fixed by only converting `-` adjacent to another border character). Also found and fixed a real, pre-existing bug this surfaced: `create_wireframe.py`'s Pattern D `full width` line was 1 character shorter than every other row, violating this skill's own same-width rule. |
| 2026-07-12 | Added "Translating an External HTML/CSS Wireframe" — a real consumer project had an HTML wireframe implemented incorrectly (`ShadcnTextField` given a hallucinated `singleLine` parameter instead of using the real, dedicated `ShadcnTextarea` component). New structural mapping table (flex/grid → Row/Column, `<textarea>` → verify the project's actual multi-line shape, icon webfont classes → resolve via imagevector-generator, never assumed 1:1), and a hard rule: never assume a Compose component's parameters by analogy to the source HTML or to Compose's own API shape. Translates into this skill's existing `docs/layout-system/*.md` format — no parallel format for HTML sources. Expanded the mapping table with 6 more verified constructs (checkbox, radio group, range slider, table, modal dialog, file input — the last one has no shadcn-compose equivalent at all, confirmed rather than assumed) using `kmp-shadcn-compose`'s new `fetch_component_signature.py`. 2 new anti-patterns. |
| 2026-07-09 | The one-screen-per-file rule was documented but had no enforcement beyond `create_wireframe.py` refusing to overwrite — a hand-edited file could still merge two screens together silently. New `kmp-audit` detector `combined layout screen file [MEDIUM]` flags any `docs/layout-system/*.md` file (other than `_components.md`) with more than one top-level heading. |
| 2026-08-04 | Split "Wireframe Templates" and "Filled Example" out of SKILL.md into `references/*.md`, leaving pointer stubs plus a new References section. SKILL.md drops from 532 to 382 lines, clearing the agentskills.io 500-line recommendation. No content removed, only relocated. Part of the same backlog cleanup as the other 18 skills fixed alongside it (KI-008). |
| 2026-07-03 | Added a repo-relative fallback path for generate_slot_scaffold.py — `~/.claude/skills/...` only resolves in a Claude Code install; Codex CLI and Gemini CLI installs need the `skills/...` relative path (see INSTALL.md). |
| 2026-07-03 | Slot-grid contracts: create_wireframe.py now emits machine-readable frontmatter (slots/grid/weights per breakpoint); new generate_slot_scaffold.py compiles the contract into a <Screen>Layout.kt shell with slot lambdas — the agent fills content, never structure. Weights restricted to a closed fraction set, enforced by the raw weight literal audit smell. |
| 2026-06-30 | Added create_wireframe.py — deterministic one-file-per-screen scaffolder (seeds section skeleton + pattern A/B/C/D block, bootstraps _components.md once, never overwrites). Hardened the one-screen-per-file rule; new anti-pattern against multi-screen files. |
| 2026-06-27 | Made all templates fully generic — replaced project-specific component names with `<placeholders>`. Added filled example using a neutral messaging app. Reframed purpose as draft/document, not limit. |
| 2026-06-27 | Fixed ASCII wireframe alignment: removed emoji from grid, moved to Legend line, standardized row widths per template. |
| 2026-06-27 | Initial release — layout system format, ASCII wireframe spec, component registry, screen file template, bootstrap flow. |
