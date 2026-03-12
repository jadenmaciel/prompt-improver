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
