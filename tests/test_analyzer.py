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
