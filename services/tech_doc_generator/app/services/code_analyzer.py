import ast
import os
import subprocess
from typing import Dict, List, Any
from pathlib import Path
import git
from collections import defaultdict
import structlog

from ..models.article import CodeAnalysis, SourceType
from ..core.cache import get_cache_manager

logger = structlog.get_logger()


class CodeAnalyzer:
    """Analyzes codebase to extract insights for article generation"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = (
            git.Repo(repo_path)
            if os.path.exists(os.path.join(repo_path, ".git"))
            else None
        )
        self.cache = get_cache_manager()

    async def analyze_source(
        self, source_type: SourceType, source_path: str
    ) -> CodeAnalysis:
        """Main entry point for code analysis"""
        logger.info(
            "Starting code analysis", source_type=source_type, source_path=source_path
        )

        if source_type == SourceType.REPOSITORY:
            return await self._analyze_repository()
        elif source_type == SourceType.DIRECTORY:
            return await self._analyze_directory(source_path)
        elif source_type == SourceType.FILE:
            return await self._analyze_file(source_path)
        elif source_type == SourceType.COMMIT:
            return await self._analyze_commit(source_path)
        elif source_type == SourceType.PR:
            return await self._analyze_pr(source_path)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def _analyze_repository(self) -> CodeAnalysis:
        """Analyze entire repository with caching"""
        # Check if we have cached full analysis
        cache_key_data = {
            "repo_path": str(self.repo_path),
            "git_head": self._get_git_head_hash(),
        }

        cached_analysis = await self.cache.get_cached_result(
            "code_analysis", **cache_key_data
        )
        if cached_analysis:
            logger.info("Using cached repository analysis")
            return CodeAnalysis(**cached_analysis)

        # Perform analysis
        patterns = await self._detect_architectural_patterns()
        complexity = await self._calculate_complexity_score()
        coverage = await self._get_test_coverage()
        dependencies = await self._extract_dependencies()
        metrics = await self._extract_metrics()
        interesting_functions = await self._find_interesting_functions()
        recent_changes = await self._get_recent_changes()

        analysis = CodeAnalysis(
            patterns=patterns,
            complexity_score=complexity,
            test_coverage=coverage,
            dependencies=dependencies,
            metrics=metrics,
            interesting_functions=interesting_functions,
            recent_changes=recent_changes,
        )

        # Cache the result
        await self.cache.cache_result(
            "code_analysis", analysis.dict(), **cache_key_data
        )

        return analysis

    def _get_git_head_hash(self) -> str:
        """Get current git HEAD hash for cache invalidation"""
        if self.repo:
            try:
                return self.repo.head.commit.hexsha[:12]
            except Exception:
                pass
        return "no_git"

    async def _analyze_directory(self, directory: str) -> CodeAnalysis:
        """Analyze specific directory"""
        dir_path = self.repo_path / directory
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        patterns = await self._detect_patterns_in_directory(dir_path)
        complexity = await self._calculate_directory_complexity(dir_path)
        dependencies = await self._extract_directory_dependencies(dir_path)
        interesting_functions = await self._find_functions_in_directory(dir_path)

        return CodeAnalysis(
            patterns=patterns,
            complexity_score=complexity,
            dependencies=dependencies,
            interesting_functions=interesting_functions,
        )

    async def _analyze_file(self, file_path: str) -> CodeAnalysis:
        """Analyze specific file"""
        full_path = self.repo_path / file_path
        if not full_path.exists():
            raise ValueError(f"File not found: {file_path}")

        patterns = await self._detect_patterns_in_file(full_path)
        complexity = await self._calculate_file_complexity(full_path)
        functions = await self._extract_functions_from_file(full_path)

        return CodeAnalysis(
            patterns=patterns,
            complexity_score=complexity,
            interesting_functions=functions,
        )

    async def _analyze_commit(self, commit_hash: str) -> CodeAnalysis:
        """Analyze specific commit"""
        if not self.repo:
            raise ValueError("Git repository not available")

        try:
            commit = self.repo.commit(commit_hash)
            changes = await self._analyze_commit_changes(commit)
            patterns = await self._detect_patterns_in_commit(commit)

            return CodeAnalysis(
                patterns=patterns,
                recent_changes=changes,
                metrics={"commit_hash": commit_hash, "message": commit.message},
            )
        except Exception as e:
            raise ValueError(f"Error analyzing commit {commit_hash}: {e}")

    async def _analyze_pr(self, pr_identifier: str) -> CodeAnalysis:
        """Analyze PR changes (placeholder - would integrate with GitHub API)"""
        # This would integrate with GitHub API to analyze PR changes
        return CodeAnalysis(patterns=["pr_analysis"], metrics={"pr_id": pr_identifier})

    async def _detect_architectural_patterns(self) -> List[str]:
        """Detect architectural patterns in the codebase with memory-efficient streaming"""
        patterns = []

        # Check for microservices pattern
        if (self.repo_path / "services").exists():
            patterns.append("microservices")

        # Check for containerization
        if (self.repo_path / "Dockerfile").exists() or (
            self.repo_path / "docker-compose.yml"
        ).exists():
            patterns.append("containerization")

        # Check for Kubernetes
        if (self.repo_path / "k8s").exists() or (self.repo_path / "charts").exists():
            patterns.append("kubernetes")

        # Memory-efficient pattern detection with streaming
        async for pattern in self._detect_patterns_streaming():
            if pattern not in patterns:
                patterns.append(pattern)

        return patterns

    async def _detect_patterns_streaming(self):
        """Stream pattern detection to avoid memory spikes"""
        MAX_FILE_SIZE = 1024 * 1024  # 1MB limit per file
        files_checked = 0
        MAX_FILES_TO_CHECK = 50  # Limit to prevent excessive scanning

        # Use generator to process files one by one
        python_files_gen = self.repo_path.rglob("*.py")

        for file_path in python_files_gen:
            if files_checked >= MAX_FILES_TO_CHECK:
                break

            try:
                # Check file size before reading
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    # Read in chunks to avoid memory spikes
                    content_chunk = f.read(8192)  # Read first 8KB only

                    if "FastAPI" in content_chunk or "@app.route" in content_chunk:
                        yield "rest_api"
                    if "async def" in content_chunk or "await " in content_chunk:
                        yield "async_programming"
                    if "prometheus" in content_chunk.lower():
                        yield "observability"

                files_checked += 1
            except (OSError, UnicodeDecodeError):
                continue

    async def _calculate_complexity_score(self) -> float:
        """Calculate overall complexity score with memory optimization"""
        try:
            # Use radon for complexity analysis if available (with timeout)
            result = subprocess.run(
                ["radon", "cc", str(self.repo_path), "-a"],
                capture_output=True,
                text=True,
                timeout=15,  # Reduced timeout
            )
            if result.returncode == 0:
                # Parse radon output to get average complexity
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Average complexity:" in line:
                        return float(line.split(":")[-1].strip().split()[0])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: memory-efficient streaming complexity calculation
        return await self._calculate_complexity_streaming()

    async def _calculate_complexity_streaming(self) -> float:
        """Calculate complexity using streaming to avoid memory spikes"""
        MAX_FILE_SIZE = 512 * 1024  # 512KB limit per file
        MAX_FILES_TO_ANALYZE = 30  # Reduced from 20 to balance speed vs accuracy

        total_complexity = 0
        file_count = 0

        # Use generator to process files one by one
        python_files_gen = self.repo_path.rglob("*.py")

        for file_path in python_files_gen:
            if file_count >= MAX_FILES_TO_ANALYZE:
                break

            try:
                # Skip large files to prevent memory issues
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue

                complexity = await self._calculate_file_complexity(file_path)
                total_complexity += complexity
                file_count += 1
            except (OSError, UnicodeDecodeError, MemoryError):
                continue

        return total_complexity / max(file_count, 1) if file_count > 0 else 1.0

    async def _calculate_file_complexity(self, file_path: Path) -> float:
        """Calculate complexity for a single file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Count control flow statements as complexity indicators
            complexity = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    complexity += 0.5
                elif isinstance(node, ast.ClassDef):
                    complexity += 0.3

            return complexity
        except Exception:
            return 1.0

    async def _calculate_directory_complexity(self, directory: Path) -> float:
        """Calculate complexity for a directory"""
        python_files = list(directory.rglob("*.py"))
        if not python_files:
            return 1.0

        total_complexity = 0
        for file_path in python_files:
            total_complexity += await self._calculate_file_complexity(file_path)

        return total_complexity / len(python_files)

    async def _get_test_coverage(self) -> float:
        """Get test coverage percentage"""
        try:
            # Try to run coverage if available
            result = subprocess.run(
                ["coverage", "report", "--show-missing"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.repo_path,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "TOTAL" in line:
                        # Extract percentage from coverage output
                        parts = line.split()
                        for part in parts:
                            if part.endswith("%"):
                                return float(part[:-1])
        except Exception:
            pass

        # Fallback: estimate based on test file presence
        python_files = list(self.repo_path.rglob("*.py"))
        test_files = [f for f in python_files if "test" in str(f).lower()]

        if not python_files:
            return 0.0

        return min(len(test_files) / len(python_files) * 100, 100)

    async def _extract_dependencies(self) -> List[str]:
        """Extract key dependencies"""
        dependencies = []

        # Check requirements.txt files
        for req_file in self.repo_path.rglob("requirements*.txt"):
            try:
                with open(req_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dep = line.split("==")[0].split(">=")[0].split("<=")[0]
                            dependencies.append(dep)
            except Exception:
                continue

        # Check pyproject.toml
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r") as f:
                    content = f.read()
                    # Simple parsing - would use toml library in production
                    if "[tool.poetry.dependencies]" in content:
                        dependencies.append("poetry")
            except Exception:
                pass

        return list(set(dependencies))

    async def _extract_metrics(self) -> Dict[str, Any]:
        """Extract various metrics about the codebase"""
        metrics = {}

        # File count by type
        file_counts = defaultdict(int)
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_counts[ext] += 1

        metrics["file_counts"] = dict(file_counts)

        # Lines of code
        total_loc = 0
        python_loc = 0

        for py_file in self.repo_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = len(f.readlines())
                    python_loc += lines
                    total_loc += lines
            except Exception:
                continue

        metrics["lines_of_code"] = {"total": total_loc, "python": python_loc}

        # Git metrics if available
        if self.repo:
            try:
                commit_count = len(list(self.repo.iter_commits()))
                contributors = len(
                    set(commit.author.email for commit in self.repo.iter_commits())
                )
                metrics["git"] = {"commits": commit_count, "contributors": contributors}
            except Exception:
                pass

        return metrics

    async def _find_interesting_functions(self) -> List[Dict[str, Any]]:
        """Find interesting functions worth highlighting with memory optimization"""
        interesting_functions = []
        MAX_FILES_TO_SCAN = 15  # Reduced from 10 to balance discovery vs performance
        MAX_FILE_SIZE = 256 * 1024  # 256KB limit per file

        files_scanned = 0
        python_files_gen = self.repo_path.rglob("*.py")

        for file_path in python_files_gen:
            if files_scanned >= MAX_FILES_TO_SCAN:
                break

            try:
                # Skip large files
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue

                functions = await self._extract_functions_from_file(file_path)
                interesting_functions.extend(functions)
                files_scanned += 1
            except (OSError, UnicodeDecodeError, MemoryError):
                continue

        # Sort by "interestingness" (complexity, length, etc.)
        interesting_functions.sort(key=lambda x: x.get("complexity", 0), reverse=True)

        return interesting_functions[:10]

    async def _extract_functions_from_file(
        self, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Extract functions from a single file"""
        functions = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Calculate function complexity
                    func_complexity = 0
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                            func_complexity += 1

                    functions.append(
                        {
                            "name": node.name,
                            "file": str(file_path.relative_to(self.repo_path)),
                            "line": node.lineno,
                            "complexity": func_complexity,
                            "docstring": ast.get_docstring(node),
                            "args": [arg.arg for arg in node.args.args],
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                        }
                    )
        except Exception:
            pass

        return functions

    async def _get_recent_changes(self) -> List[Dict[str, Any]]:
        """Get recent changes from git history"""
        changes = []

        if not self.repo:
            return changes

        try:
            # Get last 10 commits
            commits = list(self.repo.iter_commits(max_count=10))

            for commit in commits:
                changes.append(
                    {
                        "hash": commit.hexsha[:8],
                        "message": commit.message.strip(),
                        "author": commit.author.name,
                        "date": commit.committed_datetime.isoformat(),
                        "files_changed": len(list(commit.stats.files.keys())),
                    }
                )
        except Exception:
            pass

        return changes

    async def _detect_patterns_in_directory(self, directory: Path) -> List[str]:
        """Detect patterns in a specific directory"""
        patterns = []

        # Check if it's a service directory
        if "service" in directory.name.lower():
            patterns.append("service_pattern")

        # Check for common structures
        if (directory / "tests").exists():
            patterns.append("test_driven")

        if (directory / "Dockerfile").exists():
            patterns.append("containerized_service")

        return patterns

    async def _detect_patterns_in_file(self, file_path: Path) -> List[str]:
        """Detect patterns in a specific file"""
        patterns = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for common patterns
            if "class" in content and "def __init__" in content:
                patterns.append("object_oriented")

            if "async def" in content:
                patterns.append("async_pattern")

            if "@" in content and "def" in content:
                patterns.append("decorator_pattern")

            if "pytest" in content or "unittest" in content:
                patterns.append("testing")

        except Exception:
            pass

        return patterns

    async def _analyze_commit_changes(self, commit) -> List[Dict[str, Any]]:
        """Analyze changes in a specific commit"""
        changes = []

        try:
            for file_path, stats in commit.stats.files.items():
                changes.append(
                    {
                        "file": file_path,
                        "insertions": stats["insertions"],
                        "deletions": stats["deletions"],
                        "lines_changed": stats["lines"],
                    }
                )
        except Exception:
            pass

        return changes

    async def _detect_patterns_in_commit(self, commit) -> List[str]:
        """Detect patterns from commit changes"""
        patterns = []

        # Analyze commit message for patterns
        message = commit.message.lower()

        if "fix" in message or "bug" in message:
            patterns.append("bug_fix")

        if "feat" in message or "feature" in message:
            patterns.append("feature_addition")

        if "refactor" in message:
            patterns.append("refactoring")

        if "test" in message:
            patterns.append("testing_improvement")

        return patterns

    async def _find_functions_in_directory(
        self, directory: Path
    ) -> List[Dict[str, Any]]:
        """Find interesting functions in a directory"""
        functions = []

        for py_file in directory.rglob("*.py"):
            try:
                file_functions = await self._extract_functions_from_file(py_file)
                functions.extend(file_functions)
            except Exception:
                continue

        return functions[:20]  # Limit results

    async def _extract_directory_dependencies(self, directory: Path) -> List[str]:
        """Extract dependencies specific to a directory"""
        dependencies = []

        # Look for requirements files in this directory
        for req_file in directory.glob("requirements*.txt"):
            try:
                with open(req_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dep = line.split("==")[0].split(">=")[0]
                            dependencies.append(dep)
            except Exception:
                continue

        return list(set(dependencies))
