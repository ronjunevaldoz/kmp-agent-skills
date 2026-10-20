# Skills reference site

The site renders the repository's existing `skills/*/SKILL.md` files, builds a catalog
from the README skill groups, and adds a quality snapshot from the existing skill issue
scanner. The source skill files remain authoritative; generated pages are local build
output under `.generated/` and are not committed.

## Build and preview

From the repository root, create a Python virtual environment and install the site tools:

```powershell
python -m venv website/.venv
website/.venv/Scripts/python -m pip install -r website/requirements.txt
```

Generate and preview the site on Windows:

```powershell
website/.venv/Scripts/python scripts/build_skill_site.py
website/.venv/Scripts/mkdocs serve -f website/mkdocs.yml
```

On macOS or Linux, use the virtual environment's `bin` directory:

```bash
python3 -m venv website/.venv
website/.venv/bin/python -m pip install -r website/requirements.txt
website/.venv/bin/python scripts/build_skill_site.py
website/.venv/bin/mkdocs serve -f website/mkdocs.yml
```

Open the local address printed by MkDocs. To create a production-form build and check
internal links and navigation:

```powershell
website/.venv/Scripts/mkdocs build -f website/mkdocs.yml --strict
```

On macOS or Linux:

```bash
website/.venv/bin/mkdocs build -f website/mkdocs.yml --strict
```

The generator also runs automatically in the repository validation workflow before the
strict site build.

## What's in the site

- **Skills**: searchable pages rendered from `SKILL.md`, with each skill's references.
- **How skills are selected**: a generated view of `routing_rules.json` and its priority
  order.
- **Quality snapshot**: findings, severity totals, and actionable hints from
  `scripts/scan_skill_issues.py` at build time.

The quality page runs the existing issue scanner, repository audit, skill-map validator,
and keyword-routing validator. It does not prove that every technical recommendation is
correct; the repository workflow also runs the test suite.

## Maintenance

After changing skill pages or `routing_rules.json`, rebuild the site to refresh the
generated catalog, routing view, and quality snapshot:

```powershell
website/.venv/Scripts/python scripts/build_skill_site.py
```

The site uses a minimal MkDocs Material configuration with no third-party plugins. This
keeps the Markdown content and configuration easy to evaluate with Zensical as its
compatibility develops.
