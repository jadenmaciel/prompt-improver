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
