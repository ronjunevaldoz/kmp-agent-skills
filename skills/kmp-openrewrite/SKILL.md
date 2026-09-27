---
name: kmp-openrewrite
description: >
  Automated, compiler-accurate AST refactoring and migration engine for Kotlin
  Multiplatform and Gradle projects using OpenRewrite. Use when performing repo-wide
  dependency upgrades, version catalog (libs.versions.toml) updates, Gradle deprecation
  remediation, or automated framework migrations (e.g. Ktor 2 to 3, Coroutines, or
  Java to Kotlin brownfield upgrades) across dozens of multiplatform modules in a single step.
license: Apache-2.0
metadata:
  author: kmp-agent-skills
  last-updated: '2026-09-15'
  keywords:
    - openrewrite
    - rewrite
    - ast refactoring
    - automated migration
    - gradle rewrite
    - version catalog migration
    - dependency bump
    - ktor migration
    - lossless semantic tree
    - multi-module refactor
---

# OpenRewrite for Kotlin Multiplatform & Gradle

## When to Use This Skill

Use this skill when:
- Upgrading dependencies or Gradle Wrapper versions across a 20+ module KMP repository in a single command
- Performing compiler-accurate migrations on `build.gradle.kts` and `gradle/libs.versions.toml` files
- Upgrading framework APIs with verified semantic recipes (e.g., Ktor 2.x to Ktor 3.x, Kotlinx Serialization, Coroutines)
- Eliminating deprecated Gradle API calls before major Gradle bumps
- Performing brownfield migrations where manual file-by-file agent editing would waste excessive context tokens or introduce typographical syntax errors

Do NOT use this skill when:
- Making simple, localized changes to 1–2 Kotlin files (use standard agent editing or Android Studio refactor)
- Renaming Kotlin symbols that require deep IDE project context (use `kmp-refactor`)
- Enforcing project-specific architectural rules or layer boundaries without pre-built recipes (use `kmp-audit` or Detekt)

**Trigger keywords:** openrewrite, rewrite, rewriteRun, rewriteDryRun, ast refactoring, automated migration, gradle rewrite, migrate build.gradle.kts, libs.versions.toml upgrade, ktor 3 migration, bulk dependency update.

---

## Recommendation First

1. **Always run `rewriteDryRun` first.**
   Inspect the generated patch file (`build/reports/rewrite/rewrite.patch`) to verify every diff before running `rewriteRun`.
2. **Use OpenRewrite primarily for Gradle and build-logic first.**
   OpenRewrite's Lossless Semantic Tree (LST) support for Gradle Kotlin DSL (`build.gradle.kts`) and `libs.versions.toml` is compiler-precise and preserves whitespace, formatting, and comments.
3. **Commit or stash working tree before executing `rewriteRun`.**
   Enables a clean, single-command `git diff` review and instant rollback via `git restore .` if any recipe makes an undesirable edit.

---

## 1. Project Setup: Adding OpenRewrite to a KMP Root Build

Add the OpenRewrite Gradle plugin to your root `build.gradle.kts`:

```kotlin
// root build.gradle.kts
plugins {
    id("org.openrewrite.rewrite") version "7.16.0"
}

rewrite {
    // Specify active recipes or pass via CLI with -Drewrite.activeRecipes=...
    activeRecipe(
        "org.openrewrite.gradle.UpdateGradleWrapper",
    )
}

dependencies {
    // Standard OpenRewrite recipe bundles
    rewrite("org.openrewrite.recipe:rewrite-migrate-java:3.2.0")
    rewrite("org.openrewrite.recipe:rewrite-kotlin:1.24.0")
    rewrite("org.openrewrite.recipe:rewrite-recommendations:1.15.0")
}
```

Or configure it dynamically in `gradle.properties` / CLI flags without altering checked-in build logic permanently during ad-hoc migrations.

---

## 2. Core Execution Workflows

### 1. The Verification Gate: Dry-Run
Always preview changes before touching files:
```bash
./gradlew rewriteDryRun
```
Outputs a unified diff report to:
`build/reports/rewrite/rewrite.patch`

### 2. The Execution Pass
Apply the transformations directly to the working tree:
```bash
./gradlew rewriteRun
```

### 3. Running Specific On-Demand Recipes via CLI
You do not need to hardcode recipes into `build.gradle.kts`. Run any classpath recipe on the fly:
```bash
./gradlew rewriteRun -Drewrite.activeRecipes=org.openrewrite.gradle.UpdateGradleWrapper
```

---

## 3. High-Leverage KMP Recipes

### A. Gradle Wrapper & Plugin Upgrades
Safely bump the Gradle distribution and SHA-256 checksum across `gradle-wrapper.properties`:

```bash
./gradlew rewriteRun \
  -Drewrite.activeRecipes=org.openrewrite.gradle.UpdateGradleWrapper \
  -Dorg.openrewrite.gradle.UpdateGradleWrapper.version=8.14
```

### B. Dependency Catalog Upgrades (`libs.versions.toml`)
Update dependency versions in `gradle/libs.versions.toml` without breaking table alignment or formatting:

```yaml
# rewrite.yml in project root
type: specs.openrewrite.org/v1beta/recipe
name: com.awakekt.kmp.UpdateCoroutines
displayName: Update KotlinX Coroutines to 1.11.0
recipeList:
  - org.openrewrite.gradle.ChangeDependencyVersion:
      groupId: org.jetbrains.kotlinx
      artifactId: kotlinx-coroutines-*
      newVersion: 1.11.0
```

Run via:
```bash
./gradlew rewriteRun -Drewrite.configLocation=rewrite.yml -Drewrite.activeRecipes=com.awakekt.kmp.UpdateCoroutines
```

### C. Ktor 2.x to Ktor 3.x Migration
Ktor 3 changed artifact group coordinates from `io.ktor:ktor-client-*` to package-aligned modules and renamed several internal engine parameters.

```yaml
# rewrite.yml
type: specs.openrewrite.org/v1beta/recipe
name: com.awakekt.kmp.MigrateKtor3
displayName: Migrate Ktor 2 to Ktor 3
recipeList:
  - org.openrewrite.java.ChangePackage:
      oldFullyQualifiedPackageName: io.ktor.client.features
      newFullyQualifiedPackageName: io.ktor.client.plugins
  - org.openrewrite.gradle.ChangeDependencyVersion:
      groupId: io.ktor
      artifactId: *
      newVersion: 3.5.0
```

---

## 4. Agent Operational Runbook

When an AI agent is asked to perform a bulk migration across many modules:

1. **Verify Git State**: Ensure `git status` is clean.
2. **Formulate Declarative Recipe**: Create a temporary `rewrite.yml` at the project root rather than writing custom Java classes.
3. **Execute Dry-Run**:
   ```bash
   ./gradlew rewriteDryRun -Drewrite.configLocation=rewrite.yml -Drewrite.activeRecipes=<RecipeName>
   ```
4. **Review Patch**: View `build/reports/rewrite/rewrite.patch` to confirm that imports, versions, and syntax are intact.
5. **Apply & Verify**:
   ```bash
   ./gradlew rewriteRun -Drewrite.configLocation=rewrite.yml -Drewrite.activeRecipes=<RecipeName>
   ./gradlew check
   ```
6. **Clean Up**: Remove the temporary `rewrite.yml`.

---

## Common Anti-Patterns

| Mistake | Fix |
|---|---|
| Running `rewriteRun` on a dirty working tree | Run `git stash` or commit work first so you can inspect pure recipe diffs with `git diff`. |
| Writing custom Java compilation recipes for simple renames | Use declarative YAML recipes with existing primitives (`ChangePackage`, `ChangeMethodName`, `ChangeDependencyVersion`). |
| Applying Java-specific bytecode recipes to Kotlin Multiplatform targets | Use `rewrite-kotlin` and `rewrite-gradle` recipes; avoid Java annotation-processing transforms that don't recognize KMP source sets. |
| Skipping `rewriteDryRun` | Always run dry-run to ensure comment formatting or buildscript blocks were not unexpectedly restructured. |

---

## Testing

Validate OpenRewrite recipe transformations using Gradle verification tasks:
- `@Test` recipe YAML definitions against a mock Gradle project using `RewriteTest` harness.
- Run `runTest` on execution scripts to verify `rewriteDryRun` generates clean `.patch` outputs.
- Use `FakeGradleProject` fixture when testing AST modifications in isolation.

---

## Output Style

1. Always show the diff preview from `rewriteDryRun` before executing `rewriteRun`.
2. Summarize affected modules and modified dependencies in a compact table.
3. Emit exact shell commands with `-Drewrite.configLocation` and `-Drewrite.activeRecipes`.

---

## Related Skills

- `kmp-migration` — incremental architecture adoption and brownfield strategy
- `kmp-refactor` — semantic and textual symbol rename/move guidance
- `kmp-feature-scaffold` — module boundaries and convention plugin layout
- `kmp-audit` — project health audit and smell detection

**Freshness rule:** recheck OpenRewrite Gradle plugin (`org.openrewrite.rewrite`) releases and Kotlin AST recipe compatibility before executing large refactors.

---

## Changelog

| Date | Change |
|---|---|
| 2026-09-18 | Initial release — codified OpenRewrite Gradle plugin setup, declarative YAML recipes, dry-run gate, and automated Ktor 2 to 3 migration. |
