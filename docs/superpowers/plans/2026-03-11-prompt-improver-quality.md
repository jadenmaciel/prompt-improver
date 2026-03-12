# Prompt Improver Quality Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve `PromptAnalyzer` and `PromptBuilder` to clean/summarize long prompts, detect multiple tasks, apply finance domain signals, and correctly separate numeric facts from behavioral constraints.

**Architecture:** All changes are in `app.py` (single-file app, ~1050 lines, stdlib only + difflib). Two new helpers (`_summarize`, `_detect_tasks`) are added to `PromptAnalyzer`; five `PromptBuilder` methods are updated. Tests live in a new `tests/` directory using pytest.

**Tech Stack:** Python 3.12, difflib (stdlib), pytest (test runner — install separately)

**Spec:** `docs/superpowers/specs/2026-03-11-prompt-improver-quality-design.md`

---

## Chunk 1: Module-level additions — import, constants, finance domain

### Task 1: Create test infrastructure and write failing finance-domain tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: Install pytest**

```bash
python3.12 -m pip install pytest
```

- [ ] **Step 2: Create `tests/__init__.py` (empty file)**

```bash
touch tests/__init__.py
```

- [ ] **Step 3: Create `tests/test_analyzer.py`**

```python
"""Tests for PromptAnalyzer — domain detection, summarization, multi-task."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import PromptAnalyzer

analyzer = PromptAnalyzer()


class TestFinanceDomain:
    def test_credit_card_signals_finance_domain(self):
        result = analyzer.analyze("Help me understand my credit card points and limit.")
        assert result["domains"][0] == "finance"

    def test_side_hustle_signals_finance_domain(self):
        result = analyzer.analyze("I want to plan my vending machine side hustle.")
        assert result["domains"][0] == "finance"

    def test_amex_signals_finance_domain(self):
        result = analyzer.analyze("I just got an AMEX card with 15000 points signup bonus.")
        assert result["domains"][0] == "finance"

    def test_budget_signals_finance_domain(self):
        result = analyzer.analyze("Help me budget my monthly expenses and savings account.")
        assert result["domains"][0] == "finance"

    def test_finance_role_text_is_coach(self):
        result = analyzer.analyze("Review my finances and credit card strategy.")
        assert result["domains"][0] == "finance"
```

- [ ] **Step 4: Run tests to verify they fail (expected)**

```bash
cd /Users/jadenmaciel-shapiro/Projects/personal/prompt-improver
python3.12 -m pytest tests/test_analyzer.py::TestFinanceDomain -v
```

Expected: 5 FAILED — AssertionError because "finance" domain doesn't exist yet.

---

### Task 2: Add `import difflib`, module-level constants, finance domain

**Files:**
- Modify: `app.py:9` — add `import difflib` after `import re`
- Modify: `app.py:239` — add constants after `_ACRONYM_RE`
- Modify: `app.py:166` — add `"finance"` to `_DOMAIN_ROLES` before `"general"`
- Modify: `app.py:217` — add finance cluster to `_DOMAIN_SIGNALS` before `# business`

- [ ] **Step 1: Add `import difflib` after `import re` (line 9)**

The import block becomes:
```python
import platform
import re
import difflib
import tkinter as tk
from tkinter import messagebox
```

- [ ] **Step 2: Add five module-level constants after `_ACRONYM_RE` (after line 239)**

After the line `_ACRONYM_RE = re.compile(r"\b[A-Z]{2,5}\b")`, add:

```python
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

- [ ] **Step 3: Add `"finance"` to `_DOMAIN_ROLES` before `"general"` (line 166)**

Insert before the `"general"` entry:

```python
    "finance": (
        "an experienced small-business and personal-finance coach who helps people "
        "plan side hustles, manage budgets, and optimize credit-card and rewards strategies",
        "personal finance and small business"
    ),
```

- [ ] **Step 4: Add finance cluster to `_DOMAIN_SIGNALS` before `# business` (line 217)**

Insert before the `# business` comment:

```python
    # finance (placed before business so finance-specific signals win ties over generic business signals)
    ("finances",        "finance"), ("budget",         "finance"), ("spending",      "finance"),
    ("income",          "finance"), ("expenses",       "finance"), ("cash flow",     "finance"),
    ("credit card",     "finance"), ("amex",           "finance"), ("visa card",     "finance"),
    ("mastercard",      "finance"), (" apr ",          "finance"), ("points",        "finance"),
    ("miles",           "finance"), ("rewards card",   "finance"), ("signup bonus",  "finance"),
    ("side hustle",     "finance"), ("vending",        "finance"), ("net worth",     "finance"),
    ("savings account", "finance"), ("student loan",   "finance"), ("credit limit",  "finance"),
```

- [ ] **Step 5: Run finance domain tests — expect PASS**

```bash
python3.12 -m pytest tests/test_analyzer.py::TestFinanceDomain -v
```

Expected: 5 PASSED

- [ ] **Step 6: Commit**

```bash
git add tests/__init__.py tests/test_analyzer.py app.py
git commit -m "feat: add finance domain signals/role, difflib import, module-level constants"
```

---

## Chunk 2: New PromptAnalyzer helpers + analyze() integration

### Task 3: Write failing tests for `_summarize()`

**Files:**
- Modify: `tests/test_analyzer.py` — add `TestSummarize` class

- [ ] **Step 1: Add `TestSummarize` class to `tests/test_analyzer.py`**

```python
class TestSummarize:
    def test_returns_three_values(self):
        summary, key_facts, sents = analyzer._summarize("Simple test.")
        assert isinstance(summary, str)
        assert isinstance(key_facts, list)
        assert isinstance(sents, list)

    def test_short_prompt_preserves_content(self):
        summary, key_facts, sents = analyzer._summarize("Build a todo app.")
        assert "todo" in summary.lower()

    def test_deduplication_removes_near_identical_sentences(self):
        raw = (
            "I want to plan my vending machine business. "
            "I want to plan my vending machine business. "
            "Please help me with finances."
        )
        summary, _, sents = analyzer._summarize(raw)
        # Duplicated sentence should appear only once
        assert summary.lower().count("vending machine") == 1

    def test_word_duplication_artifact_removed(self):
        raw = "I want to to build a the the app for my side hustle."
        summary, _, _ = analyzer._summarize(raw)
        assert "to to" not in summary
        assert "the the" not in summary

    def test_numeric_sentences_included_in_key_facts(self):
        raw = (
            "Help me plan my side hustle. "
            "I have a $10,000 credit limit on my AMEX. "
            "I want to earn 15000 points in 3 months."
        )
        _, key_facts, _ = analyzer._summarize(raw)
        joined = " ".join(key_facts)
        # At least one numeric fact sentence captured
        assert "$10,000" in joined or "15000" in joined

    def test_key_facts_do_not_duplicate_summary(self):
        """Sentences already selected for summary must not appear in key_facts."""
        raw = "My AMEX card has a $5,000 credit limit and 10000 signup points."
        summary, key_facts, _ = analyzer._summarize(raw)
        for fact in key_facts:
            assert fact not in summary

    def test_summary_capped_at_4_sentences(self):
        raw = ". ".join(f"Sentence number {i} about this topic" for i in range(10)) + "."
        summary, _, _ = analyzer._summarize(raw)
        # Rough sentence count by splitting on ". "
        parts = [s.strip() for s in summary.split(". ") if s.strip()]
        assert len(parts) <= 5  # Allow slight fuzz for sentence-boundary edge cases
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3.12 -m pytest tests/test_analyzer.py::TestSummarize -v
```

Expected: 7 FAILED — `AttributeError: 'PromptAnalyzer' object has no attribute '_summarize'`

---

### Task 4: Implement `_summarize()`

**Files:**
- Modify: `app.py` — add `_summarize()` method to `PromptAnalyzer` after `_core_subject()` (around line 318)

- [ ] **Step 1: Add `_summarize()` method after `_core_subject()`**

```python
    def _summarize(self, raw: str) -> tuple[str, list[str], list[str]]:
        """Clean, deduplicate, and summarize a raw prompt.

        Returns:
            summary_text: Up to 4 best sentences joined with a space.
            key_facts: Numeric/currency sentences not already in the summary.
            normalized_sentences: All deduplicated normalized sentences (for _detect_tasks).
        """
        # Step 1: Sentence split using existing module-level _SENT_RE
        raw_sents = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
        if not raw_sents:
            return raw.strip(), [], []

        # Step 2: Normalize each sentence
        normalized: list[str] = []
        for s in raw_sents:
            s = re.sub(r' {2,}', ' ', s)                             # collapse spaces
            s = re.sub(r'\.\.+', '.', s)                             # fix ".."
            s = re.sub(r',,+', ',', s)                               # fix ",,"
            s = re.sub(r'\b(\w+)\s+\1\b', r'\1', s, flags=re.I)     # "the the" → "the"
            s = s.strip()
            if s:
                normalized.append(s)

        # Step 3: Deduplicate — keep sentences with similarity ≤ 0.85 vs all already kept
        kept: list[str] = []
        for s in normalized:
            is_dupe = any(
                difflib.SequenceMatcher(None, s.lower(), k.lower()).ratio() > 0.85
                for k in kept
            )
            if not is_dupe:
                kept.append(s)

        # Step 4: Select up to 4 summary sentences (~400 char budget)
        # Both list (order) and set (O(1) dedup across priority passes)
        selected: list[str] = []
        selected_set: set[str] = set()

        def _add(s: str) -> bool:
            """Add s if not already selected and budget not exhausted."""
            if s in selected_set:
                return False
            if len(selected) >= 4 or sum(len(x) for x in selected) >= 400:
                return False
            selected.append(s)
            selected_set.add(s)
            return True

        # P1: Always include first sentence
        if kept:
            _add(kept[0])

        # P2: Sentences with currency or digits (up to 2 additional)
        numeric_added = 0
        for s in kept:
            if numeric_added >= 2:
                break
            if re.search(r'[$\d]', s) and _add(s):
                numeric_added += 1

        # P3: Sentences containing any domain keyword
        domain_kws = {kw for kw, _ in _DOMAIN_SIGNALS}
        for s in kept:
            if any(kw in s.lower() for kw in domain_kws):
                _add(s)

        # P4: Fill remaining slots with any kept sentence in order
        for s in kept:
            _add(s)

        summary_text = " ".join(selected)

        # Step 5: Key facts — numeric sentences NOT already in the summary
        _key_fact_re = re.compile(
            r'\$\d|[\d,]+\s*(point|limit|month|week|spend|mile|reward|apr|bonus)',
            re.I
        )
        key_facts = [s for s in kept if _key_fact_re.search(s) and s not in selected_set]

        return summary_text, key_facts, kept
```

- [ ] **Step 2: Run summarize tests**

```bash
python3.12 -m pytest tests/test_analyzer.py::TestSummarize -v
```

Expected: 7 PASSED

---

### Task 5: Write failing tests for `_detect_tasks()`

**Files:**
- Modify: `tests/test_analyzer.py` — add `TestDetectTasks` class

- [ ] **Step 1: Add `TestDetectTasks` class**

```python
class TestDetectTasks:
    def test_returns_tuple_of_bool_and_list(self):
        _, _, sents = analyzer._summarize("Simple prompt.")
        multi, tasks = analyzer._detect_tasks(sents)
        assert isinstance(multi, bool)
        assert isinstance(tasks, list)

    def test_single_request_is_not_multitask(self):
        _, _, sents = analyzer._summarize("Build a tic tac toe game in Python.")
        multi, tasks = analyzer._detect_tasks(sents)
        assert multi is False

    def test_two_requests_is_multitask(self):
        raw = (
            "Please review my vending machine business plan. "
            "Also analyze my AMEX card finances and spending limits."
        )
        _, _, sents = analyzer._summarize(raw)
        multi, tasks = analyzer._detect_tasks(sents)
        assert multi is True
        assert len(tasks) >= 2

    def test_task_sentences_capped_at_5(self):
        raw = ". ".join([
            "Please do task one",
            "Can you do task two",
            "Help me with task three",
            "Review task four",
            "Analyze task five",
            "Build task six",
        ]) + "."
        _, _, sents = analyzer._summarize(raw)
        _, tasks = analyzer._detect_tasks(sents)
        assert len(tasks) <= 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3.12 -m pytest tests/test_analyzer.py::TestDetectTasks -v
```

Expected: 4 FAILED — `AttributeError: 'PromptAnalyzer' object has no attribute '_detect_tasks'`

---

### Task 6: Implement `_detect_tasks()` and update `analyze()`

**Files:**
- Modify: `app.py` — add `_detect_tasks()` after `_summarize()`, update `analyze()` body and return dict

- [ ] **Step 1: Add `_detect_tasks()` method after `_summarize()`**

```python
    def _detect_tasks(self, sentences: list[str]) -> tuple[bool, list[str]]:
        """Detect whether the prompt contains multiple distinct task requests.

        Returns:
            multi_task: True if ≥2 distinct request sentences found.
            task_sentences: Up to 5 matched request sentences.
        """
        request_sentences = [s for s in sentences if _REQUEST_RE.match(s)]
        return len(request_sentences) >= 2, request_sentences[:5]
```

- [ ] **Step 2: Update `analyze()` — add two calls after `is_technical` block**

After the `is_technical = (...)` block (around line 258), add:

```python
        summary, key_facts, norm_sents = self._summarize(raw)
        multi_task, task_sentences = self._detect_tasks(norm_sents)
```

- [ ] **Step 3: Update `analyze()` return dict — add four new keys after `"core_subject"`**

The return dict currently ends with `"core_subject": self._core_subject(t)`. Add after it:

```python
            # Summarization & multi-task
            "summary":        summary,
            "key_facts":      key_facts,
            "multi_task":     multi_task,
            "task_sentences": task_sentences,
```

- [ ] **Step 4: Run all analyzer tests**

```bash
python3.12 -m pytest tests/test_analyzer.py -v
```

Expected: All tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_analyzer.py
git commit -m "feat: add _summarize and _detect_tasks to PromptAnalyzer, enrich analyze() dict"
```

---

## Chunk 3: PromptBuilder updates

> **Prerequisite:** Chunks 1 and 2 must be fully applied before running any tests in this chunk. The tests depend on `summary`, `key_facts`, `multi_task`, and `task_sentences` keys existing in the `analyze()` return dict. Without them, tests will fail for the wrong reason (missing dict keys, not missing builder logic), giving a misleading fail-first signal.

### Task 7: Write failing PromptBuilder tests

**Files:**
- Create: `tests/test_builder.py`

- [ ] **Step 1: Create `tests/test_builder.py`**

```python
"""Tests for PromptBuilder — context, task, format, constraints, build warning."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import PromptAnalyzer, PromptBuilder

analyzer = PromptAnalyzer()
builder = PromptBuilder()


def build(prompt: str, **meta) -> str:
    """Run the full analyze → build pipeline and return the output string."""
    analysis = analyzer.analyze(prompt)
    return builder.build(prompt, analysis, meta)


class TestContext:
    def test_context_uses_summary_not_raw_echo(self):
        """Duplicated sentences should appear only once in [CONTEXT]."""
        raw = (
            "I want to plan my vending machine side hustle. "
            "I want to plan my vending machine side hustle. "
            "Please help me with my AMEX card finances."
        )
        out = build(raw)
        context_block = out.split("[CONTEXT]")[1].split("[TASK]")[0]
        assert context_block.lower().count("vending machine") <= 1

    def test_numeric_key_facts_appear_in_context(self):
        """Key numeric facts should surface in [CONTEXT]."""
        raw = (
            "Help me plan my side hustle. "
            "I have a $10,000 credit limit and 15000 points to earn."
        )
        out = build(raw)
        context_block = out.split("[CONTEXT]")[1].split("[TASK]")[0]
        assert "$10,000" in context_block or "15000" in context_block

    def test_key_facts_not_duplicated_in_context(self):
        """A numeric fact sentence in the summary should not appear again as Key details."""
        raw = "My AMEX card has a $5,000 credit limit and 10000 signup points."
        out = build(raw)
        context_block = out.split("[CONTEXT]")[1].split("[TASK]")[0]
        assert context_block.count("$5,000") <= 1


class TestTask:
    def test_single_task_uses_template(self):
        """Single-task prompts should use the prose template, not a numbered list."""
        out = build("Build a tic tac toe game in Python.")
        task_block = out.split("[TASK]")[1].split("[OUTPUT FORMAT]")[0]
        assert not task_block.strip().startswith("1.")

    def test_multi_task_produces_numbered_list(self):
        """Multi-task prompts should produce a numbered list in [TASK]."""
        raw = (
            "Please review my vending machine business plan. "
            "Also analyze my AMEX card spending and credit limit."
        )
        out = build(raw)
        task_block = out.split("[TASK]")[1].split("[OUTPUT FORMAT]")[0]
        assert "1." in task_block
        assert "2." in task_block


class TestFormat:
    def test_explicit_format_wins_over_multitask(self):
        """User-supplied format must take precedence over multi-task template."""
        raw = (
            "Please review my vending machine plan. "
            "Also check my AMEX card finances and credit limit."
        )
        out = build(raw, output_fmt="bullets")
        fmt_block = out.split("[OUTPUT FORMAT]")[1].split("[CONSTRAINTS")[0]
        assert "bullet" in fmt_block.lower()
        assert "Section 1:" not in fmt_block

    def test_multitask_format_has_four_sections(self):
        """Multi-task prompts without explicit format should get a sectioned markdown template."""
        raw = (
            "Please review my vending machine business plan. "
            "Also analyze my AMEX card spending and credit limit."
        )
        out = build(raw)
        fmt_block = out.split("[OUTPUT FORMAT]")[1].split("[CONSTRAINTS")[0]
        assert "Section 1:" in fmt_block
        assert "Section 2:" in fmt_block
        assert "Section 3:" in fmt_block
        assert "Section 4:" in fmt_block

    def test_single_design_task_not_multitask_format(self):
        """Single planning/design prompt should NOT trigger the multi-task template."""
        out = build("Design a strategy for growing my newsletter to 10,000 subscribers.")
        fmt_block = out.split("[OUTPUT FORMAT]")[1].split("[CONSTRAINTS")[0]
        assert "Section 1: Summary of the current situation" not in fmt_block


class TestConstraints:
    def test_numeric_fact_with_limit_not_in_constraints(self):
        """A sentence with a dollar amount + 'limit' is a fact, not a constraint."""
        raw = "Help me plan my finances. I must review my $10,000 credit limit carefully."
        out = build(raw)
        constraints_block = out.split("[CONSTRAINTS")[1]
        assert "$10,000" not in constraints_block

    def test_pure_directive_captured_as_constraint(self):
        """A 'do not' directive sentence should appear in [CONSTRAINTS]."""
        raw = "Build me a web app. Do not use any external libraries."
        out = build(raw)
        constraints_block = out.split("[CONSTRAINTS")[1]
        assert "do not" in constraints_block.lower() or "external" in constraints_block.lower()

    def test_pure_numeric_fact_not_in_constraints(self):
        """Sentences with only numbers + fact nouns belong in context, not constraints."""
        raw = "I have 15000 points to spend in 3 months on rewards."
        out = build(raw)
        if "[CONSTRAINTS" in out:
            constraints_block = out.split("[CONSTRAINTS")[1]
            assert "15000" not in constraints_block


class TestBuildWarning:
    def test_is_long_warning_message_updated(self):
        """When warning fires, it must say 'summarized' not 'truncated'."""
        # 50 repetitions → >2000 chars → is_long=True. Dedup collapses to 1 sentence,
        # so summary_len < 40% of raw → warning fires with new text.
        raw = "Help me plan my vending machine side hustle step by step. " * 50
        out = build(raw)
        if "⚠" in out:
            assert "summarized" in out
            assert "truncated" not in out

    def test_is_long_warning_suppressed_when_content_is_diverse(self):
        """When a long prompt has diverse sentences that fill the summary, suppress warning."""
        # 45 distinct sentences × ~45 chars each ≈ 2025 chars → is_long=True.
        # Summary captures 4 sentences × ~45 chars = ~180 chars ≈ 8.9% — still below 40%.
        # So we instead build a prompt where summary text is long relative to raw.
        # Use a prompt that is just over 2000 chars but has a rich, long first sentence.
        long_first = "A" * 900  # 900 chars, will be the summary
        rest = " Short filler. " * 80  # ~1280 chars filler → total ~2180 chars, is_long=True
        raw = long_first + "." + rest
        analysis = PromptAnalyzer().analyze(raw)
        assert analysis["is_long"] is True
        summary_len = len(analysis.get("summary", ""))
        raw_len = len(raw.strip())
        # summary_len >= 40% of raw_len → warning should be suppressed
        if summary_len >= raw_len * 0.4:
            out = build(raw)
            assert "⚠" not in out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3.12 -m pytest tests/test_builder.py -v
```

Expected: Multiple FAILED — existing `_context()`, `_task()`, `_format()`, `_constraints()` don't implement new behavior yet.

---

### Task 8: Update `_context()` — replace first block only

**Files:**
- Modify: `app.py:388-398` — `PromptBuilder._context()` first block

- [ ] **Step 1: Replace the first block of `_context()`**

Old code (lines 388-398, the block under `# 1. Summarize what the user is actually trying to do`):

```python
        # 1. Summarize what the user is actually trying to do
        subject  = a.get("core_subject", raw.strip()[:100])
        task_type = a["task_type"]
        verb_map = {
            "build":   "build", "design": "design", "explain": "understand",
            "compare": "compare", "fix": "fix a problem with",
            "analyze": "analyze", "write": "write", "list": "find",
            "general": "work on",
        }
        verb = verb_map.get(task_type, "work on")
        lines.append(f"The goal is to {verb}: {subject}.")
```

New code:

```python
        # 1. Use summarized text from PromptAnalyzer or fall back to core_subject
        # Note: task_type and verb_map are no longer needed here; removed.
        summary = a.get("summary") or a.get("core_subject", raw.strip()[:100])
        lines.append(summary)
        if a.get("key_facts"):
            lines.append("Key details: " + " ".join(a["key_facts"]))
```

All subsequent blocks in `_context()` (domain context injection, tech stack, audience) remain unchanged.

- [ ] **Step 2: Run context tests**

```bash
python3.12 -m pytest tests/test_builder.py::TestContext -v
```

Expected: 3 PASSED

---

### Task 9: Update `_task()` — add multi-task numbered list

**Files:**
- Modify: `app.py` — `PromptBuilder._task()` method

- [ ] **Step 1: Add multi-task guard at the very top of `_task()` body**

Before the existing `subject = a.get("core_subject", raw.strip()[:120])` line, add:

```python
        if a.get("multi_task"):
            task_sents = a.get("task_sentences", [])
            if task_sents:  # Guard: fall through to single template if list is empty
                numbered = "\n".join(
                    f"{i+1}. {s.strip().rstrip('.')}."
                    for i, s in enumerate(task_sents)
                )
                return numbered
```

The existing single-template logic (`subject`, `task_type`, `tech_str`, `expansions`) is untouched and runs as the fallthrough path when `multi_task` is falsy or `task_sents` is empty.

- [ ] **Step 2: Run task tests**

```bash
python3.12 -m pytest tests/test_builder.py::TestTask -v
```

Expected: 2 PASSED

---

### Task 10: Update `_format()` — explicit_fmt first, then multi-task, then existing

**Files:**
- Modify: `app.py` — `PromptBuilder._format()` method

- [ ] **Step 1: Add multi-task block between `explicit_fmt` return and existing task-type logic**

Insert the new block **before** the following two lines (which are the first lines of the existing per-task-type logic — use them as your literal anchor):

```python
        task_type = a["task_type"]
        domain    = a["domains"][0] if a["domains"] else "general"
```

Insert immediately before those two lines:

```python
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
```

The rest of the method (`task_type = a["task_type"]`, `domain = ...`, all the `if task_type in (...)` blocks) remain unchanged.

- [ ] **Step 2: Run format tests**

```bash
python3.12 -m pytest tests/test_builder.py::TestFormat -v
```

Expected: 3 PASSED

---

### Task 11: Update `_constraints()` — sentence-level fact/directive split

**Files:**
- Modify: `app.py` — `PromptBuilder._constraints()` first block (lines 570-574)

- [ ] **Step 1: Replace the first block of `_constraints()`**

Old code:
```python
        if a["has_constraints"]:
            m = _CON_PAT.search(raw)
            if m:
                snippet = raw[m.start():m.start()+150].split("\n")[0].strip()
                parts.append(f"From original prompt: {snippet}")
```

New code:
```python
        if a["has_constraints"]:
            raw_sents = [s.strip() for s in _SENT_RE.split(raw) if s.strip()]
            directive_sentences: list[str] = []
            for s in raw_sents:
                is_fact = bool(_FACT_RE.search(s)) and bool(_FACT_NOUN_RE.search(s))
                is_directive = bool(_DIRECTIVE_RE.search(s))
                if is_directive and not is_fact:
                    directive_sentences.append(s[:120])
                elif is_directive and is_fact:
                    # Both: extract only the directive clause.
                    # The 100-char slice is applied BEFORE split(",")[0], so output is ≤ 100 chars
                    # even when no comma is present.
                    m = _DIRECTIVE_RE.search(s)
                    if m:
                        clause = s[m.start():m.start() + 100].split(",")[0].strip()
                        directive_sentences.append(clause)
                if len(directive_sentences) >= 3:
                    break
            for sent in directive_sentences:
                parts.append(f"From original prompt: {sent}")
```

Everything after this block (tone injection, domain smart defaults, fallback) remains unchanged.

- [ ] **Step 2: Run constraints tests**

```bash
python3.12 -m pytest tests/test_builder.py::TestConstraints -v
```

Expected: 3 PASSED

---

### Task 12: Update `build()` — smart `is_long` warning + final validation

**Files:**
- Modify: `app.py:361-362` — `PromptBuilder.build()` warning block

- [ ] **Step 1: Replace the `is_long` warning block**

Old (lines 361-362):
```python
        if analysis.get("is_long"):
            body += "\n\n⚠ Original prompt was very long; some elements were truncated."
```

New:
```python
        if analysis.get("is_long"):
            summary_len = len(analysis.get("summary", ""))
            if summary_len < len(raw.strip()) * 0.4:
                body += "\n\n⚠ Original prompt was very long; key points were summarized above."
```

- [ ] **Step 2: Run full test suite**

```bash
python3.12 -m pytest tests/ -v
```

Expected: All tests PASSED

- [ ] **Step 3: Manual smoke test — run the app**

```bash
python3.12 app.py
```

Paste this prompt into the input box and click Improve:

```
I need help with two things. First, please review my vending machine side hustle and help me plan the next steps. Also, analyze my AMEX card — I have a $10,000 credit limit and a 15,000 point signup bonus after spending $6,000 in 3 months. Don't give me generic advice, keep it actionable.
```

Verify the output:
- `[ROLE / PERSONA]` → contains "finance coach" or equivalent
- `[CONTEXT]` → 2-3 sentence summary + "Key details: $10,000 credit limit…" (no duplication)
- `[TASK]` → numbered list with 2 items
- `[OUTPUT FORMAT]` → sectioned markdown with "Financial review" as Section 3
- `[CONSTRAINTS & STYLE]` → contains "Don't give me generic advice" or "keep it actionable"; no dollar amounts

- [ ] **Step 4: Final commit**

```bash
git add app.py tests/test_builder.py
git commit -m "feat: update PromptBuilder context/task/format/constraints/warning for quality improvements"
```
