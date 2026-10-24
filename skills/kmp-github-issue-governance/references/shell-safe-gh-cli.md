# Shell-Safe GitHub CLI Transport

Part of `kmp-github-issue-governance`. Load this file when constructing automated `gh` commands or writing markdown payloads from scripts.

---

## 1. The Anatomy of GitHub CLI Quoting Traps

Passing markdown payloads directly through `-b "..."` or `--body "$STR"` in bash, zsh, or Python `subprocess.run(["gh", "...", "-b", text])` fails in two catastrophic ways:

### Failure Mode 1: Subshell Command Execution & Backtick Stripping

When executing:
```bash
# BROKEN
gh issue comment 27 -b "Fixed on `refactor/studio-authoring-boundaries` branch"
```

1. The shell sees double quotes (`"..."`) and evaluates all parameter expansions and backtick command substitutions inside them.
2. The shell attempts to execute `refactor/studio-authoring-boundaries` as a terminal executable.
3. Because the command does not exist (or errors), the shell replaces it with an empty string.
4. GitHub receives:
   ```
   Fixed on  branch
   ```
   The identifier is completely stripped!

### Failure Mode 2: Escaped Newline Strings (`\n\n`)

When constructing text in Python, Node.js, or shell:
```python
# BROKEN
body = "Line 1\\n\\nLine 2"
subprocess.run(["gh", "issue", "create", "-b", body])
```
If newlines are escaped as literal two-character sequences (`\\` and `n`), `gh` encodes them as literal characters. GitHub Markdown displays `\n\n` as text rather than rendering a blank line break.

### Failure Mode 3: PowerShell Backtick Escapes (`@"..."@`) & Windows Codepage (`cp1252`) Mojibake

On Windows PowerShell, passing markdown inside double quotes (`"..."`) or a double-quoted here-string (`@"..."@`) corrupts inline code spans and Unicode punctuation:
1. PowerShell uses the backtick (`` ` ``) as its escape character inside double quotes:
   - `` `a `` becomes ASCII BEL (`\x07`, rendered as a control box `\u0007`), e.g. `` `app/dashboard` `` becomes `\u0007pp/dashboard`.
   - `` `b `` becomes ASCII Backspace (`\x08`), `` `f `` becomes Form Feed (`\x0c`), `` `v `` becomes Vertical Tab (`\x0b`), `` `0 `` becomes NUL (`\x00`), and `` `n `` / `` `r `` / `` `t `` become control whitespace.
   - Closing backticks before spaces or punctuation are silently stripped, leaving even-numbered backtick counts when an even number of code spans are eaten.
2. Non-ASCII punctuation (em-dashes `—`, en-dashes `–`, smart quotes, `→`, `×`) passed through `cp1252` console pipes or CLI arguments turns into mojibake (`â€”`, `â€“`, `â†’`, `Ã—`).
3. **Rule**: Never pass `--body @"..."@` in PowerShell. Write the payload to a UTF-8 file using plain ASCII punctuation (`-`, `--`, `->`, `x`), validate it with `validate_issue_payload.py`, and pass `--body-file`.

---

## 2. The Golden Rule: Always Use `--body-file`

The GitHub CLI provides the `--body-file` flag across `gh issue create`, `gh issue comment`, `gh pr create`, and `gh pr comment`. `--body-file` reads bytes directly from disk or standard input, bypassing shell expansion completely.

### Recipe 1: Temporary File (Universal & Safest)

```bash
# Create temporary file
PAYLOAD_FILE=$(mktemp /tmp/gh-payload-XXXXXX.md)

# Write multiline text safely (quoted EOF disables all parameter/backtick evaluation)
cat <<'EOF' > "$PAYLOAD_FILE"
### Summary
Refactored `StudioWorkspaceHost` to isolate `Game` play sessions.

### Evidence
- Passes on branch `refactor/studio-authoring-boundaries`.
- Benchmark shows 0% regression in FPS.
EOF

# Transmit to GitHub
gh issue comment 27 --body-file "$PAYLOAD_FILE"

# Clean up
rm -f "$PAYLOAD_FILE"
```

### Recipe 2: Quoted Heredoc Stdin (`--body-file -`)

`--body-file -` instructs `gh` to read the entire body from standard input:

```bash
cat <<'EOF' | gh issue comment 27 --body-file -
### Status
Completed implementation in commit `712cc39`.
All desktop tests pass:
- `StudioPlayModeTest`
- `StudioShellLayoutTest`
EOF
```

> [!IMPORTANT]
> The single quotes around `'EOF'` are mandatory. Without quotes (`cat <<EOF`), the shell will expand backticks and variables!

### Recipe 3: Python `subprocess` with Tempfile

```python
import subprocess
import tempfile

def submit_comment(issue_num: int, markdown_text: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(markdown_text)
        temp_path = f.name

    try:
        subprocess.run(
            ["gh", "issue", "comment", str(issue_num), "--body-file", temp_path],
            check=True,
        )
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

---

## 3. In-Place Comment Updates (API Patch)

To prevent spamming an issue with 9 status comments, update an existing comment in place:

```bash
# 1. Fetch latest comment ID posted by current user
COMMENT_ID=$(gh api "repos/{owner}/{repo}/issues/27/comments" \
  --jq '[.[] | select(.user.login == "bot-or-user")] | last | .id')

# 2. Update comment in place using a safe payload
gh api -X PATCH "repos/{owner}/{repo}/issues/comments/$COMMENT_ID" \
  --input /tmp/status-update.json
```

Where `/tmp/status-update.json` contains:
```json
{
  "body": "### Status: IMPLEMENTED\n\nAll tests passing on Desktop and Wasm."
}
```
*(In JSON payloads, `\n` is valid JSON escape for real newline, and backticks are preserved).*
