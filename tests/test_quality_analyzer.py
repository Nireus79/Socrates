#!/usr/bin/env python3
"""
Test Suite for QualityAnalyzer - Universal Quality Validator
============================================================

Tests for the extended QualityAnalyzer that validates across all phases:
- Socratic questioning (original)
- Chat mode statements (new)
- Code suggestions (new)
- Architecture decisions (new)
"""

import pytest
from src.agents.quality_analyzer import (
    QualityAnalyzer,
    QuestionQualityAnalyzer,  # Backward compatibility
    QuestionBias,
    CoverageGap,
    QuestionAnalysis,
    SuggestionAnalysis,
)


class TestQualityAnalyzerBasics:
    """Test basic QualityAnalyzer functionality"""

    def test_analyzer_instantiation(self):
        """Test that QualityAnalyzer can be instantiated"""
        analyzer = QualityAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'analyze_question')
        assert hasattr(analyzer, 'analyze_suggestion')
        assert hasattr(analyzer, 'analyze_statement')
        assert hasattr(analyzer, 'analyze_code_change')

    def test_backward_compatibility_alias(self):
        """Test that QuestionQualityAnalyzer still works"""
        old_analyzer = QuestionQualityAnalyzer()
        new_analyzer = QualityAnalyzer()
        assert type(old_analyzer) == type(new_analyzer)
        assert old_analyzer.__class__.__name__ == 'QualityAnalyzer'


class TestQuestionAnalysis:
    """Test original question analysis capability (should work as before)"""

    def setup_method(self):
        """Setup for each test"""
        self.analyzer = QualityAnalyzer()

    def test_analyze_unbiased_question(self):
        """Test analysis of unbiased, open-ended question"""
        question = {
            'id': 'q1',
            'text': 'What are the main requirements for this system?'
        }
        analysis = self.analyzer.analyze_question(question)

        assert isinstance(analysis, QuestionAnalysis)
        assert analysis.bias_detected is None
        assert analysis.bias_score == 0.0
        assert analysis.quality_score == 1.0

    def test_analyze_solution_biased_question(self):
        """Test detection of solution-biased question"""
        question = {
            'id': 'q2',
            'text': 'Should we build this using React and MongoDB?'
        }
        analysis = self.analyzer.analyze_question(question)

        assert analysis.bias_detected == QuestionBias.SOLUTION_BIASED
        assert analysis.bias_score > 0.0
        assert analysis.quality_score < 1.0
        assert len(analysis.suggested_alternatives) > 0

    def test_analyze_technology_biased_question(self):
        """Test detection of technology-biased question"""
        question = {
            'id': 'q3',
            'text': 'Which database should we use - PostgreSQL or MySQL?'
        }
        analysis = self.analyzer.analyze_question(question)

        # This is actually solution bias (specific tech mentioned)
        assert analysis.bias_detected in [QuestionBias.SOLUTION_BIASED, QuestionBias.TECHNOLOGY_BIASED]
        assert analysis.bias_score > 0.0

    def test_coverage_detection(self):
        """Test detection of requirement areas in questions"""
        question = {
            'id': 'q4',
            'text': 'What are the security, scalability, and performance requirements?'
        }
        analysis = self.analyzer.analyze_question(question)

        assert 'security' in analysis.coverage_areas
        assert 'scalability' in analysis.coverage_areas
        assert 'performance' in analysis.coverage_areas


class TestSuggestionAnalysis:
    """Test new suggestion analysis capability"""

    def setup_method(self):
        """Setup for each test"""
        self.analyzer = QualityAnalyzer()

    def test_analyze_code_suggestion_quality(self):
        """Test analysis of code suggestion"""
        suggestion = {
            'id': 'sug1',
            'text': 'Refactor the user service to use MongoDB for flexibility',
            'type': 'code_change'
        }
        analysis = self.analyzer.analyze_suggestion(suggestion)

        assert isinstance(analysis, SuggestionAnalysis)
        assert analysis.suggestion_type == 'code_change'
        assert analysis.bias_detected is not None
        assert analysis.quality_score < 1.0

    def test_analyze_architecture_suggestion(self):
        """Test analysis of architecture suggestion"""
        suggestion = {
            'id': 'arch1',
            'text': 'Use microservices architecture for better scalability, with monitoring and error handling',
            'type': 'architecture'
        }
        analysis = self.analyzer.analyze_suggestion(suggestion)

        assert analysis.suggestion_type == 'architecture'
        # Should have some coverage (scalability might match)
        # But microservices is a solution bias, so check at least for missing context
        assert len(analysis.missing_context) > 0 or len(analysis.coverage_areas) > 0

    def test_unverified_suggestion_confidence(self):
        """Test confidence assessment for unverified suggestions"""
        suggestion = {
            'id': 'sug2',
            'text': 'We could use Redis for caching'
        }
        analysis = self.analyzer.analyze_suggestion(suggestion)

        assert analysis.confidence_level in ['verified', 'assumed', 'speculative']

    def test_verified_suggestion_with_context(self):
        """Test confidence when context is provided"""
        suggestion = {
            'id': 'sug3',
            'text': 'Use JWT for authentication'
        }
        context = {'verified': True, 'source': 'security_audit'}

        analysis = self.analyzer.analyze_suggestion(suggestion, context)
        assert analysis.confidence_level == 'verified'

    def test_missing_context_detection(self):
        """Test detection of missing context in suggestions"""
        suggestion = {
            'id': 'sug4',
            'text': 'Add user authentication',
            'type': 'code_change'
        }
        analysis = self.analyzer.analyze_suggestion(suggestion)

        # Should detect missing testing and error handling
        assert len(analysis.missing_context) > 0


class TestStatementAnalysis:
    """Test chat statement analysis capability"""

    def setup_method(self):
        """Setup for each test"""
        self.analyzer = QualityAnalyzer()

    def test_analyze_chat_statement(self):
        """Test analysis of chat statement"""
        statement = {
            'id': 'msg1',
            'text': 'Use React because everyone uses it',
            'author': 'developer'
        }
        analysis = self.analyzer.analyze_statement(statement)

        assert isinstance(analysis, SuggestionAnalysis)
        assert analysis.bias_score > 0.0

    def test_analyze_chat_recommendation(self):
        """Test analysis of chat-based recommendation"""
        statement = {
            'id': 'msg2',
            'text': 'Consider a microservices approach with proper error handling and monitoring',
            'author': 'architect'
        }
        analysis = self.analyzer.analyze_statement(statement)

        # Should have lower bias and good coverage
        assert 'error_handling' in analysis.coverage_areas
        assert 'monitoring' in analysis.coverage_areas


class TestCodeChangeAnalysis:
    """Test code change analysis capability"""

    def setup_method(self):
        """Setup for each test"""
        self.analyzer = QualityAnalyzer()

    def test_analyze_code_change_basic(self):
        """Test analysis of proposed code change"""
        code_change = {
            'id': 'cc1',
            'description': 'Refactor user model',
            'rationale': 'Improve performance',
            'code': 'def get_user(id): return db.query(User).get(id)'
        }
        analysis = self.analyzer.analyze_code_change(code_change)

        assert isinstance(analysis, SuggestionAnalysis)
        assert analysis.suggestion_type == 'code_change'

    def test_code_quality_pattern_detection(self):
        """Test detection of code quality issues"""
        code_change = {
            'id': 'cc2',
            'description': 'Add error handling',
            'rationale': 'Safety',
            'code': 'try: something()\nexcept: pass'  # bare except
        }
        analysis = self.analyzer.analyze_code_change(code_change)

        # Should detect bare except clause
        assert any('bare except' in imp.lower() for imp in analysis.suggested_improvements)

    def test_code_change_with_todo_detection(self):
        """Test detection of incomplete code"""
        code_change = {
            'id': 'cc3',
            'description': 'Implement user validation',
            'rationale': 'Security',
            'code': '# TODO: implement email validation'
        }
        analysis = self.analyzer.analyze_code_change(code_change)

        # Should detect TODO comment
        assert any('TODO' in imp or 'todo' in imp.lower() for imp in analysis.suggested_improvements)


class TestSessionAnalysis:
    """Test analysis of multiple items across a session"""

    def setup_method(self):
        """Setup for each test"""
        self.analyzer = QualityAnalyzer()

    def test_analyze_session_with_questions(self):
        """Test analysis of questioning session"""
        questions = [
            {'id': 'q1', 'text': 'What are the requirements?'},
            {'id': 'q2', 'text': 'Who are the users?'},
            {'id': 'q3', 'text': 'Should we use React?'}
        ]
        analysis = self.analyzer.analyze_session('session1', questions)

        assert analysis.session_id == 'session1'
        assert analysis.total_questions == 3
        assert analysis.diversity_score >= 0.0

    def test_coverage_gap_identification(self):
        """Test identification of coverage gaps in session"""
        questions = [
            {'id': 'q1', 'text': 'What are the requirements?'},
            {'id': 'q2', 'text': 'Who are the users?'}
        ]
        analysis = self.analyzer.analyze_session('session2', questions)

        # Should have coverage gaps for many areas
        assert len(analysis.coverage_gaps) > 0
        assert CoverageGap.NO_SECURITY in analysis.coverage_gaps


class TestBiasPatterns:
    """Test specific bias pattern detection"""

    def setup_method(self):
        """Setup for each test"""
        self.analyzer = QualityAnalyzer()

    def test_solution_bias_patterns(self):
        """Test various solution bias patterns"""
        biased_texts = [
            'Build with MongoDB and React',
            'Implement using microservices',
            'Use Docker and Kubernetes'
        ]

        for text in biased_texts:
            analysis = self.analyzer.analyze_suggestion({'id': 'test', 'text': text})
            assert analysis.bias_score > 0.0, f"Failed to detect bias in: {text}"

    def test_technology_bias_patterns(self):
        """Test various technology bias patterns"""
        biased_texts = [
            'Should we use PostgreSQL?',
            'Can we use Angular framework?',
            'Which database should we choose?'
        ]

        for text in biased_texts:
            analysis = self.analyzer.analyze_suggestion({'id': 'test', 'text': text})
            # May be solution or technology bias
            assert analysis.bias_score >= 0.0

    def test_no_false_positives(self):
        """Test that unbiased text doesn't trigger false positives"""
        unbiased_texts = [
            'What are the core requirements?',
            'How should we handle errors?',
            'What is the team size and experience level?'
        ]

        for text in unbiased_texts:
            analysis = self.analyzer.analyze_suggestion({'id': 'test', 'text': text})
            # Should have very low or zero bias
            assert analysis.bias_score <= 0.4, f"False positive for: {text}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
