"""
Test file for PromptTestRunner - automated testing framework for prompt templates.

This follows strict TDD practices for CRA-297 CI/CD Pipeline implementation.
The PromptTestRunner should provide automated testing capabilities for prompt templates
including validation, performance checks, and quality assurance.

Author: TDD Implementation for CRA-297
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from dataclasses import dataclass

# These imports will fail initially - this is TDD!
try:
    from services.common.prompt_test_runner import (
        PromptTestRunner,
        TestCase,
        TestResult,
        TestSuite,
        TestRunnerError,
    )
except ImportError:
    # Expected to fail on first run - this is TDD!
    pass


@dataclass
class MockTestCase:
    """Mock test case for testing purposes."""
    name: str
    input_data: Dict[str, Any]
    expected_output: str
    validation_rules: List[str]


class TestPromptTestRunnerBasics:
    """Test basic PromptTestRunner functionality."""

    @pytest.fixture
    def mock_prompt_model(self):
        """Mock PromptModel for testing."""
        mock_model = Mock()
        mock_model.name = "test-prompt-model"
        mock_model.template = "Hello {name}! Welcome to {service}."
        mock_model.render.return_value = "Hello John! Welcome to TestApp."
        return mock_model

    @pytest.fixture
    def sample_test_cases(self):
        """Sample test cases for testing."""
        return [
            TestCase(
                name="basic_greeting_test",
                input_data={"name": "John", "service": "TestApp"},
                expected_output="Hello John! Welcome to TestApp.",
                validation_rules=["contains_name", "greeting_format"]
            ),
            TestCase(
                name="empty_name_test",
                input_data={"name": "", "service": "TestApp"},
                expected_output="Hello ! Welcome to TestApp.",
                validation_rules=["handles_empty_input"]
            )
        ]

    def test_prompt_test_runner_initialization(self, mock_prompt_model):
        """Test PromptTestRunner can be initialized with a prompt model."""
        # This will fail - we haven't implemented PromptTestRunner yet
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        
        assert runner.prompt_model == mock_prompt_model
        assert runner.test_results == []
        assert runner.is_running is False

    def test_prompt_test_runner_with_test_suite(self, mock_prompt_model, sample_test_cases):
        """Test initializing runner with a test suite."""
        test_suite = TestSuite(name="basic_tests", test_cases=sample_test_cases)
        runner = PromptTestRunner(prompt_model=mock_prompt_model, test_suite=test_suite)
        
        assert runner.test_suite == test_suite
        assert len(runner.test_suite.test_cases) == 2

    def test_run_single_test_case_success(self, mock_prompt_model):
        """Test running a single test case that passes."""
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="success_test",
            input_data={"name": "John", "service": "TestApp"},
            expected_output="Hello John! Welcome to TestApp.",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        
        assert isinstance(result, TestResult)
        assert result.test_case_name == "success_test"
        assert result.passed is True
        assert result.actual_output == "Hello John! Welcome to TestApp."
        assert result.error is None

    def test_run_single_test_case_failure(self, mock_prompt_model):
        """Test running a single test case that fails."""
        # Make the mock return unexpected output
        mock_prompt_model.render.return_value = "Unexpected output"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="failure_test",
            input_data={"name": "John", "service": "TestApp"},
            expected_output="Hello John! Welcome to TestApp.",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        
        assert isinstance(result, TestResult)
        assert result.test_case_name == "failure_test"
        assert result.passed is False
        assert result.actual_output == "Unexpected output"
        assert result.error is not None

    def test_run_test_suite_returns_all_results(self, mock_prompt_model, sample_test_cases):
        """Test running a complete test suite returns all results."""
        test_suite = TestSuite(name="comprehensive_tests", test_cases=sample_test_cases)
        runner = PromptTestRunner(prompt_model=mock_prompt_model, test_suite=test_suite)
        
        results = runner.run_test_suite()
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(result, TestResult) for result in results)
        assert results[0].test_case_name == "basic_greeting_test"
        assert results[1].test_case_name == "empty_name_test"


class TestPromptTestRunnerValidation:
    """Test validation capabilities of PromptTestRunner."""

    @pytest.fixture
    def mock_prompt_model(self):
        mock_model = Mock()
        mock_model.name = "validation-test-model"
        mock_model.template = "Product: {product}, Price: ${price:.2f}"
        return mock_model

    def test_exact_match_validation_passes(self, mock_prompt_model):
        """Test exact match validation rule passes when outputs match."""
        mock_prompt_model.render.return_value = "Product: Laptop, Price: $999.99"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="exact_match_test",
            input_data={"product": "Laptop", "price": 999.99},
            expected_output="Product: Laptop, Price: $999.99",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_contains_validation_passes(self, mock_prompt_model):
        """Test contains validation rule passes when expected content is present."""
        mock_prompt_model.render.return_value = "Product: Laptop, Price: $999.99, In Stock"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="contains_test",
            input_data={"product": "Laptop", "price": 999.99},
            expected_output="Laptop",  # Just check if it contains "Laptop"
            validation_rules=["contains"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_regex_validation_passes(self, mock_prompt_model):
        """Test regex validation rule passes when pattern matches."""
        mock_prompt_model.render.return_value = "Product: Laptop, Price: $999.99"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="regex_test",
            input_data={"product": "Laptop", "price": 999.99},
            expected_output=r"Price: \$\d+\.\d{2}",  # Regex pattern for price
            validation_rules=["regex_match"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_length_validation_passes(self, mock_prompt_model):
        """Test length validation rule passes when output length is within bounds."""
        mock_prompt_model.render.return_value = "Product: Laptop, Price: $999.99"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="length_test",
            input_data={"product": "Laptop", "price": 999.99},
            expected_output="30,50",  # Min 30, Max 50 characters
            validation_rules=["length_range"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_multiple_validation_rules_all_pass(self, mock_prompt_model):
        """Test multiple validation rules where all pass."""
        mock_prompt_model.render.return_value = "Product: Laptop, Price: $999.99"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="multi_validation_test",
            input_data={"product": "Laptop", "price": 999.99},
            expected_output="Laptop",
            validation_rules=["contains", "length_range:10,50", "regex_match:Product.*Price"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_validation_failure_with_detailed_error(self, mock_prompt_model):
        """Test validation failure provides detailed error information."""
        mock_prompt_model.render.return_value = "Wrong output format"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="validation_failure_test",
            input_data={"product": "Laptop", "price": 999.99},
            expected_output="Product: Laptop, Price: $999.99",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is False
        assert "exact_match" in result.error
        assert "Expected" in result.error
        assert "Actual" in result.error


class TestPromptTestRunnerPerformance:
    """Test performance measurement capabilities."""

    @pytest.fixture
    def mock_prompt_model(self):
        mock_model = Mock()
        mock_model.render.return_value = "Test output"
        return mock_model

    def test_execution_time_measurement(self, mock_prompt_model):
        """Test that execution time is measured and recorded."""
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="performance_test",
            input_data={"input": "test"},
            expected_output="Test output",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        
        assert result.execution_time is not None
        assert result.execution_time > 0
        assert isinstance(result.execution_time, float)

    def test_performance_threshold_validation(self, mock_prompt_model):
        """Test performance threshold validation."""
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="performance_threshold_test",
            input_data={"input": "test"},
            expected_output="Test output",
            validation_rules=["exact_match", "max_execution_time:1.0"]  # 1 second max
        )
        
        result = runner.run_test_case(test_case)
        
        # Should pass if execution is under 1 second
        assert result.passed is True

    @patch('time.time')
    def test_slow_execution_fails_performance_check(self, mock_time, mock_prompt_model):
        """Test that slow execution fails performance validation."""
        # Mock time to simulate slow execution
        mock_time.side_effect = [0.0, 2.0]  # 2 second execution time
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="slow_execution_test",
            input_data={"input": "test"},
            expected_output="Test output",
            validation_rules=["exact_match", "max_execution_time:1.0"]  # 1 second max
        )
        
        result = runner.run_test_case(test_case)
        
        assert result.passed is False
        assert "execution_time" in result.error


class TestPromptTestRunnerErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def mock_prompt_model(self):
        mock_model = Mock()
        mock_model.name = "error-test-model"
        return mock_model

    def test_prompt_model_render_exception_handled(self, mock_prompt_model):
        """Test that exceptions during prompt rendering are handled gracefully."""
        mock_prompt_model.render.side_effect = Exception("Rendering failed")
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="exception_test",
            input_data={"input": "test"},
            expected_output="Test output",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        
        assert result.passed is False
        assert "Rendering failed" in result.error
        assert result.actual_output is None

    def test_invalid_validation_rule_raises_error(self, mock_prompt_model):
        """Test that invalid validation rules raise appropriate errors."""
        mock_prompt_model.render.return_value = "Test output"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="invalid_rule_test",
            input_data={"input": "test"},
            expected_output="Test output",
            validation_rules=["invalid_rule"]
        )
        
        with pytest.raises(TestRunnerError, match="Unknown validation rule"):
            runner.run_test_case(test_case)

    def test_empty_test_suite_returns_empty_results(self, mock_prompt_model):
        """Test that empty test suite returns empty results."""
        test_suite = TestSuite(name="empty_suite", test_cases=[])
        runner = PromptTestRunner(prompt_model=mock_prompt_model, test_suite=test_suite)
        
        results = runner.run_test_suite()
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_none_prompt_model_raises_error(self):
        """Test that None prompt model raises appropriate error."""
        with pytest.raises(TestRunnerError, match="Prompt model cannot be None"):
            PromptTestRunner(prompt_model=None)


class TestPromptTestRunnerReporting:
    """Test reporting and summary capabilities."""

    @pytest.fixture
    def mock_prompt_model(self):
        mock_model = Mock()
        mock_model.name = "reporting-test-model"
        mock_model.render.return_value = "Test output"
        return mock_model

    @pytest.fixture
    def mixed_results_test_suite(self):
        """Test suite with mixed pass/fail results."""
        return TestSuite(
            name="mixed_results_suite",
            test_cases=[
                TestCase(
                    name="passing_test",
                    input_data={"input": "test"},
                    expected_output="Test output",
                    validation_rules=["exact_match"]
                ),
                TestCase(
                    name="failing_test",
                    input_data={"input": "test"},
                    expected_output="Different output",
                    validation_rules=["exact_match"]
                )
            ]
        )

    def test_generate_test_summary_report(self, mock_prompt_model, mixed_results_test_suite):
        """Test generating summary report from test results."""
        runner = PromptTestRunner(prompt_model=mock_prompt_model, test_suite=mixed_results_test_suite)
        results = runner.run_test_suite()
        
        summary = runner.generate_summary_report(results)
        
        assert isinstance(summary, dict)
        assert summary["total_tests"] == 2
        assert summary["passed_tests"] == 1
        assert summary["failed_tests"] == 1
        assert summary["success_rate"] == 0.5
        assert "execution_time_stats" in summary
        assert summary["test_suite_name"] == "mixed_results_suite"

    def test_generate_detailed_report(self, mock_prompt_model, mixed_results_test_suite):
        """Test generating detailed report with all test results."""
        runner = PromptTestRunner(prompt_model=mock_prompt_model, test_suite=mixed_results_test_suite)
        results = runner.run_test_suite()
        
        detailed_report = runner.generate_detailed_report(results)
        
        assert isinstance(detailed_report, dict)
        assert "summary" in detailed_report
        assert "test_results" in detailed_report
        assert len(detailed_report["test_results"]) == 2
        assert "prompt_model_info" in detailed_report
        assert detailed_report["prompt_model_info"]["name"] == "reporting-test-model"

    def test_export_results_to_json(self, mock_prompt_model, mixed_results_test_suite):
        """Test exporting test results to JSON format."""
        runner = PromptTestRunner(prompt_model=mock_prompt_model, test_suite=mixed_results_test_suite)
        results = runner.run_test_suite()
        
        json_report = runner.export_results_to_json(results)
        
        assert isinstance(json_report, str)
        
        # Parse JSON to verify structure
        import json
        parsed_report = json.loads(json_report)
        assert "summary" in parsed_report
        assert "test_results" in parsed_report
        assert parsed_report["summary"]["total_tests"] == 2


class TestPromptTestRunnerIntegration:
    """Integration tests with real PromptModel instances."""

    @pytest.fixture
    def real_prompt_model(self):
        """Create a real PromptModel for integration testing."""
        with patch('services.common.prompt_model_registry.get_mlflow_client'):
            from services.common.prompt_model_registry import PromptModel, ModelStage
            
            model = PromptModel(
                name="integration-test-model",
                template="Welcome {user} to {platform}! Your role is {role}.",
                version="1.0.0",
                stage=ModelStage.DEV,
                metadata={"purpose": "integration_testing"}
            )
            return model

    def test_integration_with_real_prompt_model(self, real_prompt_model):
        """Test PromptTestRunner with real PromptModel integration."""
        test_cases = [
            TestCase(
                name="admin_welcome_test",
                input_data={"user": "Admin", "platform": "TestPlatform", "role": "administrator"},
                expected_output="Welcome Admin to TestPlatform! Your role is administrator.",
                validation_rules=["exact_match"]
            ),
            TestCase(
                name="user_welcome_test",
                input_data={"user": "John", "platform": "TestPlatform", "role": "user"},
                expected_output="Welcome John to TestPlatform! Your role is user.",
                validation_rules=["exact_match"]
            )
        ]
        
        test_suite = TestSuite(name="integration_tests", test_cases=test_cases)
        runner = PromptTestRunner(prompt_model=real_prompt_model, test_suite=test_suite)
        
        results = runner.run_test_suite()
        
        assert len(results) == 2
        assert all(result.passed for result in results)  # All should pass with exact matches
        
        summary = runner.generate_summary_report(results)
        assert summary["success_rate"] == 1.0


class TestTestCaseDataclass:
    """Test TestCase dataclass functionality."""

    def test_test_case_creation_with_all_fields(self):
        """Test TestCase can be created with all required fields."""
        test_case = TestCase(
            name="test_case_1",
            input_data={"var1": "value1", "var2": 123},
            expected_output="Expected result",
            validation_rules=["exact_match", "contains"]
        )
        
        assert test_case.name == "test_case_1"
        assert test_case.input_data == {"var1": "value1", "var2": 123}
        assert test_case.expected_output == "Expected result"
        assert test_case.validation_rules == ["exact_match", "contains"]

    def test_test_case_with_optional_metadata(self):
        """Test TestCase with additional metadata."""
        test_case = TestCase(
            name="metadata_test",
            input_data={"input": "test"},
            expected_output="output",
            validation_rules=["exact_match"],
            metadata={"author": "test_user", "priority": "high"}
        )
        
        assert hasattr(test_case, 'metadata')
        assert test_case.metadata["author"] == "test_user"


class TestTestResultDataclass:
    """Test TestResult dataclass functionality."""

    def test_test_result_creation_success(self):
        """Test TestResult creation for successful test."""
        result = TestResult(
            test_case_name="success_test",
            passed=True,
            actual_output="Expected output",
            expected_output="Expected output",
            execution_time=0.025,
            error=None
        )
        
        assert result.test_case_name == "success_test"
        assert result.passed is True
        assert result.actual_output == "Expected output"
        assert result.execution_time == 0.025
        assert result.error is None

    def test_test_result_creation_failure(self):
        """Test TestResult creation for failed test."""
        result = TestResult(
            test_case_name="failure_test",
            passed=False,
            actual_output="Unexpected output",
            expected_output="Expected output",
            execution_time=0.030,
            error="Output mismatch: expected 'Expected output', got 'Unexpected output'"
        )
        
        assert result.passed is False
        assert result.error is not None
        assert "Output mismatch" in result.error


class TestTestSuiteDataclass:
    """Test TestSuite dataclass functionality."""

    def test_test_suite_creation(self):
        """Test TestSuite creation with test cases."""
        test_cases = [
            TestCase("test1", {"input": "1"}, "output1", ["exact_match"]),
            TestCase("test2", {"input": "2"}, "output2", ["exact_match"])
        ]
        
        suite = TestSuite(name="test_suite", test_cases=test_cases)
        
        assert suite.name == "test_suite"
        assert len(suite.test_cases) == 2
        assert suite.test_cases[0].name == "test1"

    def test_test_suite_with_metadata(self):
        """Test TestSuite with additional metadata."""
        suite = TestSuite(
            name="metadata_suite",
            test_cases=[],
            metadata={"version": "1.0", "description": "Test suite for validation"}
        )
        
        assert hasattr(suite, 'metadata')
        assert suite.metadata["version"] == "1.0"


# Performance and edge case tests
class TestPromptTestRunnerEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def mock_prompt_model(self):
        mock_model = Mock()
        mock_model.name = "edge-case-model"
        mock_model.render.return_value = "Standard output"
        return mock_model

    def test_very_large_input_data_handling(self, mock_prompt_model):
        """Test handling of very large input data."""
        large_input = {"data": "x" * 100000}  # 100KB of data
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="large_input_test",
            input_data=large_input,
            expected_output="Standard output",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_unicode_and_special_characters(self, mock_prompt_model):
        """Test handling of unicode and special characters."""
        mock_prompt_model.render.return_value = "Hello 世界! 🚀 Special chars: αβγ"
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="unicode_test",
            input_data={"text": "世界", "emoji": "🚀"},
            expected_output="Hello 世界! 🚀 Special chars: αβγ",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_empty_expected_output_validation(self, mock_prompt_model):
        """Test validation when expected output is empty."""
        mock_prompt_model.render.return_value = ""
        
        runner = PromptTestRunner(prompt_model=mock_prompt_model)
        test_case = TestCase(
            name="empty_output_test",
            input_data={"input": "test"},
            expected_output="",
            validation_rules=["exact_match"]
        )
        
        result = runner.run_test_case(test_case)
        assert result.passed is True

    def test_concurrent_test_execution(self, mock_prompt_model):
        """Test running tests concurrently doesn't cause issues."""
        import threading
        
        results = []
        errors = []
        
        def run_test(test_id):
            try:
                runner = PromptTestRunner(prompt_model=mock_prompt_model)
                test_case = TestCase(
                    name=f"concurrent_test_{test_id}",
                    input_data={"id": test_id},
                    expected_output="Standard output",
                    validation_rules=["exact_match"]
                )
                result = runner.run_test_case(test_case)
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=run_test, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result.passed for result in results)


# Mark some tests as e2e if they require integration
@pytest.mark.e2e
class TestPromptTestRunnerE2EIntegration:
    """End-to-end integration tests requiring full environment."""
    
    def test_full_ci_cd_pipeline_integration(self):
        """Test PromptTestRunner as part of full CI/CD pipeline."""
        # This test would require actual MLflow server and full integration
        # For now, we'll skip it unless in e2e environment
        pytest.skip("Requires full e2e environment - implement when other components ready")