#!/usr/bin/env python3
"""
Test Impact Analysis - Only run tests for changed code
Analyzes git diff to determine which tests should run based on code changes
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple

class TestImpactAnalyzer:
    def __init__(self):
        self.service_test_mapping = {
            'orchestrator': ['services/orchestrator/tests/', 'tests/e2e/test_orchestrator'],
            'celery_worker': ['services/celery_worker/tests/', 'tests/e2e/test_celery'],
            'persona_runtime': ['services/persona_runtime/tests/', 'tests/e2e/test_persona'],
            'viral_engine': ['services/viral_engine/tests/', 'tests/e2e/test_viral'],
            'fake_threads': ['services/fake_threads/tests/'],
            'threads_adaptor': ['services/threads_adaptor/tests/'],
            'achievement_collector': ['services/achievement_collector/tests/'],
            'performance_monitor': ['services/performance_monitor/tests/'],
            'common': ['services/common/tests/', 'tests/unit/'],
        }
        
        self.critical_paths = {
            'chart/': ['tests/e2e/'],  # Helm changes require e2e tests
            'docker/': ['tests/e2e/'],  # Docker changes require e2e tests
            '.github/workflows/': [],  # CI changes don't require tests
            'docs/': [],  # Documentation changes don't require tests
            '*.md': [],  # Markdown changes don't require tests
        }

    def get_changed_files(self, base_branch: str = 'origin/main') -> List[str]:
        """Get list of changed files compared to base branch"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'{base_branch}...HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return [f for f in result.stdout.strip().split('\n') if f]
        except subprocess.CalledProcessError:
            # Fallback to unstaged changes
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                capture_output=True,
                text=True
            )
            return [f for f in result.stdout.strip().split('\n') if f]

    def analyze_file_change(self, filepath: str) -> Set[str]:
        """Determine which tests should run for a given file change"""
        tests_to_run = set()
        
        # Skip the test-impact-analysis script itself
        if 'test-impact-analysis.py' in filepath:
            return tests_to_run
            
        # Check if it's a test file itself
        if 'test' in filepath or 'spec' in filepath:
            # Only add if it's actually a test file, not a script
            if filepath.startswith('tests/') or '/tests/' in filepath or '/test_' in filepath:
                tests_to_run.add(filepath)
            return tests_to_run
        
        # Check critical paths
        for pattern, test_paths in self.critical_paths.items():
            if pattern.endswith('/'):
                if filepath.startswith(pattern):
                    tests_to_run.update(test_paths)
            elif '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(filepath, pattern):
                    tests_to_run.update(test_paths)
        
        # Check service-specific changes
        for service, test_paths in self.service_test_mapping.items():
            if f'services/{service}/' in filepath:
                tests_to_run.update(test_paths)
                
        # Check for model/schema changes (require integration tests)
        if any(pattern in filepath for pattern in ['models.py', 'schemas.py', 'database.py']):
            tests_to_run.add('tests/e2e/')
            
        # Check for API endpoint changes
        if any(pattern in filepath for pattern in ['routes/', 'endpoints/', 'api/']):
            tests_to_run.add('tests/e2e/')
            
        return tests_to_run

    def get_import_dependencies(self, filepath: str) -> Set[str]:
        """Analyze Python imports to find dependent modules"""
        dependencies = set()
        
        if not filepath.endswith('.py'):
            return dependencies
            
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Find all imports
            import_pattern = r'(?:from\s+([\w\.]+)|import\s+([\w\.]+))'
            matches = re.findall(import_pattern, content)
            
            for match in matches:
                module = match[0] or match[1]
                if module.startswith('services.'):
                    service = module.split('.')[1]
                    if service in self.service_test_mapping:
                        dependencies.update(self.service_test_mapping[service])
                        
        except Exception as e:
            print(f"Warning: Could not analyze {filepath}: {e}", file=sys.stderr)
            
        return dependencies

    def analyze(self, changed_files: List[str]) -> Tuple[List[str], bool]:
        """
        Analyze changed files and return tests to run
        Returns: (list of test paths, should_run_all_tests)
        """
        all_tests = set()
        run_all = False
        
        for filepath in changed_files:
            # Check if critical infrastructure changed
            if any(critical in filepath for critical in ['requirements.txt', 'setup.py', 'pyproject.toml']):
                run_all = True
                break
                
            # Get direct test requirements
            tests = self.analyze_file_change(filepath)
            all_tests.update(tests)
            
            # Get dependency test requirements
            deps = self.get_import_dependencies(filepath)
            all_tests.update(deps)
        
        # Remove empty strings and sort
        test_list = sorted([t for t in all_tests if t])
        
        # If no tests identified but code changed, run unit tests at least
        if not test_list and not run_all and any('.py' in f for f in changed_files):
            test_list = ['tests/unit/']
            
        return test_list, run_all

    def generate_pytest_command(self, test_paths: List[str], extra_args: str = '') -> str:
        """Generate optimized pytest command"""
        if not test_paths:
            return ''
            
        # Filter out non-existent paths and non-test files
        existing_paths = []
        for path in test_paths:
            p = Path(path)
            # Skip non-Python files and config files
            if path.endswith('.ini') or path.endswith('.sh') or path.endswith('.skip'):
                continue
            # Only include Python test files or test directories
            if p.exists() and (p.is_dir() or (path.endswith('.py') and ('test' in path or 'spec' in path))):
                existing_paths.append(path)
                
        if not existing_paths:
            return ''
            
        # Build pytest command
        cmd_parts = ['pytest']
        
        # Add parallelization if multiple test directories
        if len(existing_paths) > 1:
            cmd_parts.append('-n auto')
            
        # Add coverage only for service tests
        if any('services/' in p for p in existing_paths):
            cmd_parts.append('--cov=services --cov-report=xml')
            
        # Add paths
        cmd_parts.extend(existing_paths)
        
        # Add extra arguments
        if extra_args:
            cmd_parts.append(extra_args)
            
        return ' '.join(cmd_parts)

def main():
    parser = argparse.ArgumentParser(description='Analyze test impact based on code changes')
    parser.add_argument('--changed-files', help='Comma-separated list of changed files')
    parser.add_argument('--base-branch', default='origin/main', help='Base branch for comparison')
    parser.add_argument('--output', help='Output file for test paths')
    parser.add_argument('--format', choices=['list', 'pytest', 'json'], default='list', help='Output format')
    parser.add_argument('--pytest-args', default='', help='Additional pytest arguments')
    
    args = parser.parse_args()
    
    analyzer = TestImpactAnalyzer()
    
    # Get changed files
    if args.changed_files:
        changed_files = args.changed_files.split(',')
    else:
        changed_files = analyzer.get_changed_files(args.base_branch)
    
    if not changed_files:
        print("No changed files detected", file=sys.stderr)
        sys.exit(0)
    
    # Analyze impact
    test_paths, run_all = analyzer.analyze(changed_files)
    
    # Format output
    if run_all:
        output = 'ALL_TESTS'
    elif args.format == 'pytest':
        output = analyzer.generate_pytest_command(test_paths, args.pytest_args)
    elif args.format == 'json':
        output = json.dumps({
            'test_paths': test_paths,
            'run_all': run_all,
            'changed_files': changed_files
        })
    else:
        output = '\n'.join(test_paths) if test_paths else 'NO_TESTS'
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)
    
    # Exit code indicates if tests should run
    sys.exit(0 if test_paths or run_all else 1)

if __name__ == '__main__':
    main()