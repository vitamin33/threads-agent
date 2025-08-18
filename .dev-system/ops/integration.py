"""
Telemetry Integration Helpers
Easy integration patterns for adding telemetry to existing services
"""

import sys
from pathlib import Path
from typing import Any, Callable

# Add common services to path for integration
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
services_dir = project_root / "services"
common_dir = services_dir / "common"

if str(common_dir) not in sys.path:
    sys.path.insert(0, str(common_dir))
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))

from .telemetry import telemetry_decorator, openai_cost_calculator


# Service-specific decorators with pre-configured settings
def orchestrator_telemetry(func: Callable) -> Callable:
    """Telemetry decorator for orchestrator service"""
    return telemetry_decorator(agent_name="orchestrator", event_type="api_call")(func)


def persona_runtime_telemetry(func: Callable) -> Callable:
    """Telemetry decorator for persona runtime service"""
    return telemetry_decorator(
        agent_name="persona_runtime",
        event_type="model_call",
        cost_calculator=openai_cost_calculator,
    )(func)


def celery_worker_telemetry(func: Callable) -> Callable:
    """Telemetry decorator for celery worker"""
    return telemetry_decorator(agent_name="celery_worker", event_type="task_execution")(
        func
    )


def viral_engine_telemetry(func: Callable) -> Callable:
    """Telemetry decorator for viral engine"""
    return telemetry_decorator(
        agent_name="viral_engine",
        event_type="model_call",
        cost_calculator=openai_cost_calculator,
    )(func)


def model_call_telemetry(service_name: str) -> Callable:
    """Generic model call telemetry for any service"""

    def decorator(func: Callable) -> Callable:
        return telemetry_decorator(
            agent_name=service_name,
            event_type="model_call",
            cost_calculator=openai_cost_calculator,
        )(func)

    return decorator


def tool_call_telemetry(service_name: str) -> Callable:
    """Generic tool call telemetry for any service"""

    def decorator(func: Callable) -> Callable:
        return telemetry_decorator(agent_name=service_name, event_type="tool_call")(
            func
        )

    return decorator


# OpenAI Wrapper Integration
def wrap_openai_client():
    """Wrap OpenAI client with telemetry if available"""
    try:
        # Try to import and wrap the common OpenAI wrapper
        from openai_wrapper import chat

        @model_call_telemetry("openai_wrapper")
        def telemetry_chat(*args, **kwargs):
            return chat(*args, **kwargs)

        # Monkey patch the original function
        import openai_wrapper

        openai_wrapper.chat = telemetry_chat

        print("✅ OpenAI client wrapped with telemetry")
        return True

    except ImportError:
        print("⚠️  OpenAI wrapper not found - telemetry not applied")
        return False


# Auto-integration for common patterns
def auto_integrate_service(service_name: str, service_module: Any = None):
    """Automatically integrate telemetry into a service module"""
    integrations_applied = []

    # If module provided, try to wrap common function patterns
    if service_module:
        # Look for common AI function patterns
        for attr_name in dir(service_module):
            attr = getattr(service_module, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                # Apply telemetry to functions with AI-related names
                if any(
                    keyword in attr_name.lower()
                    for keyword in ["chat", "generate", "predict", "analyze", "process"]
                ):
                    wrapped_func = model_call_telemetry(service_name)(attr)
                    setattr(service_module, attr_name, wrapped_func)
                    integrations_applied.append(attr_name)

    if integrations_applied:
        print(
            f"✅ Applied telemetry to {service_name}: {', '.join(integrations_applied)}"
        )
    else:
        print(f"⚠️  No auto-integration targets found in {service_name}")

    return integrations_applied


# Example integration patterns
INTEGRATION_EXAMPLES = {
    "orchestrator": """
# In services/orchestrator/main.py
from dev_system.ops.integration import orchestrator_telemetry

@orchestrator_telemetry
async def create_task(task_data: dict):
    # Your existing function
    pass
""",
    "persona_runtime": """
# In services/persona_runtime/runtime.py  
from dev_system.ops.integration import persona_runtime_telemetry

@persona_runtime_telemetry
def generate_content(prompt: str):
    # Your existing OpenAI call
    pass
""",
    "viral_engine": """
# In services/viral_engine/main.py
from dev_system.ops.integration import viral_engine_telemetry

@viral_engine_telemetry
def optimize_hook(content: str):
    # Your existing function
    pass
""",
}
