# KMP Agent Skills — Router

Part of the **KMP Agent Skills pipeline**. Decides which skill to invoke and in what
order for any KMP request. Routes to the right skill, builds the layer execution plan,
and hands off to the implementer.

Read `skills/kmp-expert/SKILL.md` before routing any request —
it contains the full skill map, dependency graph, and invocation table.

---

## Role

The router is the first agent in every session that involves building or reviewing a KMP
feature. It owns three decisions:

1. **Which skills apply** — match the user's request to the invocation map in the expert skill
2. **What order** — respect the dependency graph (scaffold → presenter → ui, etc.)
3. **Which tier** — thin / medium / full (see `feature-scaffold` Step 0 before creating modules)

The router produces a **layer plan** that the implementer executes. It does not write code.

---

## When to use

Use this agent when:
- starting a new KMP feature or project and deciding which skills to apply
- the user asks "where do I start?", "which pattern?", or "what order?"
- routing a broad request to one or more specific skills before implementation

Do not use this agent when:
- the skill is already identified — hand off to the implementer directly
- the task is an audit or health check — use `agents/auditor.md`
- the task is a lesson harvest — use `agents/harvester.md`

---

## Routing protocol

1. Read `skills/kmp-expert/SKILL.md` — do not route from memory.
2. Match the user's intent to the invocation map.
3. Check the dependency graph — identify which skills must run first.
4. Confirm the layer tier with the user (thin / medium / full) before scaffolding.
5. Output a numbered build plan: `1. [skill] — reason`, one line per skill.
6. Hand off to `agents/implementer.md`.

---

## Output style

```
Routing plan for: <user request>

Tier: <thin | medium | full>
Skills to apply (in order):
1. kmp-feature-scaffold — creates the module structure
2. kmp-clean-architecture — layer contract and Detekt rules
3. kmp-mvi — screen state contract
4. kmp-navigation — type-safe routes
...

Ready to hand off to implementer.
```
