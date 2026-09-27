# Motion Decision Framework

Part of `kmp-compose-animation`. Load this file when working on: deciding whether to
animate, choosing easing or duration, motion tokens, press feedback.

Adapted to Compose from Emil Kowalski's design-engineering skill
([emilkowalski/skill](https://github.com/emilkowalski/skill), MIT). The source rules are
written for CSS; the numbers and decisions carry over, the APIs below are Compose's.

---

Answer the four questions in order before writing animation code.

## 1. Should it animate at all?

Frequency decides.

| How often the user sees it | Decision |
|---|---|
| 100+ times a day (keyboard shortcut, command palette, tab switch) | No animation |
| Tens of times a day (list navigation, hover) | Remove, or cut to the minimum |
| Occasional (dialog, bottom sheet, snackbar) | Standard animation |
| Rare (onboarding, first success, empty → first item) | Room for delight |

- Never animate keyboard-initiated actions on Desktop/Web. Repeated input turns any
  delay into lag.
- On a high-frequency path, an instant cut is the correct design, not a missing one.

## 2. What is it for?

Valid purposes:
- **Spatial consistency** — a snackbar leaves the way it came, so swipe-to-dismiss makes sense.
- **State change** — a button morphs to show "saving" → "saved".
- **Feedback** — a press scales down, confirming the tap registered.
- **Explanation** — onboarding shows how a gesture works.
- **Avoiding a jarring jump** — content that pops in or out without transition reads as broken.

"It looks nice" on a frequent path is not a purpose. Don't animate.

## 3. Which easing?

| Motion | Easing |
|---|---|
| Entering or exiting | ease-out — `AppMotion.EaseOut` |
| Moving or morphing on screen | ease-in-out — `AppMotion.EaseInOut` |
| Color or opacity change in place | ease-out or ease-in-out; either reads fine |
| Constant motion (indeterminate progress, marquee) | `LinearEasing` |

- **Never ease-in for UI.** It starts slow, exactly when the user is watching, so the UI
  feels sluggish. The same 200 ms feels faster with ease-out.
- **`tween()` defaults to `FastOutSlowInEasing`** (Material's standard in-out curve).
  Pass the easing explicitly for enter/exit instead of relying on the default.
- **Use the stronger custom curves** in `AppMotion` — Compose's built-in curves are mild,
  and motion reads as unintentional.

## 4. How long?

UI motion stays under 300 ms. Faster reads as more responsive: a 180 ms menu feels
quicker than a 400 ms one even when the content loads at the same speed.

| Element | Duration | Token |
|---|---|---|
| Press feedback | 100–160 ms | `DURATION_FAST` |
| Tooltip, small popover | 125–200 ms | `DURATION_SHORT` |
| Dropdown, menu, in-place content swap | 150–250 ms | `DURATION_MEDIUM` |
| Dialog, bottom sheet, drawer | 200–500 ms | `DURATION_LONG` |
| Explanatory / onboarding | longer is fine | — |

---

## Motion tokens

Put these in `:core:designsystem` (`tokens/AppMotion.kt`) so no screen hardcodes
`tween(300)`. A plain `object`: motion doesn't change between light and dark themes, so
it needs no `CompositionLocal`.

```kotlin
package GROUP_ID.core.designsystem.tokens

import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.Easing

object AppMotion {
    val EaseOut: Easing = CubicBezierEasing(0.23f, 1f, 0.32f, 1f)       // enter / exit
    val EaseInOut: Easing = CubicBezierEasing(0.77f, 0f, 0.175f, 1f)    // on-screen movement
    val EaseDrawer: Easing = CubicBezierEasing(0.32f, 0.72f, 0f, 1f)    // iOS-like sheet / drawer

    const val DURATION_FAST = 140    // press feedback
    const val DURATION_SHORT = 180   // tooltip, small popover
    const val DURATION_MEDIUM = 220  // menu, dropdown, content swap
    const val DURATION_LONG = 300    // dialog, sheet, drawer
}
```

Usage: `tween(AppMotion.DURATION_MEDIUM, easing = AppMotion.EaseOut)`.

---

## Compose rules that follow

**Nothing appears from nothing.** `scaleIn()` defaults to `initialScale = 0f`, which looks
like the element came from nowhere. Start near full size and pair it with a fade:

```kotlin
enter = fadeIn(tween(AppMotion.DURATION_SHORT, easing = AppMotion.EaseOut)) +
        scaleIn(tween(AppMotion.DURATION_SHORT, easing = AppMotion.EaseOut), initialScale = 0.95f)
```

**Popovers scale from their trigger.** A menu opening below its anchor grows from the top
edge, not the center: `scaleIn(initialScale = 0.95f, transformOrigin = TransformOrigin(0.5f, 0f))`.
Dialogs are not anchored, so they keep the default center origin.

**Pressables confirm the press.** Scale to 0.95–0.98, fast, ease-out. Design-system `App*`
components already get this from their Style `pressed {}` block; for any other clickable:

```kotlin
val interactionSource = remember { MutableInteractionSource() }
val pressed by interactionSource.collectIsPressedAsState()
val scale by animateFloatAsState(
    targetValue = if (pressed) 0.97f else 1f,
    animationSpec = tween(AppMotion.DURATION_FAST, easing = AppMotion.EaseOut),
    label = "press_scale",
)
Box(
    Modifier
        .graphicsLayer { scaleX = scale; scaleY = scale }
        .clickable(interactionSource = interactionSource, indication = null, onClick = onClick),
)
```

**Springs for gestures and interruptions.** When the target changes mid-flight, a
`spring` continues with its current velocity; a `tween` restarts its timing from the
current value, which reads as a stutter. Use springs for drag-release, swipe-to-dismiss,
and anything the user can reverse quickly.

**Keep routine UI springs non-bouncy.** `spring(dampingRatio = Spring.DampingRatioNoBouncy)`
for selection, expansion, and layout changes. Save bounce (`dampingRatio` around 0.75–0.9)
for drag-release and playful, rare moments — never on a control used many times a day.

**Reduced motion wins.** Every rule above applies only when `rememberReduceMotion()` is
false; otherwise cut instantly or crossfade (see the SKILL.md Reduced-motion section).
