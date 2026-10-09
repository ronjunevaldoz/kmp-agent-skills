# Developer-Friendly Vibe-to-Plan Template

Use this template when translating natural user instructions ("vibe coding") into a structured, executable task plan in `docs/tasks/YYYY-MM-DD-<slug>-plan.md`.

---

# [Feature Name / Bugfix Title]

**Date:** YYYY-MM-DD  
**Status:** `Active`  
**Parent / Issue:** #<ticket-id> or N/A  
**Target Modules:** `:feature:<name>:model`, `:domain`, `:presenter`, `:ui`  

---

## 1. Real-World Mental Model (The Analogy)

> [!TIP]
> **Real-World Analogy**:  
> *Explain the problem and solution like a real-world scenario so any developer immediately grasps the UX and data flow.*
>
> *Example (Minimap & Fog of War)*: Think of an explorer with a physical parchment map. When they walk into a new valley, they sketch the landmarks onto the paper (Domain). The minimap widget is just the magnifying glass looking at that paper on screen (UI).

- **User Goal**: What the user wants to experience or achieve.
- **Root Cause / Current State**: Why it doesn't work today (or what is missing).

---

## 2. Before vs After (Call-Site Code Snippets)

### ❌ Before (Current Limitation)
```kotlin
// How callers currently struggle or why it fails:
val items = repository.fetchRawItems() // Leaks DB model into UI!
Text(text = "Price: ${items.price}")   // Formatting logic scattered in UI
```

### ✅ After (Target Architecture)
```kotlin
// How callers interact cleanly after this change:
val uiState by viewModel.uiState.collectAsState()
InventoryGrid(
    items = uiState.formattedItems,
    onItemClick = { viewModel.handle(InventoryIntent.Equip(it.id)) }
)
```

---

## 3. The 4-Stage Architectural Progression

Follow the Clean KMP Feature Pipeline:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 1. DATA / MODEL │ ──► │ 2. DOMAIN LOGIC │ ──► │ 3. PRESENTER    │ ──► │ 4. UI / RENDER  │
│   (Ingredients) │     │    (The Recipe) │     │    (The Waiter) │     │    (The Dish)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Stage 1: Data & Models (`:feature:<name>:model`)
- [ ] Define immutable UI state or data models `[ItemUiModel]`.
- [ ] Define pure domain entities.

### Stage 2: Domain Business Rules (`:feature:<name>:domain`)
- [ ] Implement use cases `[EquipItemUseCase]`.
- [ ] Zero Android/JVM/Compose dependencies in this layer.

### Stage 3: Presenter & State Flow (`:feature:<name>:presenter`)
- [ ] Create `[FeatureViewModel]` or State Holder.
- [ ] Expose single `StateFlow<FeatureUiState>` and `handle(intent: FeatureIntent)`.

### Stage 4: UI & Layout (`:feature:<name>:ui`)
- [ ] Build pure Composable UI components using design tokens (`AppTheme.colors.*`).
- [ ] Add `@Preview` for Desktop JVM.

---

## 4. Verification & Testing

```bash
# 1. Run domain unit tests
./gradlew :feature:<name>:domain:test

# 2. Record visual screenshot baselines (Roborazzi)
./gradlew :feature:<name>:ui:recordRoborazziDesktop

# 3. Verify architecture health (Zero God Classes / Smells)
python3 .agents/skills/kmp-audit/scripts/audit_project.py .
```

---
*Generated via Vibe Planning Standard — Automatically indexed by `heal_docs.py`*
