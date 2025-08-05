"""
Tests for CodeAnalyzer - Following TDD principles

This module tests the core code analysis functionality that extracts
insights from repositories for article generation.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.code_analyzer import CodeAnalyzer
from app.models.article import SourceType, CodeAnalysis


class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer following TDD methodology"""

    def test_code_analyzer_initialization_with_valid_repo_path(self):
        """
        Test: CodeAnalyzer should initialize with a valid repository path
        Expected: Should create instance without errors
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = CodeAnalyzer(temp_dir)
            assert analyzer.repo_path == Path(temp_dir)
            assert analyzer.repo is None  # No .git directory

    def test_code_analyzer_initialization_with_git_repo(self):
        """
        Test: CodeAnalyzer should detect git repository when .git exists
        Expected: Should initialize with git.Repo instance
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .git directory to simulate git repo
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()

            with patch("git.Repo") as mock_repo:
                mock_repo.return_value = MagicMock()
                analyzer = CodeAnalyzer(temp_dir)
                assert analyzer.repo is not None
                mock_repo.assert_called_once_with(temp_dir)

    @pytest.mark.asyncio
    async def test_analyze_source_with_repository_type_calls_repository_analysis(self):
        """
        Test: analyze_source with REPOSITORY type should call _analyze_repository
        Expected: Should return CodeAnalysis from repository analysis
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = CodeAnalyzer(temp_dir)

            # Mock the _analyze_repository method
            expected_analysis = CodeAnalysis(
                patterns=["test_pattern"],
                complexity_score=2.5,
                test_coverage=75.0,
                dependencies=["pytest"],
                metrics={"files": 10},
            )

            with patch.object(
                analyzer, "_analyze_repository", return_value=expected_analysis
            ):
                result = await analyzer.analyze_source(SourceType.REPOSITORY, temp_dir)

                assert result == expected_analysis
                assert result.patterns == ["test_pattern"]
                assert result.complexity_score == 2.5

    @pytest.mark.asyncio
    async def test_analyze_source_with_unsupported_type_raises_error(self):
        """
        Test: analyze_source with unsupported type should raise ValueError
        Expected: Should raise ValueError with appropriate message
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = CodeAnalyzer(temp_dir)

            # Use an invalid source type (this should fail until we handle all types)
            with pytest.raises(ValueError) as exc_info:
                await analyzer.analyze_source("INVALID_TYPE", temp_dir)

            assert "Unsupported source type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_repository_returns_code_analysis_with_basic_patterns(self):
        """
        Test: _analyze_repository should return CodeAnalysis with detected patterns
        Expected: Should detect basic patterns like microservices, containerization
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a services directory to trigger microservices pattern
            services_dir = temp_path / "services"
            services_dir.mkdir()

            # Create a Dockerfile to trigger containerization pattern
            dockerfile = temp_path / "Dockerfile"
            dockerfile.write_text("FROM python:3.12")

            analyzer = CodeAnalyzer(temp_dir)
            result = await analyzer._analyze_repository()

            assert isinstance(result, CodeAnalysis)
            assert "microservices" in result.patterns
            assert "containerization" in result.patterns
            assert result.complexity_score >= 0

    @pytest.mark.asyncio
    async def test_detect_architectural_patterns_identifies_microservices(self):
        """
        Test: _detect_architectural_patterns should identify microservices pattern
        Expected: Should return ["microservices"] when services/ directory exists
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            services_dir = temp_path / "services"
            services_dir.mkdir()

            analyzer = CodeAnalyzer(temp_dir)
            patterns = await analyzer._detect_architectural_patterns()

            assert "microservices" in patterns

    @pytest.mark.asyncio
    async def test_detect_architectural_patterns_identifies_containerization(self):
        """
        Test: _detect_architectural_patterns should identify containerization
        Expected: Should return ["containerization"] when Dockerfile exists
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dockerfile = temp_path / "Dockerfile"
            dockerfile.write_text("FROM python:3.12")

            analyzer = CodeAnalyzer(temp_dir)
            patterns = await analyzer._detect_architectural_patterns()

            assert "containerization" in patterns

    @pytest.mark.asyncio
    async def test_calculate_complexity_score_returns_numeric_value(self):
        """
        Test: _calculate_complexity_score should return a numeric complexity score
        Expected: Should return float >= 0 representing codebase complexity
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a simple Python file with some complexity
            py_file = temp_path / "test.py"
            py_file.write_text("""
def simple_function():
    if True:
        for i in range(10):
            while i > 0:
                try:
                    pass
                except:
                    pass
            """)

            analyzer = CodeAnalyzer(temp_dir)
            complexity = await analyzer._calculate_complexity_score()

            assert isinstance(complexity, float)
            assert complexity >= 0

    @pytest.mark.asyncio
    async def test_extract_dependencies_finds_requirements_txt(self):
        """
        Test: _extract_dependencies should parse requirements.txt files
        Expected: Should return list of dependencies from requirements.txt
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            req_file = temp_path / "requirements.txt"
            req_file.write_text("fastapi==0.104.1\npytest>=7.0.0\nstructlog")

            analyzer = CodeAnalyzer(temp_dir)
            dependencies = await analyzer._extract_dependencies()

            assert "fastapi" in dependencies
            assert "pytest" in dependencies
            assert "structlog" in dependencies

    @pytest.mark.asyncio
    async def test_get_test_coverage_estimates_from_test_files(self):
        """
        Test: _get_test_coverage should estimate coverage from test file ratio
        Expected: Should return coverage percentage based on test files present
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some Python files
            (temp_path / "main.py").write_text("def main(): pass")
            (temp_path / "utils.py").write_text("def helper(): pass")

            # Create test files
            (temp_path / "test_main.py").write_text("def test_main(): pass")

            analyzer = CodeAnalyzer(temp_dir)
            coverage = await analyzer._get_test_coverage()

            assert isinstance(coverage, float)
            assert 0 <= coverage <= 100
            # Should have some coverage since we have test files
            assert coverage > 0

    @pytest.mark.asyncio
    async def test_find_interesting_functions_extracts_function_metadata(self):
        """
        Test: _find_interesting_functions should extract function details
        Expected: Should return list of functions with metadata
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            py_file = temp_path / "example.py"
            py_file.write_text('''
async def complex_function(arg1, arg2):
    """This is a complex function with documentation."""
    if arg1:
        for item in arg2:
            if item > 10:
                try:
                    return item * 2
                except Exception:
                    pass
    return None

def simple_function():
    return "hello"
            ''')

            analyzer = CodeAnalyzer(temp_dir)
            functions = await analyzer._find_interesting_functions()

            assert len(functions) >= 2

            # Find the complex function
            complex_func = next(
                (f for f in functions if f["name"] == "complex_function"), None
            )
            assert complex_func is not None
            assert complex_func["is_async"] is True
            assert (
                complex_func["docstring"]
                == "This is a complex function with documentation."
            )
            assert "arg1" in complex_func["args"]
            assert "arg2" in complex_func["args"]
            assert complex_func["complexity"] > 0
