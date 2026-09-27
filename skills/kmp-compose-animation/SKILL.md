---
name: kmp-compose-animation
description: >-
  Compose Multiplatform animation patterns — AnimatedVisibility with enter/exit
  transitions, animateContentSize, Crossfade for screen-level transitions,
  animateFloatAsState / animateDpAsState for property animations, and shared
  element transitions (Compose 1.7+). Covers when to use each API, whether to
  animate at all, easing and duration choices with motion tokens, and how to keep
  animations accessible with reduced-motion support.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-27'
  keywords:
    - animation
    - AnimatedVisibility
    - animateContentSize
    - Crossfade
    - AnimatedContent
    - animateFloatAsState
    - animateDpAsState
    - shared element transition
    - enter transition
    - exit transition
    - spring animation
    - tween animation
    - compose animation
    - reduced motion
    - accessibility animation
    - motion tokens
    - easing curve
    - animation duration
    - CubicBezierEasing
    - press feedback
---

## When to Use This Skill

Use when:
- A UI element should fade, slide, or expand into view rather than appearing instantly
- Switching between two composables needs a visual crossfade or slide transition
- A card or list item changes size and should animate the height change
- A property (alpha, scale, offset) needs to animate from one value to another
- Shared element transitions are needed between list and detail screens (Compose 1.7+)

**Trigger keywords:** animation, AnimatedVisibility, animateContentSize, Crossfade,
AnimatedContent, animateFloatAsState, animateDpAsState, transition, enter transition,
exit transition, shared element, spring animation, tween animation, compose animation,
fade in, slide in, bounce, ease, reduced motion, motion accessibility,
animate, animated transition, smooth transition, animate appearance, animate change,
motion, visual transition, page transition, screen transition, easing curve,
animation duration, how long should this animate, should this animate, motion tokens,
CubicBezierEasing, press feedback, animation feels slow, animation feels janky.

**Freshness rule:** Shared element transitions were stabilized in Compose 1.7 (Compose
Multiplatform 1.7). For earlier versions use `Crossfade` or a custom `AnimatedContent`.
`androidx.compose.animation:animation-graphics` (animated vector drawables) is
Android-only and not available in `commonMain`.

---

## Recommendation First

First decide *whether* and *how* to animate — Motion Decision Framework below. Then use
the simplest API that achieves the goal. In order of preference:
1. `AnimatedVisibility` — show/hide with transitions
2. `animateContentSize()` — height/width change
3. `Crossfade` / `AnimatedContent` — swap between two composables
4. `animateXAsState` — animate a single property value
5. Shared element transitions — only for connected list-detail navigation

---

## Motion Decision Framework

Full content (tables, token file, press-feedback snippet, spring rules):
`references/motion-decision-framework.md`. Adapted from Emil Kowalski's design-engineering
skill ([emilkowalski/skill](https://github.com/emilkowalski/skill), MIT). The four questions:

1. **Animate at all?** High-frequency actions (keyboard shortcuts, tab switches) get no
   animation. Rare moments may get delight.
2. **Purpose?** Spatial consistency, state change, feedback, explanation, or avoiding a
   jarring jump. "Looks nice" on a frequent path is not a purpose.
3. **Easing?** Enter/exit ease-out, on-screen movement ease-in-out, never ease-in.
   `tween()` defaults to `FastOutSlowInEasing`, so pass `AppMotion.EaseOut` explicitly.
4. **Duration?** Under 300 ms for UI: press 100–160, popover 125–200, menu 150–250,
   dialog/sheet 200–500.

Use `AppMotion` tokens (`tokens/AppMotion.kt` in `:core:designsystem`), never raw
`tween(300)`. `scaleIn()` defaults to `initialScale = 0f` — pass `0.95f` with a `fadeIn()`.

---

## AnimatedVisibility — show/hide with enter/exit

```kotlin
@Composable
fun ExpandableCard(title: String, body: String) {
    var expanded by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .animateContentSize()                  // smooth height change
            .clip(RoundedCornerShape(AppTheme.spacing.sm))
            .background(AppTheme.colors.surface)
            .clickable { expanded = !expanded }
            .padding(AppTheme.spacing.md),
    ) {
        Text(title, style = AppTheme.typography.titleMedium)

        AnimatedVisibility(
            visible = expanded,
            enter   = fadeIn() + expandVertically(),
            exit    = shrinkVertically() + fadeOut(),
        ) {
            Text(
                body,
                style    = AppTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = AppTheme.spacing.sm),
            )
        }
    }
}
```

---

## Crossfade — swap between two composables

```kotlin
@Composable
fun LoadingOrContent(isLoading: Boolean, content: @Composable () -> Unit) {
    Crossfade(
        targetState = isLoading,
        animationSpec = tween(AppMotion.DURATION_MEDIUM, easing = AppMotion.EaseOut),
    ) { loading ->
        if (loading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else {
            content()
        }
    }
}
```

---

## AnimatedContent — slide between states

```kotlin
@Composable
fun StepCounter(step: Int) {
    AnimatedContent(
        targetState = step,
        transitionSpec = {
            if (targetState > initialState) {
                // Advancing — slide in from right
                slideInHorizontally { it } + fadeIn() togetherWith
                        slideOutHorizontally { -it } + fadeOut()
            } else {
                // Going back — slide in from left
                slideInHorizontally { -it } + fadeIn() togetherWith
                        slideOutHorizontally { it } + fadeOut()
            }.using(SizeTransform(clip = false))
        },
        label = "step_counter",
    ) { currentStep ->
        Text("Step $currentStep", style = AppTheme.typography.headlineMedium)
    }
}
```

---

## animateXAsState — animate a property value

```kotlin
@Composable
fun SelectableChip(selected: Boolean, label: String, onClick: () -> Unit) {
    val backgroundColor by animateColorAsState(
        targetValue = if (selected) AppTheme.colors.primary else AppTheme.colors.surface,
        animationSpec = tween(AppMotion.DURATION_SHORT, easing = AppMotion.EaseOut),
        label = "chip_bg",
    )
    val scale by animateFloatAsState(
        targetValue   = if (selected) 1.05f else 1f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioNoBouncy), // routine UI: no bounce
        label = "chip_scale",
    )

    Box(
        modifier = Modifier
            .scale(scale)
            .clip(CircleShape)
            .background(backgroundColor)
            .clickable(onClick = onClick)
            .padding(horizontal = AppTheme.spacing.md, vertical = AppTheme.spacing.sm),
    ) {
        Text(label, color = if (selected) AppTheme.colors.onPrimary else AppTheme.colors.onSurface)
    }
}
```

---

## Transition — animate multiple properties together

```kotlin
@Composable
fun PulsingFab(onClick: () -> Unit) {
    var pressed by remember { mutableStateOf(false) }
    val transition = updateTransition(targetState = pressed, label = "fab_press")

    val scale by transition.animateFloat(
        label = "fab_scale",
        transitionSpec = { tween(AppMotion.DURATION_FAST, easing = AppMotion.EaseOut) }
    ) { if (it) 0.97f else 1f }   // press feedback: 0.95–0.98, fast

    val elevation by transition.animateDp(label = "fab_elevation") { if (it) 2.dp else 6.dp }

    FloatingActionButton(
        onClick = onClick,
        elevation = FloatingActionButtonDefaults.elevation(defaultElevation = elevation),
        modifier = Modifier.scale(scale).pointerInput(Unit) {
            detectTapGestures(
                onPress = {
                    pressed = true
                    tryAwaitRelease()
                    pressed = false
                },
            )
        },
    ) {
        AppIcon(Icons.Default.Add, contentDescription = "Add")
    }
}
```

---

## Shared element transitions (Compose 1.7+)

```kotlin
// List item — source
@Composable
fun ProductListItem(product: Product, onClick: () -> Unit) {
    val sharedTransitionScope = LocalSharedTransitionScope.current
        ?: error("No SharedTransitionScope")
    val animatedContentScope = LocalNavAnimatedContentScope.current
        ?: error("No AnimatedContentScope")

    with(sharedTransitionScope) {
        Card(onClick = onClick) {
            AsyncImage(
                model = product.imageUrl,
                contentDescription = null,
                modifier = Modifier
                    .size(72.dp)
                    .sharedElement(
                        state = rememberSharedContentState(key = "product_image_${product.id}"),
                        animatedVisibilityScope = animatedContentScope,
                    ),
            )
            Text(product.name)
        }
    }
}

// Detail screen — destination
@Composable
fun ProductDetailContent(product: Product) {
    with(LocalSharedTransitionScope.current!!) {
        AsyncImage(
            model = product.imageUrl,
            contentDescription = product.name,
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp)
                .sharedElement(
                    state = rememberSharedContentState(key = "product_image_${product.id}"),
                    animatedVisibilityScope = LocalNavAnimatedContentScope.current!!,
                ),
        )
    }
}
```

NavHost must be wrapped in `SharedTransitionLayout`:

```kotlin
SharedTransitionLayout {
    CompositionLocalProvider(LocalSharedTransitionScope provides this) {
        NavHost(...) { /* routes */ }
    }
}
```

---

## Reduced-motion accessibility

Compose's common `AccessibilityManager` has no reduce-motion flag (its only member is
`calculateRecommendedTimeoutMillis`), so read each platform's own setting:

```kotlin
// commonMain
@Composable
expect fun rememberReduceMotion(): Boolean

// androidMain — the system "Remove animations" setting sets the animator duration scale to 0
@Composable
actual fun rememberReduceMotion(): Boolean {
    val resolver = LocalContext.current.contentResolver
    return remember { Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f }
}

// iosMain
@Composable
actual fun rememberReduceMotion(): Boolean = remember { UIAccessibilityIsReduceMotionEnabled() }

// wasmJsMain / jsMain — `window` comes from org.jetbrains.kotlinx:kotlinx-browser on wasmJs
@Composable
actual fun rememberReduceMotion(): Boolean =
    remember { window.matchMedia("(prefers-reduced-motion: reduce)").matches }

// jvmMain (Desktop) — no portable OS signal; back it with an in-app setting if needed
@Composable
actual fun rememberReduceMotion(): Boolean = false
```

Read once per composition entry: a user who flips the setting while the screen is open
gets it on the next screen, not live.

```kotlin
@Composable
fun AnimatedVisibilityOrInstant(
    visible: Boolean,
    content: @Composable () -> Unit,
) {
    if (rememberReduceMotion()) {
        if (visible) content()
    } else {
        AnimatedVisibility(visible = visible, enter = fadeIn(), exit = fadeOut()) {
            content()
        }
    }
}
```

---

## Testing

```kotlin
@get:Rule val composeRule = createComposeRule()

@Test fun `animated visibility shows content when visible`() {
    var visible by mutableStateOf(false)
    composeRule.setContent {
        AnimatedVisibility(visible = visible) {
            Text("Hello", modifier = Modifier.testTag("content"))
        }
    }
    composeRule.onNodeWithTag("content").assertDoesNotExist()
    visible = true
    composeRule.waitForIdle()
    composeRule.onNodeWithTag("content").assertExists()
}

@Test fun `crossfade renders target state after transition`() {
    var state by mutableStateOf("A")
    composeRule.setContent {
        Crossfade(targetState = state) { s ->
            Text(s, modifier = Modifier.testTag("text"))
        }
    }
    composeRule.onNodeWithTag("text").assertTextEquals("A")
    state = "B"
    composeRule.mainClock.advanceTimeByFrame()
    composeRule.waitForIdle()
    composeRule.onNodeWithTag("text").assertTextEquals("B")
}

// Roborazzi — capture final (animated-in) visual state
@Test fun `animated_content_visible_screenshot`() {
    captureRoboImage("animation_visible_state.png") {
        AppTheme {
            var visible by remember { mutableStateOf(true) }
            AnimatedVisibility(visible = visible) {
                Box(Modifier.size(80.dp).background(AppTheme.colors.primary))
            }
        }
    }
}
```

---

## Common Anti-Patterns

- **Animating inside a `LazyColumn` item without a `key`** — without stable keys Compose
  recycles items and restarts animations mid-flight; always set `key = { item.id }` in
  `LazyColumn`
- **`animateContentSize()` on a `LazyColumn`** — `LazyColumn` manages its own height;
  `animateContentSize` only works on layout containers whose content fits in memory
- **Using `Crossfade` for navigation-level transitions** — Crossfade is for in-place
  state swaps; use NavHost's `enterTransition`/`exitTransition` params for screen-level nav
- **Forgetting `label` on `animateXAsState`** — the `label` is used in Android Studio's
  Animation Preview; always provide a descriptive label
- **Shared element with a missing `SharedTransitionLayout` wrapper** — `sharedElement`
  crashes if no `SharedTransitionScope` is in the composition tree; wrap the NavHost
- **No reduced-motion fallback** — users with vestibular disorders can enable "Reduce Motion"
  in system settings; check `rememberReduceMotion()` before adding non-trivial animations
- **`LocalAccessibilityManager.current?.isReduceMotionEnabled`** — doesn't exist in Compose's
  common `AccessibilityManager` and won't compile; use the `rememberReduceMotion()` expect/actual
- **Default or ease-in easing on enter/exit** — `tween()` without `easing` is
  `FastOutSlowInEasing`; enter/exit wants `AppMotion.EaseOut`, and ease-in is never right for UI
- **`scaleIn()` with its default `initialScale = 0f`** — the element pops out of nothing;
  pass `initialScale = 0.95f` and pair with `fadeIn()`
- **Bouncy springs on routine controls** — `DampingRatioMediumBouncy` on a chip or toggle
  used many times a day; keep routine UI at `DampingRatioNoBouncy`
- **Animating high-frequency actions** — keyboard shortcuts, tab switches, command palettes;
  an instant cut is the correct design there
- **Raw `tween(300)` in screens** — use `AppMotion` duration and easing tokens

---

## References

Full content lives in `references/*.md`: `motion-decision-framework`. Load it under the
Motion Decision Framework pointer above, not standalone.

---

## Related Skills

- `kmp-compose-design-system` — `AppMotion` duration and easing tokens live in its
  `tokens/` package (see `references/motion-decision-framework.md`), not hardcoded `tween(300)`
- `kmp-compose-accessibility` — reduced-motion support is an a11y requirement;
  check `LocalAccessibilityManager` before applying non-trivial animations
- `kmp-navigation` — shared element transitions require the NavHost to be
  wrapped in `SharedTransitionLayout`; see the navigation skill for the full NavHost setup

---

## Output Style

When implementing animations, respond in this order:
0. **Decide** — whether to animate, purpose, easing, duration (Motion Decision Framework)
1. **Identify the right API** — `AnimatedVisibility`, `Crossfade`, `animateXAsState`,
   shared element — based on what the UI is doing
2. **Implementation** — composable with the animation applied
3. **Reduced-motion** — `rememberReduceMotion()` check for non-trivial transitions
4. **Anti-pattern note** — call out if the chosen API has a common pitfall in this context

---

## Changelog

| Date | Change |
|---|---|
| 2026-09-27 | Added the Motion Decision Framework (`references/motion-decision-framework.md`), adapted from Emil Kowalski's design-engineering skill (MIT): whether to animate by frequency, purpose, easing (ease-out for enter/exit, never ease-in; `tween()` defaults to `FastOutSlowInEasing`), duration table, and `AppMotion` tokens (`CubicBezierEasing` curves + durations) for `:core:designsystem`. Examples now use tokens, non-bouncy springs for routine UI, and 0.97 press scale. Fixed the reduced-motion snippet: `LocalAccessibilityManager.isReduceMotionEnabled` doesn't exist in Compose's common `AccessibilityManager` (verified against androidx source); replaced with a `rememberReduceMotion()` expect/actual over each platform's real setting. |
| 2026-06-21 | Initial release. |
