"""Golden fixture tests — exact output snapshots for regression detection.

These tests store the full improved-prompt output verbatim. If a refactor
changes behavior in any way (wording, ordering, section content), these tests
will fail and force a conscious decision about whether the change is intentional.

To update a fixture after an intentional change:
    1. Run the app or script to regenerate the output.
    2. Replace the GOLDEN_N_OUTPUT string below.
    3. Commit the update with a clear message explaining why the output changed.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import PromptAnalyzer, PromptBuilder

analyzer = PromptAnalyzer()
builder = PromptBuilder()


def _build(raw: str) -> str:
    analysis = analyzer.analyze(raw)
    return builder.build(raw, analysis, {})


# ---------------------------------------------------------------------------
# Golden 1: Multi-task finance — vending machine side hustle + AMEX card
# ---------------------------------------------------------------------------

GOLDEN_1_PROMPT = (
    "I need help with two things. First, please review my vending machine side hustle and help me plan the next steps. "
    "Also, analyze my AMEX card \u2014 I have a $10,000 credit limit and a 15,000 point signup bonus after spending $6,000 in 3 months. "
    "Don't give me generic advice, keep it actionable."
)

GOLDEN_1_OUTPUT = (
    "[ROLE / PERSONA]\n"
    "You are an experienced small-business and personal-finance coach who helps people plan side hustles, manage budgets, and optimize credit-card and rewards strategies.\n"
    "\n"
    "[CONTEXT]\n"
    "I need help with two things. Also, analyze my AMEX card \u2014 I have a $10,000 credit limit and a 15,000 point signup bonus after spending $6,000 in 3 months. First, please review my vending machine side hustle and help me plan the next steps. Don't give me generic advice, keep it actionable.\n"
    "Assume a technical developer audience familiar with the relevant concepts.\n"
    "\n"
    "[TASK]\n"
    "1. I need help with two things.\n"
    "2. First, please review my vending machine side hustle and help me plan the next steps.\n"
    "3. Also, analyze my AMEX card \u2014 I have a $10,000 credit limit and a 15,000 point signup bonus after spending $6,000 in 3 months.\n"
    "\n"
    "[INPUT]\n"
    "The user will provide: the content, code, or system to be analyzed.\n"
    "\n"
    "[OUTPUT FORMAT]\n"
    "Return a markdown document with:\n"
    "- Section 1: Summary of the current situation\n"
    "- Section 2: Action plan (prioritized steps, grouped by timeframe if applicable)\n"
    "- Section 3: Financial review (card details, budget, key numbers)\n"
    "- Section 4: Integrated recommendations and risks\n"
    "\n"
    "[CONSTRAINTS & STYLE]\n"
    "- From original prompt: Don't give me generic advice, keep it actionable.\n"
    "\n"
    "---\n"
    "Paste the prompt above into your AI tool of choice.\n"
    "Adjust any bracketed sections as needed."
)


# ---------------------------------------------------------------------------
# Golden 2: Single-task technical build — Python CLI tic-tac-toe
# ---------------------------------------------------------------------------

GOLDEN_2_PROMPT = (
    "Build a command-line tic-tac-toe game in Python with an unbeatable AI opponent."
)

GOLDEN_2_OUTPUT = (
    "[ROLE / PERSONA]\n"
    "You are an expert frontend developer specializing in modern UI frameworks and user experience, with hands-on experience in Python.\n"
    "\n"
    "[CONTEXT]\n"
    "Build a command-line tic-tac-toe game in Python with an unbeatable AI opponent.\n"
    "This is a frontend development task involving UI components, browser rendering, or user experience.\n"
    "Key technologies involved: Python.\n"
    "Assume a technical developer audience familiar with the relevant concepts.\n"
    "\n"
    "[TASK]\n"
    "Design and implement a command-line tic-tac-toe game in Python with an unbeatable AI opponent. using Python.\n"
    "Cover: (1) overall architecture and how components fit together, (2) step-by-step implementation with concrete code examples, (3) any configuration, auth, or security considerations.\n"
    "\n"
    "[OUTPUT FORMAT]\n"
    "- Section 1: High-level architecture (1\u20132 paragraphs)\n"
    "- Section 2: Key components or tools in a markdown table (columns: Name | Purpose | Notes)\n"
    "- Section 3: Step-by-step implementation with code snippets\n"
    "- Section 4: Security, edge cases, and gotchas as bullet points\n"
    "\n"
    "[CONSTRAINTS & STYLE]\n"
    "- Show working code, not pseudocode. If choices depend on the user's stack, offer 2 concrete options.\n"
    "\n"
    "---\n"
    "Paste the prompt above into your AI tool of choice.\n"
    "Adjust any bracketed sections as needed."
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGoldenFixtures:
    def test_golden_1_multitask_finance(self):
        """Vending machine + AMEX multi-task prompt produces exact expected output."""
        assert _build(GOLDEN_1_PROMPT) == GOLDEN_1_OUTPUT

    def test_golden_2_single_task_build(self):
        """Single-task Python CLI build prompt produces exact expected output."""
        assert _build(GOLDEN_2_PROMPT) == GOLDEN_2_OUTPUT
