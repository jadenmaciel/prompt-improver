# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python3.12 app.py
```

**Requirement:** Python 3.12 with Tkinter. On macOS, the system Python will not have `_tkinter`. Install via:
```bash
brew install python-tk@3.12
```

There are no external dependencies — stdlib only.

## Architecture

Single-file app (`app.py`, ~1050 lines). All logic, UI, and knowledge bases live in one file with no imports outside stdlib.

### Module-level globals (top of file)

- `C` — color palette dict (dark theme). All UI colors reference this.
- `F` — font dict, platform-branched (macOS: SF Pro/Menlo, Windows: Segoe/Consolas, Linux: DejaVu).
- `_TECH_TERMS` — dict mapping ~60 lowercase keywords → canonical display names, used for tech stack detection.
- `_DOMAIN_ROLES` — dict mapping domain keys → `(role_description, label)` tuples.
- `_DOMAIN_SIGNALS` — ordered list of `(keyword, domain_key)` tuples for domain classification.
- `_FMT_EXPANSIONS` — dict mapping format shorthands (`"bullets"`, `"json"`, `"table"`, etc.) to full prose descriptions.
- Regex constants: `_BUILD_RE`, `_DESIGN_RE`, `_EXPLAIN_RE`, `_COMPARE_RE`, `_FIX_RE`, `_ANALYZE_RE`, `_WRITE_RE`, `_LIST_RE` for task type; `_ROLE_PAT`, `_CTX_PAT`, `_FMT_PAT`, `_CON_PAT`, `_TASK_PAT` for structural presence detection.

### Classes

**`PromptAnalyzer`** — stateless, all class methods. `analyze(text) -> dict` is the entry point.

Returns: `has_role`, `has_context`, `has_task`, `has_output_format`, `has_constraints` (for badge display), plus `task_type`, `domains` (ordered list), `tech_stack` (list of canonical names), `is_technical`, `is_short`, `is_long`, `core_subject`.

Tech stack detection uses word-boundary regex (`\bkeyword\b`) to avoid false positives (e.g. "go" inside "mongo").

**`PromptBuilder`** — builds the improved prompt from a raw prompt + optional user fields.

- `build(prompt, audience, tone, fmt, constraints) -> str` is the entry point.
- `_clean(s)` — static helper, strips trailing `.!?,;:` before appending a period (prevents "Concise..").
- Private methods per section: `_role()`, `_context()`, `_task()`, `_input_section()`, `_output_format()`, `_constraints()`.
- Output format: `_format()` checks `_FMT_EXPANSIONS` for shorthand expansion before returning verbatim.
- Each section returns a `[SECTION NAME]\n...` block. Sections are joined with `\n\n`.
- `[INPUT]` section only emits when task_type is `fix`/`analyze` or prompt mentions "the following"/"below".

**`GuideMeDialog(tk.Toplevel)`** — 4-step modal dialog that walks user through audience → tone → format → constraints fields sequentially, with a Canvas progress strip.

**`PromptImproverApp`** — main application class.

- `_build_left()` — left panel: prompt input (`tk.Text`), badge strip (5 `tk.Label` widgets), Guide Me + Improve buttons.
- `_build_right()` — right panel: output `tk.Text` with `section_hdr` and `divider` tag configurations, Copy button.
- `_make_section(parent, title)` — helper that returns a styled section frame (header bar + content frame) instead of `tk.LabelFrame`.
- `_improve()` — calls `PromptAnalyzer.analyze()` then `PromptBuilder.build()`, inserts result into output widget, applies `section_hdr` tag to `[...]` lines and `divider` tag to `---` lines.
- Placeholder system: `_placeholder_active: dict[str, bool]` + `_setup_placeholder(entry, key, text)` — avoids `textvariable` to prevent placeholder text from showing selected/black on macOS.
- Scrollbars: `tk.Scrollbar` (not `ttk`) for dark theme styling; hidden entirely on macOS (trackpad), `<MouseWheel>` bound directly to text widgets.

### Data flow

```
raw prompt + options fields
        ↓
PromptAnalyzer.analyze()  →  analysis dict
        ↓
PromptBuilder.build()     →  improved prompt string
        ↓
_improve() applies text tags → output Text widget
```
