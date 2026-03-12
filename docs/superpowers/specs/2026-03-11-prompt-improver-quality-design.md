# Prompt Improver Quality Improvements — Design Spec

**Date:** 2026-03-11
**Status:** Revised (v3)
**Scope:** `app.py` — `PromptAnalyzer` and `PromptBuilder` classes only. No UI changes. No new dependencies beyond stdlib.

---

## Problem Statement

The prompt-improver produces low-quality output for long, messy, or multi-goal inputs. Specific failures:

1. **No cleaning or summarization** — long prompts are echoed verbatim (truncated at 120 chars) rather than cleaned and summarized.
2. **Multi-goal prompts not split** — multiple distinct tasks (e.g., "plan my side hustle + review my AMEX card") collapse into a single task block.
3. **Finance/hustle domain undetected** — no domain signals for personal finance, credit cards, or side hustles → falls through to "knowledgeable assistant" role.
4. **Constraints bug** — `_constraints()` grabs a raw 150-char window around any word matching `limit/max/only/must`, pulling numeric facts (e.g., "$10,000 limit") into `[CONSTRAINTS]` instead of `[CONTEXT]`.
5. **Numeric facts missing from context** — dollar amounts, point thresholds, and timelines are not surfaced in `[CONTEXT]`.

---

## Architecture

All changes are confined to `app.py`. One new stdlib import: `import difflib` (add to the existing import block after `import re`).

### Affected components

| Component | Change |
|---|---|
| `import difflib` | New import, add after `import re` |
| Module-level constants | Add `_REQUEST_RE`, `_MULTITASK_SECTION3`, `_FACT_RE`, `_FACT_NOUN_RE`, `_DIRECTIVE_RE` |
| `PromptAnalyzer._summarize()` | New helper; returns `(summary, key_facts, normalized_sentences)` |
| `PromptAnalyzer._detect_tasks()` | New helper; takes normalized sentences, returns `(multi_task, task_sentences)` |
| `PromptAnalyzer.analyze()` | Call both helpers; add `summary`, `key_facts`, `multi_task`, `task_sentences` to returned dict |
| `_DOMAIN_SIGNALS` | Add `finance` domain keyword cluster before `business` cluster |
| `_DOMAIN_ROLES` | Add `finance` role entry |
| `PromptBuilder._context()` | Replace first block only; preserve domain context, tech stack, and audience lines |
| `PromptBuilder._task()` | Multi-task mode: emit numbered list before existing template logic |
| `PromptBuilder._format()` | Multi-task mode: emit sectioned markdown as fallback after `explicit_fmt` check |
| `PromptBuilder._constraints()` | Sentence-level extraction; discriminate facts from directives; preserve tone and smart defaults |
| `PromptBuilder.build()` | Update `is_long` warning condition |

---

## New Module-Level Constants

Add these alongside the existing `_BUILD_RE`, `_FIX_RE`, etc., in the regex constants block:

```python
import difflib  # add after `import re`

_REQUEST_RE = re.compile(
    r'^\s*(please\s+)?(what|how|why|when|can you|could you|help me|i need|i want|'
    r'tell me|look at|review|summarize|list|analyze|build|plan|check|explain|find|'
    r'show|give|create|make|write|compare|evaluate|assess)\b',
    re.I
)

_MULTITASK_SECTION3: dict[str, str] = {
    "finance":   "Financial review (card details, budget, key numbers)",
    "business":  "Business analysis (market, operations, strategy)",
    "backend":   "Technical review (architecture, APIs, data layer)",
    "frontend":  "UI/UX review (components, performance, accessibility)",
    "devops":    "Infrastructure review (deployment, reliability, costs)",
    "ai_ml":     "Model and data review (approach, evaluation, risks)",
    "security":  "Security review (threats, vulnerabilities, mitigations)",
    "data":      "Data review (sources, quality, pipeline)",
    "mobile":    "Platform review (iOS/Android, performance, UX)",
    "education": "Learning path review (resources, milestones, gaps)",
    "writing":   "Content review (tone, structure, audience fit)",
    "general":   "Deep dive on each subtopic",
}

# Used by _constraints() for fact vs. directive classification
_FACT_RE      = re.compile(r'[$\d]')
_FACT_NOUN_RE = re.compile(r'\b(limit|points|month|week|spend|miles|reward|budget|income|apr|bonus)\b', re.I)
_DIRECTIVE_RE = re.compile(r"\b(must|should|don'?t|do not|avoid|only|no more than|please don'?t|refrain|exclude|keep it|limit to)\b", re.I)
```

---

## Change 1: Text Cleaning, Summarization & Numeric Fact Extraction

### Sentence splitting

Reuse the existing module-level `_SENT_RE = re.compile(r"(?<=[.!?])\s+")` for all sentence splitting. Call `_SENT_RE.split(text)`, then strip and drop empty strings.

### New helper: `PromptAnalyzer._summarize(raw: str) -> tuple[str, list[str], list[str]]`

Returns `(summary_text, key_facts, normalized_sentences)`.

The `normalized_sentences` return value allows `analyze()` to pass the already-normalized sentence list to `_detect_tasks()`, avoiding duplicated splitting.

**Pipeline:**

1. **Sentence split:**
   ```python
   sentences = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
   ```

2. **Normalize each sentence:**
   - Collapse multiple spaces: `re.sub(r' {2,}', ' ', s)`
   - Fix `..` → `.`, `,,` → `,`
   - Remove word-duplication artifacts: `re.sub(r'\b(\w+)\s+\1\b', r'\1', s, flags=re.I)`

3. **Deduplicate near-identical sentences** using `difflib.SequenceMatcher`:
   - Maintain a `kept: list[str]` of accepted sentences.
   - For each normalized sentence, compare against every sentence already in `kept`.
   - If `SequenceMatcher(None, s.lower(), k.lower()).ratio() > 0.85` for any `k` in `kept` → discard.
   - Otherwise append to `kept`.

4. **Select summary sentences** (total cap: 4 sentences or 400 chars):
   - Maintain a `selected: list[str]` and a `selected_set: set[str]` (for O(1) duplicate checks across priority passes).
   - **P1 (always):** The first sentence in `kept`. Add unconditionally.
   - **P2 (up to 2 additional):** Sentences in `kept` that match `r'[$\d]'`. Skip any already in `selected_set`. Add up to 2, stopping if cap is reached.
   - **P3 (fill remaining):** Sentences in `kept` containing any `_DOMAIN_SIGNALS` keyword (check `if kw in s.lower()` for each keyword). Skip any already in `selected_set`. Add in order until cap is reached.
   - **P4 (fill remaining):** Any remaining `kept` sentences, skipping those already in `selected_set`, until cap is reached.
   - Cap is hit when `len(selected) >= 4` OR `sum(len(s) for s in selected) >= 400`.
   - `summary_text = " ".join(selected)`

5. **Extract key facts:**
   - From `kept`, find sentences matching `re.search(r'\$\d|[\d,]+\s*(point|limit|month|week|spend|mile|reward|apr|bonus)', s, re.I)`.
   - **Exclude any sentence already present in `selected`** (check `if s not in selected_set`).
   - Return as `key_facts: list[str]`.
   - This ensures `[CONTEXT]` never shows the same sentence twice — once in the summary and again in "Key details."

### `analyze()` integration

```python
summary, key_facts, norm_sents = self._summarize(raw)
multi_task, task_sentences = self._detect_tasks(norm_sents)
# Add to returned dict:
"summary":        summary,
"key_facts":      key_facts,
"multi_task":     multi_task,
"task_sentences": task_sentences,
```

### `PromptBuilder._context()` update

**Replace only the first block** (the `subject`/`verb_map`/`verb`/`lines.append` block). All subsequent blocks — domain context sentence injection, tech stack line, and audience line — remain unchanged and in their original order.

The `task_type` and `verb_map` local variables from the old block are no longer referenced by anything below in the method and can be removed.

Old first block:
```python
subject  = a.get("core_subject", raw.strip()[:100])
task_type = a["task_type"]
verb_map = { ... }
verb = verb_map.get(task_type, "work on")
lines.append(f"The goal is to {verb}: {subject}.")
```

New first block:
```python
summary = a.get("summary") or a.get("core_subject", raw.strip()[:100])
lines.append(summary)
if a.get("key_facts"):
    lines.append("Key details: " + " ".join(a["key_facts"]))
```

Everything after that in the existing method is unchanged.

### `PromptBuilder.build()` — update `is_long` warning

The existing warning fires whenever `is_long` is True. After `_summarize()`, every prompt produces a non-empty summary, so a naive `not analysis.get("summary")` check would permanently suppress the warning.

Instead, fire the warning only when summarization meaningfully truncated content — defined as the summary being less than 40% of the raw prompt length:

```python
# Old:
if analysis.get("is_long"):
    body += "\n\n⚠ Original prompt was very long; some elements were truncated."

# New:
if analysis.get("is_long"):
    summary_len = len(analysis.get("summary", ""))
    if summary_len < len(raw.strip()) * 0.4:
        body += "\n\n⚠ Original prompt was very long; key points were summarized above."
```

This preserves user feedback for genuinely long prompts while not spamming short ones.

---

## Change 2: Multi-task Detection

### New helper: `PromptAnalyzer._detect_tasks(sentences: list[str]) -> tuple[bool, list[str]]`

Takes the `normalized_sentences` list returned by `_summarize()`.

**Logic:**

```python
def _detect_tasks(self, sentences: list[str]) -> tuple[bool, list[str]]:
    request_sentences = [s for s in sentences if _REQUEST_RE.match(s)]
    multi_task = len(request_sentences) >= 2
    return multi_task, request_sentences[:5]
```

`_REQUEST_RE` is the module-level constant defined above.

### `PromptBuilder._task()` update

Add at the top of the method body, before the existing `subject = ...` line:

```python
if a.get("multi_task"):
    task_sents = a.get("task_sentences", [])
    numbered = "\n".join(f"{i+1}. {s.strip().rstrip('.')}." for i, s in enumerate(task_sents))
    return numbered
```

The existing single-template logic is untouched and runs only when `multi_task` is falsy.

### `PromptBuilder._format()` update

The check order must be: **`explicit_fmt` first**, then multi-task, then existing per-task-type logic. Explicit user input always wins.

```python
def _format(self, a: dict, explicit_fmt: str) -> str:
    # 1. Explicit user-supplied format always wins
    if explicit_fmt:
        key = self._clean(explicit_fmt).lower()
        expanded = _FMT_EXPANSIONS.get(key) or _FMT_EXPANSIONS.get(key.rstrip("s"))
        return expanded if expanded else explicit_fmt

    # 2. Multi-task mode: sectioned markdown
    if a.get("multi_task"):
        domain = a["domains"][0] if a["domains"] else "general"
        section3 = _MULTITASK_SECTION3.get(domain, _MULTITASK_SECTION3["general"])
        return (
            "Return a markdown document with:\n"
            "- Section 1: Summary of the current situation\n"
            "- Section 2: Action plan (prioritized steps, grouped by timeframe if applicable)\n"
            f"- Section 3: {section3}\n"
            "- Section 4: Integrated recommendations and risks"
        )

    # 3. Existing per-task-type logic — unchanged
    task_type = a["task_type"]
    domain    = a["domains"][0] if a["domains"] else "general"
    # ... rest of existing method unchanged ...
```

---

## Change 3: Finance Domain

### `_DOMAIN_ROLES` addition

Add before the `"general"` entry:

```python
"finance": (
    "an experienced small-business and personal-finance coach who helps people "
    "plan side hustles, manage budgets, and optimize credit-card and rewards strategies",
    "personal finance and small business"
),
```

### `_DOMAIN_SIGNALS` additions

Insert a `# finance` cluster **before the `# business` cluster**. Placing finance before business ensures that in a tie (equal keyword counts), Python's stable sort preserves insertion-order and `finance` signals encountered earlier may give finance a higher count for prompts with mixed signals. The precise tiebreaker is Python's `sorted(..., key=lambda k: -counts[k])` which is stable — if two domains have equal counts, the one whose first matching keyword appeared earlier in `_DOMAIN_SIGNALS` will come first.

```python
# finance
("finances",       "finance"), ("budget",         "finance"), ("spending",      "finance"),
("income",         "finance"), ("expenses",        "finance"), ("cash flow",     "finance"),
("credit card",    "finance"), ("amex",            "finance"), ("visa card",     "finance"),
("mastercard",     "finance"), (" apr ",           "finance"), ("points",        "finance"),
("miles",          "finance"), ("rewards card",    "finance"), ("signup bonus",  "finance"),
("side hustle",    "finance"), ("vending",         "finance"), ("net worth",     "finance"),
("savings account","finance"), ("student loan",    "finance"), ("credit limit",  "finance"),
```

**False-positive mitigations:**
- `" apr "` (space-padded) avoids matching "april" or "apricot"
- Phrase keywords (`"credit card"`, `"side hustle"`, `"savings account"`, `"student loan"`, `"credit limit"`, `"cash flow"`, `"rewards card"`, `"visa card"`, `"signup bonus"`, `"net worth"`) are specific enough that substring matching is safe
- `"vending"`, `"amex"`, `"mastercard"` are specific
- `"miles"` and `"points"` have minor false-positive risk but are contextually clear when combined with other finance signals; accepted trade-off

---

## Change 4: Context vs. Constraints Discrimination

### `PromptBuilder._constraints()` rewrite (first block only)

Replace the existing first block:
```python
if a["has_constraints"]:
    m = _CON_PAT.search(raw)
    if m:
        snippet = raw[m.start():m.start()+150].split("\n")[0].strip()
        parts.append(f"From original prompt: {snippet}")
```

With:
```python
if a["has_constraints"]:
    raw_sents = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
    directive_sentences = []
    for s in raw_sents:
        is_fact = bool(_FACT_RE.search(s)) and bool(_FACT_NOUN_RE.search(s))
        is_directive = bool(_DIRECTIVE_RE.search(s))
        if is_directive and not is_fact:
            directive_sentences.append(s[:120])
        elif is_directive and is_fact:
            # Both: extract only the directive clause
            # Slice to 100 chars from the directive keyword, then split on comma
            # The 100-char cap is applied to the slice input (before split),
            # guaranteeing output is ≤ 100 chars even when no comma is present.
            m = _DIRECTIVE_RE.search(s)
            if m:
                clause = s[m.start():m.start() + 100].split(",")[0].strip()
                directive_sentences.append(clause)
        if len(directive_sentences) >= 3:
            break
    for sent in directive_sentences:
        parts.append(f"From original prompt: {sent}")
```

`_FACT_RE`, `_FACT_NOUN_RE`, `_DIRECTIVE_RE` are used here as module-level constants (defined in the New Module-Level Constants section above).

**The tone injection block and all smart-default domain blocks that follow this extraction block are preserved exactly as-is.** Only the first `if a["has_constraints"]` block is replaced.

---

## Data Flow (Updated)

```
raw prompt
    ↓
PromptAnalyzer._summarize(raw)                   [reuses _SENT_RE]
    → summary (str), key_facts (list[str]), normalized_sentences (list[str])
    ↓
PromptAnalyzer._detect_tasks(normalized_sentences)
    → multi_task (bool), task_sentences (list[str])
    ↓
analyze() dict adds:
  summary, key_facts, multi_task, task_sentences
    ↓
PromptBuilder._context()     → summary + key_facts (no duplication: key_facts excludes summary sentences)
PromptBuilder._task()        → multi_task? → numbered list : existing single template
PromptBuilder._format()      → explicit_fmt first → multi_task → existing per-type logic
PromptBuilder._constraints() → sentence-level: directive-only sentences; tone and defaults preserved
PromptBuilder.build()        → is_long warning: fires only when summary < 40% of raw length
```

---

## Test Cases

### Test 1 — Long messy prompt
**Input:** Multi-paragraph prompt with duplicated sentences and grammar artifacts (e.g., "the the", "..", repeated sentences).
**Expected:**
- `[CONTEXT]` contains 3–4 cleaned, deduplicated sentences.
- No repeated phrases appear in output.
- `[CONTEXT]` "Key details" line does not repeat sentences already in the summary.

### Test 2 — Multi-goal prompt (vending + AMEX)
**Input:** Prompt asking to plan a vending-machine side hustle AND review AMEX card finances (containing "$10,000 limit", "15,000 points", "$6,000 spend in 3 months").
**Expected:**
- `[ROLE]` → finance coach persona.
- `[CONTEXT]` → cleaned summary + "Key details:" line with numeric facts (no duplication).
- `[TASK]` → numbered list with 2+ tasks.
- `[OUTPUT FORMAT]` → sectioned markdown with "Financial review" as Section 3.
- `[CONSTRAINTS]` → behavioral directives only; no dollar amounts or card numbers.

### Test 3 — Domain detection (finance)
**Input:** Short prompt containing "credit card", "points", "side hustle".
**Expected:** Finance domain detected → finance coach role.

### Test 4 — Simple build prompt (regression)
**Input:** `"Build a tic tac toe game in Python."`
**Expected:** Existing behavior preserved — no multi-task mode, single `build` template, code-oriented format, backend/general role.

### Test 5 — Single planning/design task (regression)
**Input:** `"Design a strategy for growing my newsletter to 10,000 subscribers."`
**Expected:** `multi_task = False` (only one request sentence). `_format()` uses the existing `design` task-type branch (sectioned technical template). Multi-task block is not triggered.

### Test 6 — Explicit format override with multi-task prompt
**Input:** Multi-task prompt with explicit format set to "bullets".
**Expected:** `[OUTPUT FORMAT]` uses the `bullets` expansion, not the multi-task template. Explicit user format wins.

---

## Out of Scope

- No changes to the UI, badge system, or Guide Me dialog.
- No changes to `_TECH_TERMS` or `_core_subject()`.
- No new external dependencies.
- No LLM calls — all logic is heuristic/regex/difflib.
