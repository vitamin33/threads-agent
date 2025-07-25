"""Root conftest.py to configure pytest environment."""

import os
import sys

# Disable langsmith/langchain tracing before any imports
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGCHAIN_CALLBACKS_MANAGER"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""

# Prevent pytest from loading the langsmith plugin
# This needs to happen before pytest loads plugins
def pytest_configure(config):
    """Configure pytest to disable langsmith plugin."""
    # Block langsmith plugin from loading
    config.pluginmanager.set_blocked("langsmith")
    
    # Also try to prevent its auto-discovery
    if hasattr(config.pluginmanager, "_plugin_distinfo"):
        # Remove langsmith from the list of plugins to load
        config.pluginmanager._plugin_distinfo = [
            info for info in config.pluginmanager._plugin_distinfo
            if "langsmith" not in str(info).lower()
        ]


# Early intervention to prevent langsmith plugin loading
def pytest_load_initial_conftests(early_config, parser, args):
    """Prevent langsmith from being loaded as early as possible."""
    early_config.pluginmanager.set_blocked("langsmith")