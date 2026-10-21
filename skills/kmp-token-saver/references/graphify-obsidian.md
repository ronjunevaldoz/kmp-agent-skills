# Optional local Graphify and Git-backed Obsidian

Use this workflow for focused code relationship discovery and documentation that follows
a developer between machines. It adds no runtime dependency to the consumer project.

## Setup on each development machine

Install Python 3.10+ and [uv](https://docs.astral.sh/uv/), then install the reviewed CLI:

```text
uv tool install graphifyy==0.9.93
graphify --version
```

Ensure uv's tool binary directory is on PATH. The helper uses only Python's standard
library and checks the CLI version before processing source. On Windows use `py -3`
where the commands below use `python3`. No shell-specific environment syntax is needed.

Run the [helper](../scripts/graphify_local.py) from its maintained or deployed skill location. In examples,
`<helper>` means `skills/kmp-token-saver/scripts/graphify_local.py` inside the skills
checkout, or the corresponding deployed skill path. `<project>` is your current
consumer checkout; do not copy another machine's absolute paths into project docs.

```text
python3 <helper> build --root <project> --scope path/to/module
python3 <helper> query --root <project> --scope path/to/module --text "EntityArena allocation" --budget 1000
python3 <helper> explain --root <project> --scope path/to/module --text "src/commonMain/kotlin/example/Platform.kt::platformName()"
python3 <helper> export --root <project> --scope path/to/module
python3 <helper> info --root <project> --scope path/to/module
```

The same checkout and scope share a cache. Different paths, modules and worktrees get
separate caches. `info` prints the graph and generated vault locations. Cache files live
under the local OS cache directory, outside the repository; no ignore-file edit is needed.
Use the same scope for all commands. Start small rather than indexing an entire monorepo.

The helper sets `GRAPHIFY_BACKEND=none` and disables query logging only in its child
processes. Code-only extraction skips Markdown, PDFs and images; it does not pay a model
to interpret documentation. Clustering uses local labels. It never runs `graphify install`,
patches AGENTS.md, registers assistant hooks, starts a watcher or handles API keys.

Rebuild after edits, branch switches or pulling changes; extraction supports incremental
refresh. Queries do not automatically rebuild. Inspect the graph's source commit and
current source before relying on an edge. Generated files may be discarded and rebuilt.

## Obsidian development documentation

Use the repository's existing `docs/` folder as an Obsidian vault. Keep authored architecture
notes, API guides and decisions in Git, using ordinary relative Markdown links or GitHub
permalinks to source. A GitHub link works even on a device without that source checkout.
Do not create a second authoritative copy of the same documentation in a personal vault.

Commit and push notes before switching machines. Clone/pull on the other machine and open
its `docs/` folder as a vault. Keep machine-specific Obsidian layout files ignored, for example
these patterns in the consumer project's `.gitignore` when using `docs/` as the vault:

```gitignore
/docs/.obsidian/workspace*.json
/docs/.obsidian/cache/
```

Share other vault preferences only when the project wants them. Keep existing documentation
compatible with its normal renderer; Obsidian does not require converting it to wiki links.
Obsidian Sync and community plugins are optional; normal Git push/pull carries the docs.

The generated vault printed by `info` is separate from authored docs. Open it as a separate
vault for symbol graphs and Canvas. Do not nest it in the docs vault or commit its thousands
of generated notes. Regenerate it on the development machine where it is needed.

## Retrieval limits and evaluation

- Use a fresh scoped graph for relationships. Use `rg` for exact names and strings.
- Follow returned paths and inspect source before edits. `INFERRED` edges are hypotheses.
- Use path-qualified symbols when common and platform declarations share a name.
- Do not infer Gradle dependency wiring or compiler-level expect/actual matching from AST
  edges. In the Kotlin pilot, build scripts yielded no symbols and the common declaration's
  neighborhood did not link its platform actuals. Gradle/compiler checks remain authoritative.
- A broad World query in the pilot reached 546 nodes and truncated at a 1,000-token budget.
  Narrow the question or explain one symbol before increasing the approximate budget.
- Load only query output and the relevant source slices, not the full graph/report/vault.
- Compare useful source locations, correctness and context size on real tasks before claiming
  savings. No token-billing reduction percentage has been established by this workflow.

The helper is designed for Windows, macOS and Linux; record which hosts were actually tested.
The initial real CLI smoke test ran on Windows. Other hosts need a smoke test after setup.

Upstream references: [Graphify](https://github.com/Graphify-Labs/graphify),
[configuration](https://docs.graphify.com/reference/configuration),
[Obsidian file storage](https://help.obsidian.md/Files+and+folders/How+Obsidian+stores+data).
