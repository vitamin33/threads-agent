"""
API Contract Tests for Airflow Operators (CRA-284)

This module provides comprehensive contract tests to ensure API compatibility
and adherence to service contracts across all viral learning services.

Test Categories:
- Service API contract validation
- Schema compatibility testing
- Backward compatibility verification
- API versioning compliance
- Error response standardization

Requirements:
- All tests must complete within 1 second
- 90%+ API contract coverage
- Schema validation for all endpoints
- Version compatibility checks
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch
import jsonschema
from jsonschema import validate, ValidationError

# Import operators for testing
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../operators"))

from health_check_operator import HealthCheckOperator
from metrics_collector_operator import MetricsCollectorOperator


class APIContractValidator:
    """Utility class for API contract validation."""

    # Standard API response schemas
    HEALTH_CHECK_SCHEMA = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
            "timestamp": {"type": "string", "format": "date-time"},
            "response_time_ms": {"type": "number", "minimum": 0},
            "version": {"type": "string"},
            "service_name": {"type": "string"},
            "dependencies": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
        },
        "required": ["status", "timestamp"],
    }

    METRICS_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "timestamp": {"type": "string", "format": "date-time"},
            "service_name": {"type": "string"},
            "metrics": {
                "type": "object",
                "properties": {
                    "business_kpis": {
                        "type": "object",
                        "properties": {
                            "engagement_rate": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "cost_per_follow": {"type": "number", "minimum": 0},
                            "viral_coefficient": {"type": "number", "minimum": 0},
                            "revenue_projection_monthly": {
                                "type": "number",
                                "minimum": 0,
                            },
                        },
                    },
                    "performance_metrics": {
                        "type": "object",
                        "properties": {
                            "response_time_ms": {"type": "number", "minimum": 0},
                            "throughput_rps": {"type": "number", "minimum": 0},
                            "error_rate": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                    },
                },
            },
        },
        "required": ["timestamp", "service_name", "metrics"],
    }

    ERROR_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "request_id": {"type": "string"},
                    "details": {"type": "object"},
                },
                "required": ["code", "message", "timestamp"],
            }
        },
        "required": ["error"],
    }

    @classmethod
    def validate_health_response(cls, response_data: Dict[str, Any]) -> bool:
        """Validate health check response against schema."""
        try:
            validate(instance=response_data, schema=cls.HEALTH_CHECK_SCHEMA)
            return True
        except ValidationError:
            return False

    @classmethod
    def validate_metrics_response(cls, response_data: Dict[str, Any]) -> bool:
        """Validate metrics response against schema."""
        try:
            validate(instance=response_data, schema=cls.METRICS_RESPONSE_SCHEMA)
            return True
        except ValidationError:
            return False

    @classmethod
    def validate_error_response(cls, response_data: Dict[str, Any]) -> bool:
        """Validate error response against schema."""
        try:
            validate(instance=response_data, schema=cls.ERROR_RESPONSE_SCHEMA)
            return True
        except ValidationError:
            return False


class TestServiceAPIContracts:
    """Test API contracts for all viral learning services."""

    @pytest.fixture
    def service_contracts(self):
        """Define expected API contracts for each service."""
        return {
            "orchestrator": {
                "base_url": "http://orchestrator:8080",
                "endpoints": {
                    "/health": {
                        "methods": ["GET"],
                        "response_schema": APIContractValidator.HEALTH_CHECK_SCHEMA,
                        "expected_fields": ["status", "timestamp", "dependencies"],
                    },
                    "/metrics": {
                        "methods": ["GET"],
                        "response_schema": APIContractValidator.METRICS_RESPONSE_SCHEMA,
                        "expected_fields": ["timestamp", "service_name", "metrics"],
                    },
                    "/thompson-sampling/metrics": {
                        "methods": ["GET"],
                        "parameters": ["hours"],
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "experiment_id": {"type": "string"},
                                "variants": {"type": "array"},
                                "convergence_probability": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                            "required": ["experiment_id", "variants"],
                        },
                    },
                },
                "required_dependencies": ["database", "rabbitmq"],
                "version": "v1",
            },
            "viral_scraper": {
                "base_url": "http://viral-scraper:8080",
                "endpoints": {
                    "/health": {
                        "methods": ["GET"],
                        "response_schema": APIContractValidator.HEALTH_CHECK_SCHEMA,
                        "expected_fields": ["status", "timestamp"],
                    },
                    "/metrics": {
                        "methods": ["GET"],
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "scraping_metrics": {
                                    "type": "object",
                                    "properties": {
                                        "posts_scraped": {
                                            "type": "integer",
                                            "minimum": 0,
                                        },
                                        "success_rate": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "rate_limit_hits": {
                                            "type": "integer",
                                            "minimum": 0,
                                        },
                                    },
                                }
                            },
                            "required": ["scraping_metrics"],
                        },
                    },
                    "/rate-limit/metrics": {
                        "methods": ["GET"],
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "active_limits": {"type": "integer", "minimum": 0},
                                "violations": {"type": "integer", "minimum": 0},
                                "reset_time": {"type": "string"},
                            },
                        },
                    },
                },
                "version": "v1",
            },
            "viral_engine": {
                "base_url": "http://viral-engine:8080",
                "endpoints": {
                    "/health": {
                        "methods": ["GET"],
                        "response_schema": APIContractValidator.HEALTH_CHECK_SCHEMA,
                    },
                    "/metrics/patterns": {
                        "methods": ["GET"],
                        "parameters": ["hours"],
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "patterns_extracted": {"type": "integer", "minimum": 0},
                                "pattern_types": {"type": "array"},
                                "extraction_rate": {"type": "number", "minimum": 0},
                            },
                        },
                    },
                    "/metrics/predictions": {
                        "methods": ["GET"],
                        "parameters": ["hours"],
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "predictions_made": {"type": "integer", "minimum": 0},
                                "accuracy": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "model_version": {"type": "string"},
                            },
                        },
                    },
                },
                "version": "v1",
            },
        }

    @pytest.mark.contract
    async def test_health_endpoint_contracts(self, service_contracts):
        """Test health endpoint contracts for all services."""
        start_time = time.time()

        for service_name, contract in service_contracts.items():
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Create compliant health response
                health_response_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "response_time_ms": 45.0,
                    "version": contract["version"],
                    "service_name": service_name,
                }

                # Add required dependencies for orchestrator
                if service_name == "orchestrator":
                    health_response_data["dependencies"] = {
                        "database": "connected",
                        "rabbitmq": "connected",
                    }

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = health_response_data
                mock_response.elapsed.total_seconds.return_value = 0.045
                mock_session.get.return_value = mock_response

                # Test health check operator with this service
                health_operator = HealthCheckOperator(
                    task_id=f"contract_test_{service_name}",
                    service_urls={service_name: contract["base_url"]},
                )

                results = health_operator.execute({})

                # Validate contract compliance
                service_health = results["services"][service_name]
                assert service_health["status"] == "healthy"

                # Validate response schema
                response_details = service_health.get("details", {})
                if response_details:
                    assert APIContractValidator.validate_health_response(
                        response_details
                    )

                    # Check required fields
                    health_contract = contract["endpoints"]["/health"]
                    for field in health_contract.get("expected_fields", []):
                        assert field in response_details, (
                            f"Missing required field '{field}' in {service_name} health response"
                        )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Health contract test took {execution_time:.2f}s"

    @pytest.mark.contract
    async def test_metrics_endpoint_contracts(self, service_contracts):
        """Test metrics endpoint contracts for all services."""
        start_time = time.time()

        for service_name, contract in service_contracts.items():
            metrics_endpoints = [
                ep for ep in contract["endpoints"].keys() if "metrics" in ep
            ]

            for endpoint in metrics_endpoints:
                with patch("requests.Session") as mock_session_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    # Create contract-compliant response based on endpoint
                    if endpoint == "/metrics":
                        response_data = self._create_standard_metrics_response(
                            service_name
                        )
                    elif endpoint == "/thompson-sampling/metrics":
                        response_data = {
                            "experiment_id": "test_experiment_001",
                            "variants": [
                                {"id": "variant_a", "performance": 0.067},
                                {"id": "variant_b", "performance": 0.045},
                            ],
                            "convergence_probability": 0.89,
                        }
                    elif endpoint == "/metrics/patterns":
                        response_data = {
                            "patterns_extracted": 156,
                            "pattern_types": [
                                "curiosity_gap",
                                "controversy",
                                "story_hook",
                            ],
                            "extraction_rate": 0.94,
                        }
                    elif endpoint == "/metrics/predictions":
                        response_data = {
                            "predictions_made": 89,
                            "accuracy": 0.73,
                            "model_version": "v2.1.0",
                        }
                    elif endpoint == "/rate-limit/metrics":
                        response_data = {
                            "active_limits": 3,
                            "violations": 0,
                            "reset_time": datetime.now().isoformat(),
                        }
                    else:
                        response_data = {"status": "ok"}

                    # Setup mock responses
                    health_response = Mock()
                    health_response.status_code = 200
                    health_response.json.return_value = {"status": "healthy"}
                    health_response.elapsed.total_seconds.return_value = 0.01

                    metrics_response = Mock()
                    metrics_response.status_code = 200
                    metrics_response.json.return_value = response_data

                    mock_session.get.side_effect = [health_response, metrics_response]

                    # Test metrics collection with this service
                    metrics_operator = MetricsCollectorOperator(
                        task_id=f"metrics_contract_test_{service_name}",
                        service_urls={service_name: contract["base_url"]},
                    )

                    results = metrics_operator.execute({})

                    # Validate contract compliance
                    service_metrics = results["services"][service_name]
                    assert service_metrics["status"] in ["success", "partial"]

                    # Validate response schema
                    endpoint_contract = contract["endpoints"][endpoint]
                    if "response_schema" in endpoint_contract:
                        try:
                            validate(
                                instance=response_data,
                                schema=endpoint_contract["response_schema"],
                            )
                        except ValidationError as e:
                            pytest.fail(
                                f"Schema validation failed for {service_name}{endpoint}: {e}"
                            )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Metrics contract test took {execution_time:.2f}s"

    @pytest.mark.contract
    async def test_error_response_contracts(self, service_contracts):
        """Test error response contracts across all services."""
        start_time = time.time()

        for service_name, contract in service_contracts.items():
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Simulate various error conditions
                error_scenarios = [
                    {
                        "status_code": 400,
                        "error_data": {
                            "error": {
                                "code": "BAD_REQUEST",
                                "message": "Invalid request parameters",
                                "timestamp": datetime.now().isoformat(),
                                "request_id": "req_123456",
                            }
                        },
                    },
                    {
                        "status_code": 503,
                        "error_data": {
                            "error": {
                                "code": "SERVICE_UNAVAILABLE",
                                "message": "Service temporarily unavailable",
                                "timestamp": datetime.now().isoformat(),
                                "request_id": "req_789012",
                            }
                        },
                    },
                ]

                for scenario in error_scenarios:
                    mock_response = Mock()
                    mock_response.status_code = scenario["status_code"]
                    mock_response.json.return_value = scenario["error_data"]
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    mock_session.get.return_value = mock_response

                    health_operator = HealthCheckOperator(
                        task_id=f"error_contract_test_{service_name}_{scenario['status_code']}",
                        service_urls={service_name: contract["base_url"]},
                        max_retries=1,
                    )

                    results = health_operator.execute({})

                    # Validate error handling
                    service_health = results["services"][service_name]
                    assert service_health["status"] == "unhealthy"

                    # Validate error response schema if available
                    if "details" in service_health and isinstance(
                        service_health["details"], dict
                    ):
                        if "error" in service_health["details"]:
                            assert APIContractValidator.validate_error_response(
                                service_health["details"]
                            )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Error contract test took {execution_time:.2f}s"

    def _create_standard_metrics_response(self, service_name: str) -> Dict[str, Any]:
        """Create standardized metrics response for a service."""
        base_response = {
            "timestamp": datetime.now().isoformat(),
            "service_name": service_name,
            "metrics": {
                "performance_metrics": {
                    "response_time_ms": 45.0,
                    "throughput_rps": 100.0,
                    "error_rate": 0.01,
                }
            },
        }

        if service_name == "orchestrator":
            base_response["metrics"]["business_kpis"] = {
                "engagement_rate": 0.067,
                "cost_per_follow": 0.009,
                "viral_coefficient": 1.25,
                "revenue_projection_monthly": 18500.0,
            }
        elif service_name == "viral_scraper":
            base_response["metrics"]["scraping_metrics"] = {
                "posts_scraped": 1440,
                "success_rate": 0.94,
                "rate_limit_hits": 2,
            }

        return base_response


class TestAPIVersionCompatibility:
    """Test API version compatibility and backward compatibility."""

    @pytest.fixture
    def version_scenarios(self):
        """Define version compatibility test scenarios."""
        return {
            "v1_compatibility": {
                "client_version": "v1",
                "server_versions": ["v1", "v1.1", "v1.2"],
                "expected_compatibility": True,
            },
            "v2_compatibility": {
                "client_version": "v2",
                "server_versions": ["v2", "v2.1"],
                "expected_compatibility": True,
            },
            "incompatible_versions": {
                "client_version": "v1",
                "server_versions": ["v2", "v3"],
                "expected_compatibility": False,
            },
        }

    @pytest.mark.contract
    @pytest.mark.version
    async def test_backward_compatibility(self, version_scenarios):
        """Test backward compatibility across API versions."""
        start_time = time.time()

        for scenario_name, scenario in version_scenarios.items():
            for server_version in scenario["server_versions"]:
                with patch("requests.Session") as mock_session_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    # Create version-specific response
                    response_data = {
                        "status": "healthy",
                        "timestamp": datetime.now().isoformat(),
                        "api_version": server_version,
                        "client_version": scenario["client_version"],
                        "compatible": scenario["expected_compatibility"],
                    }

                    mock_response = Mock()
                    mock_response.status_code = (
                        200 if scenario["expected_compatibility"] else 400
                    )
                    mock_response.json.return_value = response_data
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    mock_session.get.return_value = mock_response

                    health_operator = HealthCheckOperator(
                        task_id=f"version_test_{scenario_name}_{server_version}",
                        service_urls={"version_service": "http://version-service:8080"},
                    )

                    if scenario["expected_compatibility"]:
                        results = health_operator.execute({})
                        assert (
                            results["services"]["version_service"]["status"]
                            == "healthy"
                        )
                    else:
                        # Incompatible versions should result in unhealthy status
                        results = health_operator.execute({})
                        assert (
                            results["services"]["version_service"]["status"]
                            == "unhealthy"
                        )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Version compatibility test took {execution_time:.2f}s"
        )

    @pytest.mark.contract
    async def test_api_deprecation_warnings(self):
        """Test proper handling of API deprecation warnings."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Response with deprecation warning
            response_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "warnings": [
                    {
                        "type": "deprecation",
                        "message": "This endpoint will be deprecated in v2.0",
                        "sunset_date": "2024-12-31T00:00:00Z",
                        "replacement": "/v2/health",
                    }
                ],
            }

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_response.headers = {
                "Deprecation": "true",
                "Sunset": "2024-12-31T00:00:00Z",
            }
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="deprecation_test",
                service_urls={"deprecated_service": "http://deprecated-service:8080"},
            )

            results = health_operator.execute({})

            # Service should still be healthy but warnings should be captured
            assert results["services"]["deprecated_service"]["status"] == "healthy"

            # Check if deprecation information is preserved
            details = results["services"]["deprecated_service"].get("details", {})
            if "warnings" in details:
                deprecation_warnings = [
                    w for w in details["warnings"] if w["type"] == "deprecation"
                ]
                assert len(deprecation_warnings) > 0

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Deprecation test took {execution_time:.2f}s"


class TestSchemaEvolution:
    """Test schema evolution and compatibility."""

    @pytest.mark.contract
    async def test_additive_schema_changes(self):
        """Test that additive schema changes don't break compatibility."""
        start_time = time.time()

        # Original schema
        original_response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
        }

        # Enhanced schema with new fields
        enhanced_response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": 86400,
            "build_version": "1.2.3",
            "environment": "production",
            "features": ["feature_a", "feature_b"],
        }

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Test both schemas
            for response_data in [original_response, enhanced_response]:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = response_data
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id="schema_evolution_test",
                    service_urls={"evolving_service": "http://evolving-service:8080"},
                )

                results = health_operator.execute({})

                # Both should work - additive changes are compatible
                assert results["services"]["evolving_service"]["status"] == "healthy"

                # Original required fields should always be present
                details = results["services"]["evolving_service"].get("details", {})
                if details:
                    assert APIContractValidator.validate_health_response(details)

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Schema evolution test took {execution_time:.2f}s"

    @pytest.mark.contract
    async def test_field_type_changes(self):
        """Test handling of field type changes in responses."""
        start_time = time.time()

        type_change_scenarios = [
            {
                "name": "string_to_number",
                "old_value": "45",
                "new_value": 45,
                "field": "response_time_ms",
            },
            {
                "name": "number_to_string",
                "old_value": 86400,
                "new_value": "86400",
                "field": "uptime_seconds",
            },
        ]

        for scenario in type_change_scenarios:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                response_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    scenario["field"]: scenario["new_value"],
                }

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = response_data
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id=f"type_change_test_{scenario['name']}",
                    service_urls={
                        "type_changing_service": "http://type-changing-service:8080"
                    },
                )

                # Should handle type changes gracefully
                results = health_operator.execute({})
                assert (
                    results["services"]["type_changing_service"]["status"] == "healthy"
                )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Type change test took {execution_time:.2f}s"


class TestContractCompliance:
    """Test overall contract compliance and governance."""

    @pytest.mark.contract
    async def test_contract_validation_coverage(self, service_contracts):
        """Test that all defined contracts are validated."""
        start_time = time.time()

        total_endpoints = 0
        validated_endpoints = 0

        for service_name, contract in service_contracts.items():
            for endpoint, endpoint_config in contract["endpoints"].items():
                total_endpoints += 1

                # Check if endpoint has proper schema definition
                if "response_schema" in endpoint_config:
                    validated_endpoints += 1

                    # Verify schema is valid JSON Schema
                    try:
                        jsonschema.Draft7Validator.check_schema(
                            endpoint_config["response_schema"]
                        )
                    except jsonschema.SchemaError as e:
                        pytest.fail(f"Invalid schema for {service_name}{endpoint}: {e}")

        # Ensure high coverage of contract validation
        coverage_ratio = (
            validated_endpoints / total_endpoints if total_endpoints > 0 else 0
        )
        assert coverage_ratio >= 0.9, (
            f"Contract validation coverage ({coverage_ratio:.2%}) below 90% threshold"
        )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Coverage test took {execution_time:.2f}s"

    @pytest.mark.contract
    async def test_required_fields_compliance(self, service_contracts):
        """Test compliance with required fields across all contracts."""
        start_time = time.time()

        for service_name, contract in service_contracts.items():
            health_endpoint = contract["endpoints"].get("/health", {})
            required_fields = health_endpoint.get("required_fields", [])

            if required_fields:
                with patch("requests.Session") as mock_session_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    # Create response with all required fields
                    complete_response = {
                        "status": "healthy",
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Add service-specific required fields
                    if "dependencies" in required_fields:
                        complete_response["dependencies"] = {"database": "connected"}

                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = complete_response
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    mock_session.get.return_value = mock_response

                    health_operator = HealthCheckOperator(
                        task_id=f"required_fields_test_{service_name}",
                        service_urls={service_name: contract["base_url"]},
                    )

                    results = health_operator.execute({})

                    # Validate all required fields are present
                    service_details = results["services"][service_name].get(
                        "details", {}
                    )
                    for field in required_fields:
                        assert field in service_details, (
                            f"Required field '{field}' missing from {service_name} response"
                        )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Required fields test took {execution_time:.2f}s"
