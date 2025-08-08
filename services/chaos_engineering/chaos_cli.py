"""
Chaos Engineering CLI - Command-line interface for chaos experiments.

This module provides a comprehensive CLI for managing and running chaos experiments
with safety controls, monitoring, and integration with both custom and LitmusChaos operators.
"""

import asyncio
import json
import yaml
from typing import Dict, Any
import click
from pathlib import Path

from chaos_experiment_executor import ChaosExperimentExecutor
from litmus_chaos_integration import LitmusChaosManager


# CLI version
__version__ = "1.0.0"


@click.group()
@click.version_option(version=__version__, prog_name="Chaos Engineering CLI")
@click.pass_context
def cli(ctx):
    """
    Chaos Engineering CLI - Enterprise-grade chaos experiments for Kubernetes.

    This CLI provides comprehensive chaos engineering capabilities including:
    - Pod kill experiments
    - Network partitioning
    - CPU/Memory stress testing
    - Safety controls and monitoring
    - LitmusChaos integration
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    "--type",
    "experiment_type",
    type=click.Choice(
        ["pod_kill", "network_partition", "cpu_stress", "memory_pressure"]
    ),
    help="Type of chaos experiment to run",
)
@click.option("--name", required=False, help="Name of the experiment")
@click.option("--namespace", default="default", help="Kubernetes namespace")
@click.option("--target-app", help="Target application label")
@click.option("--duration", type=int, default=30, help="Duration in seconds")
@click.option("--config", type=click.Path(exists=True), help="JSON/YAML config file")
@click.option(
    "--safety-threshold", type=float, default=0.8, help="Safety threshold (0.0-1.0)"
)
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def run(
    experiment_type,
    name,
    namespace,
    target_app,
    duration,
    config,
    safety_threshold,
    output,
):
    """Run a chaos experiment with safety controls."""

    try:
        # Load configuration from file if provided
        if config:
            config_path = Path(config)
            if config_path.suffix == ".json":
                with open(config) as f:
                    experiment_config = json.load(f)
            elif config_path.suffix in [".yaml", ".yml"]:
                with open(config) as f:
                    experiment_config = yaml.safe_load(f)
            else:
                raise click.ClickException("Config file must be JSON or YAML")
        else:
            # Validate required arguments when not using config file
            if not experiment_type:
                raise click.ClickException(
                    "Experiment type is required when not using config file"
                )
            if not name:
                raise click.ClickException(
                    "Experiment name is required when not using config file"
                )
            if not target_app:
                raise click.ClickException(
                    "Target app is required when not using config file"
                )

            # Build configuration from CLI arguments
            experiment_config = {
                "name": name,
                "type": experiment_type,
                "target": {"namespace": namespace, "app_label": target_app},
                "duration": duration,
            }

        # Validate experiment type
        valid_types = ["pod_kill", "network_partition", "cpu_stress", "memory_pressure"]
        if experiment_config.get("type") not in valid_types:
            raise click.ClickException(
                f"Invalid experiment type. Must be one of: {', '.join(valid_types)}"
            )

        # Run the experiment
        executor = ChaosExperimentExecutor(safety_threshold=safety_threshold)
        result = asyncio.run(run_experiment(executor, experiment_config))

        # Output results
        if output == "json":
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(
                f"Experiment {result.experiment_name} completed with status: {result.status.value}"
            )
            click.echo(f"Execution time: {result.execution_time:.1f} seconds")
            click.echo(
                f"Safety checks: {'PASSED' if result.safety_checks_passed else 'FAILED'}"
            )
            if result.error_message:
                click.echo(f"Error: {result.error_message}")
            click.echo(f"Actions performed: {', '.join(result.actions_performed)}")

    except Exception as e:
        raise click.ClickException(f"Failed to run experiment: {str(e)}")


@cli.command()
@click.option("--namespace", default="litmus", help="LitmusChaos namespace")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def list(namespace, output):
    """List all chaos experiments."""

    try:
        manager = LitmusChaosManager(namespace=namespace)
        result = asyncio.run(list_experiments(manager))

        if output == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("Chaos Experiments:")
            click.echo("=" * 80)

            if not result.get("items"):
                click.echo("No experiments found.")
                return

            for item in result["items"]:
                name = item["metadata"]["name"]
                created = item["metadata"].get("creationTimestamp", "Unknown")
                status = item.get("status", {}).get("phase", "Unknown")

                click.echo(f"Name: {name}")
                click.echo(f"  Status: {status}")
                click.echo(f"  Created: {created}")
                click.echo("")

    except Exception as e:
        raise click.ClickException(f"Failed to list experiments: {str(e)}")


@cli.command()
@click.argument("experiment_name")
@click.option("--namespace", default="litmus", help="LitmusChaos namespace")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def status(experiment_name, namespace, output):
    """Get the status of a specific chaos experiment."""

    try:
        manager = LitmusChaosManager(namespace=namespace)
        result = asyncio.run(get_experiment_status(manager, experiment_name))

        if output == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Experiment: {experiment_name}")
            click.echo("=" * 50)

            status_info = result.get("status", {})
            phase = status_info.get("phase", "Unknown")
            click.echo(f"Phase: {phase}")

            if "experimentStatus" in status_info:
                click.echo("\nExperiment Results:")
                for exp_name, exp_result in status_info["experimentStatus"].items():
                    verdict = exp_result.get("verdict", "Unknown")
                    success_rate = exp_result.get("probeSuccessPercentage", "Unknown")
                    click.echo(f"  {exp_name}: {verdict} ({success_rate}% success)")

    except Exception as e:
        raise click.ClickException(f"Failed to get experiment status: {str(e)}")


@cli.command()
@click.argument("experiment_name")
def stop(experiment_name):
    """Stop a running chaos experiment (emergency stop)."""

    try:
        executor = ChaosExperimentExecutor()
        asyncio.run(stop_experiment(executor, experiment_name))

        click.echo(f"Emergency stop triggered for experiment: {experiment_name}")
        click.echo("Note: It may take a few moments for the experiment to fully stop.")

    except Exception as e:
        raise click.ClickException(f"Failed to stop experiment: {str(e)}")


@cli.command()
@click.option(
    "--yaml",
    "yaml_file",
    type=click.Path(exists=True),
    help="YAML file with ChaosEngine specification",
)
@click.option("--namespace", default="litmus", help="LitmusChaos namespace")
def create(yaml_file, namespace):
    """Create a chaos experiment from YAML ChaosEngine specification."""

    try:
        if not yaml_file:
            raise click.ClickException("YAML file path is required")

        with open(yaml_file) as f:
            chaos_spec = yaml.safe_load(f)

        # Validate basic ChaosEngine structure
        if chaos_spec.get("kind") != "ChaosEngine":
            raise click.ClickException("YAML file must contain a ChaosEngine resource")

        experiment_name = chaos_spec["metadata"]["name"]
        click.echo(f"Creating chaos experiment: {experiment_name}")

        # Parse and display experiment details
        spec = chaos_spec.get("spec", {})
        app_info = spec.get("appinfo", {})
        experiments = spec.get("experiments", [])

        click.echo(f"Target namespace: {app_info.get('appns', 'default')}")
        click.echo(f"Target app: {app_info.get('applabel', 'unknown')}")
        click.echo(f"Experiments: {len(experiments)}")

        for exp in experiments:
            click.echo(f"  - {exp.get('name', 'unknown')}")

        click.echo(f"\nExperiment {experiment_name} configuration loaded successfully.")
        click.echo(
            "Note: This is a dry-run. Use appropriate tools to apply the ChaosEngine to Kubernetes."
        )

    except Exception as e:
        raise click.ClickException(f"Failed to create experiment: {str(e)}")


# Helper functions for async operations
async def run_experiment(executor: ChaosExperimentExecutor, config: Dict[str, Any]):
    """Helper function to run an experiment asynchronously."""
    return await executor.execute_experiment(config)


async def list_experiments(manager: LitmusChaosManager):
    """Helper function to list experiments asynchronously."""
    return await manager.list_experiments()


async def get_experiment_status(manager: LitmusChaosManager, experiment_name: str):
    """Helper function to get experiment status asynchronously."""
    return await manager.get_experiment_status(experiment_name)


async def stop_experiment(executor: ChaosExperimentExecutor, experiment_name: str):
    """Helper function to stop an experiment asynchronously."""
    await executor.emergency_stop()


def create_experiment_from_yaml(yaml_content: str) -> Dict[str, Any]:
    """Helper function to parse YAML experiment configuration."""
    return yaml.safe_load(yaml_content)


if __name__ == "__main__":
    cli()
