#!/bin/bash
# Script to verify the CI langsmith fix works

echo "🔍 Verifying CI langsmith/pydantic fix..."

# Set up environment like CI does
export LANGCHAIN_TRACING_V2="false"
export LANGSMITH_TRACING="false"
export LANGCHAIN_TRACING="false"
export LANGCHAIN_CALLBACKS_MANAGER="false"
export PYTHONPATH=$PWD

# Activate virtual environment
source .venv/bin/activate

echo "✅ Environment configured"

# Test 1: Verify pytest loads without langsmith errors
echo "📋 Test 1: Checking pytest can load without langsmith errors..."
python -m pytest --version -p no:langsmith
if [ $? -eq 0 ]; then
    echo "✅ Pytest loads successfully with langsmith disabled"
else
    echo "❌ Pytest failed to load"
    exit 1
fi

# Test 2: Verify we can import langgraph without issues
echo "📋 Test 2: Checking langgraph import..."
python -c "import langgraph; print('✅ langgraph imported successfully')"
if [ $? -ne 0 ]; then
    echo "❌ Failed to import langgraph"
    exit 1
fi

# Test 3: Run a unit test that uses langgraph
echo "📋 Test 3: Running unit tests that import langgraph..."
pytest -q -p no:langsmith services/persona_runtime/tests/unit/test_runtime.py::test_dag_build_standard -v
if [ $? -eq 0 ]; then
    echo "✅ Unit test with langgraph passed"
else
    echo "❌ Unit test failed"
    exit 1
fi

# Test 4: Verify the exact CI command would work (without k8s dependency)
echo "📋 Test 4: Testing CI pytest arguments..."
PYTEST_ARGS="-q -p no:langsmith -n auto --maxprocesses=4 --dist loadscope --timeout=60"
pytest $PYTEST_ARGS tests/unit -x
if [ $? -eq 0 ]; then
    echo "✅ CI pytest command works for unit tests"
else
    echo "❌ CI pytest command failed"
    exit 1
fi

echo ""
echo "🎉 All verification tests passed!"
echo "✅ The langsmith/pydantic fix is working correctly"
echo "✅ CI should now pass once Docker/k3d issues are resolved"
echo ""
echo "📝 Summary of changes:"
echo "   - Added conftest.py to disable langsmith tracing"
echo "   - Added tests/conftest.py for additional test configuration"
echo "   - Environment variables properly set to disable langsmith"
echo ""
echo "⚠️  Note: e2e tests require a running k3d cluster which is currently unavailable due to Docker issues"