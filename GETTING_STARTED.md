# Getting Started with KMP Agent Skills

You have a Kotlin Multiplatform (KMP) project or want to start one. These agent skills guide you through architecture decisions, module structure, and implementation — end-to-end, one feature at a time.

**This is not a tutorial.** You don't read it. You use Claude Code to invoke these skills directly in your project.

---

## Main Use Cases

### Start a brand-new KMP project

```
/kmp-new-project "A shopping app with auth, product listing, and orders"
```

Collects your group ID, project name, platforms, and what the app does — then runs a
9-step pipeline: scaffold → clean architecture → infrastructure → design system →
features → tests → `.agents/` agent setup. Everything is wired and ready to build.

### Add agent workflows to an existing project

```
/kmp-setup-agents
```

Reads your `settings.gradle.kts` and `libs.versions.toml`, generates a tailored
`AGENTS.md` routing table, installs consumer commands, and deploys skills into `.agents/`.

### Audit an existing project

```
/kmp-run-audit
```

Runs `audit_project.py` and produces per-finding remediation using the relevant skill.

---

## 5-Minute Start (existing project)

```bash
cd your-kmp-project
claude
```

Then in Claude Code:

1. **New project** → `/kmp-new-project <description>`
2. **Existing project** → `/kmp-setup-agents`
3. **Audit** → `/kmp-run-audit`
4. **Add a feature** → `/kmp-implement-feature <name>`
5. **Not sure?** → Ask `kmp-expert` — it routes you to the smallest relevant skill set

---

## Common Starting Points

| Goal | Command / Skill |
|---|---|
| **New KMP project from scratch** | `/kmp-new-project <description>` |
| **Set up agents in existing project** | `/kmp-setup-agents` |
| **Add a new feature** | `/kmp-implement-feature <name>` or ask `kmp-expert` |
| **Audit an existing project** | `/kmp-run-audit` |
| **Implement a GitHub issue end-to-end** | `/kmp-execute-ticket <id>` |
| **Fix design system violations** | `/kmp-fix-design` |
| **Set up CI/CD** | `kmp-ci-github-actions` skill |
| **Publish to Maven Central** | `kmp-release` skill |
| **Migrate MVVM → MVI** | `kmp-migration` skill |
| **Debug architecture issues** | `/kmp-run-audit` → `kmp-expert` routes fixes |

---

## How Skill Triggering Works

Skills auto-activate when you mention a trigger keyword. You don't need to say the skill name.

```
How do I set up auth with JWT?
```

Claude invokes `kmp-ktor-auth-service` automatically because "JWT" and
"auth" are trigger keywords. See [README.md](README.md) for the full keyword list.

---

## Skill Collection Overview

69 skills organized into layers — architecture contract, project foundation, core
infrastructure, platform patterns, feature building blocks, UI system, testing & quality,
plus a meta layer for routing/audit/migration. Full per-layer breakdown, kept in sync
with the real skill count automatically:
[`skills/kmp-expert/SKILL.md`](skills/kmp-expert/SKILL.md)'s "The Skills and What They
Own" section. See [README.md](README.md) for the full map too.

---

## Versioning & Stability

```bash
npx skills add ronjunevaldoz/kmp-agent-skills
```

Or pin in `.kmp-skills`:
```json
{
  "skills_repo": "ronjunevaldoz/kmp-agent-skills",
  "version": "1.29.18"
}
```

[CHANGELOG.md](CHANGELOG.md) tracks what changed each release.

---

## File an Issue if Something's Wrong

<a name="when-to-file-here"></a>
**File here** if a skill gave wrong guidance or missed a case.

**File in your own repo** if you applied the guidance correctly and something in your project broke.

Use `/kmp-report-skill-issue` from Claude Code to file with the right template.
