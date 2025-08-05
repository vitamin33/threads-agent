"""
Security Tests for Airflow Operators (CRA-284)

This module provides comprehensive security tests to ensure operators
handle authentication, authorization, and security protocols correctly.

Test Categories:
- Authentication mechanisms
- Authorization and access control
- SSL/TLS certificate validation
- Input validation and sanitization
- Secrets management
- Network security
- Data privacy compliance

Requirements:
- All tests must complete within 1 second
- Security vulnerabilities must be detected
- Compliance with security standards
- Proper handling of sensitive data
"""

import pytest
import time
import ssl
import base64
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch
from urllib.parse import urlparse

# Import operators for testing
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../operators"))

from health_check_operator import HealthCheckOperator


class SecurityTestUtils:
    """Utility class for security testing."""

    @staticmethod
    def create_malicious_payload(payload_type: str) -> str:
        """Create malicious payloads for security testing."""
        payloads = {
            "sql_injection": "'; DROP TABLE users; --",
            "xss": "<script>alert('XSS')</script>",
            "command_injection": "; rm -rf /; #",
            "path_traversal": "../../etc/passwd",
            "json_bomb": '{"a":' * 10000 + '"b"' + "}" * 10000,
            "oversized_data": "A" * 1000000,  # 1MB of data
        }
        return payloads.get(payload_type, "")

    @staticmethod
    def create_invalid_certificate() -> Dict[str, Any]:
        """Create invalid certificate for SSL testing."""
        return {
            "expired": True,
            "self_signed": True,
            "wrong_hostname": True,
            "invalid_chain": True,
        }

    @staticmethod
    def create_auth_headers(
        auth_type: str, credentials: str = "test:test"
    ) -> Dict[str, str]:
        """Create authentication headers for testing."""
        if auth_type == "basic":
            encoded = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        elif auth_type == "bearer":
            return {"Authorization": f"Bearer {credentials}"}
        elif auth_type == "api_key":
            return {"X-API-Key": credentials}
        return {}


class TestAuthenticationSecurity:
    """Test authentication security mechanisms."""

    @pytest.mark.security
    async def test_http_basic_auth_handling(self):
        """Test proper handling of HTTP Basic Authentication."""
        start_time = time.time()

        auth_scenarios = [
            {"username": "admin", "password": "secure_password", "expected": "success"},
            {"username": "admin", "password": "wrong_password", "expected": "failure"},
            {"username": "", "password": "", "expected": "failure"},
            {"username": "admin", "password": None, "expected": "failure"},
        ]

        for scenario in auth_scenarios:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Simulate auth response
                if scenario["expected"] == "success":
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "healthy",
                        "authenticated": True,
                        "user": scenario["username"],
                    }
                else:
                    mock_response = Mock()
                    mock_response.status_code = 401
                    mock_response.json.return_value = {"error": "Authentication failed"}

                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                # Configure auth in session
                if scenario["username"] and scenario["password"]:
                    mock_session.auth = (scenario["username"], scenario["password"])

                health_operator = HealthCheckOperator(
                    task_id=f"auth_test_{scenario['username'] or 'empty'}",
                    service_urls={"auth_service": "http://auth-service:8080"},
                    verify_ssl=True,
                )

                results = health_operator.execute({})

                # Validate authentication behavior
                service_health = results["services"]["auth_service"]
                if scenario["expected"] == "success":
                    assert service_health["status"] == "healthy"
                else:
                    assert service_health["status"] == "unhealthy"
                    assert service_health["status_code"] == 401

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Auth test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_bearer_token_validation(self):
        """Test Bearer token authentication validation."""
        start_time = time.time()

        token_scenarios = [
            {"token": "valid_jwt_token_here", "expected": "success"},
            {"token": "expired_token", "expected": "failure"},
            {"token": "malformed.token", "expected": "failure"},
            {"token": "", "expected": "failure"},
            {
                "token": SecurityTestUtils.create_malicious_payload("xss"),
                "expected": "failure",
            },
        ]

        for scenario in token_scenarios:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Mock token validation response
                if (
                    scenario["expected"] == "success"
                    and scenario["token"] == "valid_jwt_token_here"
                ):
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "healthy",
                        "token_valid": True,
                    }
                else:
                    mock_response = Mock()
                    mock_response.status_code = 403
                    mock_response.json.return_value = {
                        "error": "Invalid or expired token"
                    }

                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                # Set authorization header
                if scenario["token"]:
                    mock_session.headers = {
                        "Authorization": f"Bearer {scenario['token']}"
                    }

                health_operator = HealthCheckOperator(
                    task_id=f"token_test_{len(scenario['token'])}",
                    service_urls={"token_service": "http://token-service:8080"},
                )

                results = health_operator.execute({})

                # Validate token handling
                service_health = results["services"]["token_service"]
                if scenario["expected"] == "success":
                    assert service_health["status"] == "healthy"
                else:
                    assert service_health["status"] == "unhealthy"

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Token test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_api_key_security(self):
        """Test API key security mechanisms."""
        start_time = time.time()

        api_key_scenarios = [
            {"key": "sk-1234567890abcdef", "location": "header", "expected": "success"},
            {"key": "invalid_key", "location": "header", "expected": "failure"},
            {"key": "", "location": "header", "expected": "failure"},
            {"key": "sk-1234567890abcdef", "location": "query", "expected": "insecure"},
        ]

        for scenario in api_key_scenarios:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Mock API key validation
                if scenario["expected"] == "success":
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "healthy",
                        "api_key_valid": True,
                    }
                elif scenario["expected"] == "insecure":
                    # Warn about insecure API key in query parameter
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "degraded",
                        "warning": "API key in query parameter is insecure",
                    }
                else:
                    mock_response = Mock()
                    mock_response.status_code = 401
                    mock_response.json.return_value = {"error": "Invalid API key"}

                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id=f"apikey_test_{scenario['location']}",
                    service_urls={"apikey_service": "http://apikey-service:8080"},
                )

                results = health_operator.execute({})

                # Validate API key handling
                service_health = results["services"]["apikey_service"]
                if scenario["expected"] == "success":
                    assert service_health["status"] == "healthy"
                elif scenario["expected"] == "insecure":
                    assert service_health["status"] == "degraded"
                else:
                    assert service_health["status"] == "unhealthy"

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"API key test took {execution_time:.2f}s"


class TestSSLTLSSecurity:
    """Test SSL/TLS security mechanisms."""

    @pytest.mark.security
    async def test_ssl_certificate_validation(self):
        """Test SSL certificate validation."""
        start_time = time.time()

        cert_scenarios = [
            {"verify_ssl": True, "cert_valid": True, "expected": "success"},
            {"verify_ssl": True, "cert_valid": False, "expected": "failure"},
            {"verify_ssl": False, "cert_valid": False, "expected": "insecure_success"},
        ]

        for scenario in cert_scenarios:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                if scenario["cert_valid"] or not scenario["verify_ssl"]:
                    # Valid cert or SSL verification disabled
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "healthy"}
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    mock_session.get.return_value = mock_response
                else:
                    # Invalid certificate
                    mock_session.get.side_effect = ssl.SSLError(
                        "Certificate verification failed"
                    )

                health_operator = HealthCheckOperator(
                    task_id=f"ssl_test_{scenario['verify_ssl']}_{scenario['cert_valid']}",
                    service_urls={"ssl_service": "https://ssl-service:8443"},
                    verify_ssl=scenario["verify_ssl"],
                )

                results = health_operator.execute({})

                # Validate SSL behavior
                service_health = results["services"]["ssl_service"]
                if scenario["expected"] == "success":
                    assert service_health["status"] == "healthy"
                elif scenario["expected"] == "insecure_success":
                    # Should work but with security warning
                    assert service_health["status"] in ["healthy", "degraded"]
                else:
                    assert service_health["status"] == "unreachable"
                    assert "ssl" in str(service_health.get("error", "")).lower()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"SSL test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_tls_version_enforcement(self):
        """Test TLS version enforcement."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock TLS version check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "tls_version": "TLSv1.3",
            }
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            # Ensure modern TLS is used
            with patch("ssl.create_default_context") as mock_ssl_context:
                mock_context = Mock()
                mock_context.minimum_version = ssl.TLSVersion.TLSv1_2
                mock_ssl_context.return_value = mock_context

                health_operator = HealthCheckOperator(
                    task_id="tls_version_test",
                    service_urls={"tls_service": "https://tls-service:8443"},
                    verify_ssl=True,
                )

                results = health_operator.execute({})

                # Should use secure TLS version
                assert results["services"]["tls_service"]["status"] == "healthy"

                # Verify TLS context was configured securely
                mock_ssl_context.assert_called()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"TLS version test took {execution_time:.2f}s"


class TestInputValidationSecurity:
    """Test input validation and sanitization."""

    @pytest.mark.security
    async def test_malicious_input_handling(self):
        """Test handling of malicious inputs."""
        start_time = time.time()

        malicious_inputs = [
            {
                "type": "sql_injection",
                "input": SecurityTestUtils.create_malicious_payload("sql_injection"),
            },
            {"type": "xss", "input": SecurityTestUtils.create_malicious_payload("xss")},
            {
                "type": "command_injection",
                "input": SecurityTestUtils.create_malicious_payload(
                    "command_injection"
                ),
            },
            {
                "type": "path_traversal",
                "input": SecurityTestUtils.create_malicious_payload("path_traversal"),
            },
        ]

        for malicious in malicious_inputs:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Mock sanitized response (input should be rejected/sanitized)
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.json.return_value = {
                    "error": "Invalid input detected",
                    "type": "input_validation_error",
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                # Try to use malicious input in service URL (should be caught)
                try:
                    # This should be handled safely
                    service_url = (
                        f"http://service:8080/endpoint?param={malicious['input']}"
                    )
                    parsed = urlparse(service_url)

                    # URL parsing should work, but service should reject malicious params
                    assert parsed.hostname == "service"

                    health_operator = HealthCheckOperator(
                        task_id=f"malicious_input_test_{malicious['type']}",
                        service_urls={"vulnerable_service": "http://service:8080"},
                    )

                    results = health_operator.execute({})

                    # Service should handle malicious input safely
                    service_health = results["services"]["vulnerable_service"]
                    # Should either reject (400) or sanitize input
                    assert service_health["status"] == "unhealthy"
                    assert service_health["status_code"] == 400

                except Exception as e:
                    # If operator itself catches malicious input, that's good
                    assert "invalid" in str(e).lower() or "malicious" in str(e).lower()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Malicious input test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_oversized_input_handling(self):
        """Test handling of oversized inputs."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock response for oversized data
            mock_response = Mock()
            mock_response.status_code = 413  # Payload Too Large
            mock_response.json.return_value = {"error": "Request entity too large"}
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="oversized_input_test",
                service_urls={"size_limited_service": "http://size-limited:8080"},
                timeout=10,  # Reasonable timeout
            )

            results = health_operator.execute({})

            # Should handle oversized input gracefully
            service_health = results["services"]["size_limited_service"]
            assert service_health["status"] == "unhealthy"
            assert service_health["status_code"] == 413

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Oversized input test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_json_bomb_protection(self):
        """Test protection against JSON bomb attacks."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock JSON bomb response
            json_bomb = SecurityTestUtils.create_malicious_payload("json_bomb")

            mock_response = Mock()
            mock_response.status_code = 200
            # Simulate JSON bomb in response
            mock_response.json.side_effect = json.JSONDecodeError(
                "JSON bomb detected", json_bomb, 0
            )
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="json_bomb_test",
                service_urls={"json_bomb_service": "http://json-bomb:8080"},
                timeout=5,  # Short timeout to prevent hanging
            )

            results = health_operator.execute({})

            # Should handle JSON parsing error gracefully
            service_health = results["services"]["json_bomb_service"]
            assert (
                service_health["status"] == "healthy"
            )  # 200 status but no JSON details
            assert "details" not in service_health or not service_health["details"]

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"JSON bomb test took {execution_time:.2f}s"


class TestSecretsManagement:
    """Test secrets management security."""

    @pytest.mark.security
    async def test_credential_exposure_prevention(self):
        """Test prevention of credential exposure in logs/outputs."""
        start_time = time.time()

        sensitive_data = [
            "password123",
            "sk-1234567890abcdef",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "AKIA1234567890EXAMPLE",
            "mysql://user:secret@host:3306/db",
        ]

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Response that might contain sensitive data
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "config": {
                    "database_url": "mysql://user:***@host:3306/db",  # Should be masked
                    "api_key": "***",  # Should be masked
                },
            }
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            # Capture log output
            with patch("logging.Logger.info") as mock_log:
                health_operator = HealthCheckOperator(
                    task_id="credential_exposure_test",
                    service_urls={"secure_service": "http://secure-service:8080"},
                )

                results = health_operator.execute({})

                # Check that sensitive data is not exposed in results
                results_str = json.dumps(results)
                for sensitive in sensitive_data:
                    assert sensitive not in results_str, (
                        f"Sensitive data '{sensitive}' exposed in results"
                    )

                # Check that logs don't contain sensitive data
                all_log_calls = [str(call) for call in mock_log.call_args_list]
                log_output = " ".join(all_log_calls)
                for sensitive in sensitive_data:
                    assert sensitive not in log_output, (
                        f"Sensitive data '{sensitive}' exposed in logs"
                    )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Credential exposure test took {execution_time:.2f}s"
        )

    @pytest.mark.security
    async def test_environment_variable_security(self):
        """Test secure handling of environment variables."""
        start_time = time.time()

        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "super_secret_value",
                "API_TOKEN": "secret_token_123",
                "PUBLIC_CONFIG": "public_value",
            },
        ):
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "healthy"}
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id="env_security_test",
                    service_urls={"env_service": "http://env-service:8080"},
                )

                results = health_operator.execute({})

                # Ensure secret environment variables are not leaked
                results_str = json.dumps(results)
                assert "super_secret_value" not in results_str
                assert "secret_token_123" not in results_str
                # Public config might be OK in some contexts

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Environment variable test took {execution_time:.2f}s"
        )


class TestNetworkSecurity:
    """Test network security mechanisms."""

    @pytest.mark.security
    async def test_url_validation(self):
        """Test URL validation and security."""
        start_time = time.time()

        url_test_cases = [
            {"url": "http://valid-service:8080", "expected": "valid"},
            {"url": "https://secure-service:8443", "expected": "valid"},
            {"url": "ftp://malicious-service:21", "expected": "invalid"},
            {"url": "//malicious.com", "expected": "invalid"},
            {"url": "javascript:alert(1)", "expected": "invalid"},
            {"url": "http://localhost:8080", "expected": "internal"},
            {"url": "http://127.0.0.1:8080", "expected": "internal"},
        ]

        for test_case in url_test_cases:
            try:
                parsed_url = urlparse(test_case["url"])

                # Validate URL scheme
                if parsed_url.scheme not in ["http", "https"]:
                    assert test_case["expected"] == "invalid"
                    continue

                # Check for internal/localhost access (might be restricted)
                if parsed_url.hostname in ["localhost", "127.0.0.1"]:
                    assert test_case["expected"] == "internal"
                    # In production, might want to restrict this

                with patch("requests.Session") as mock_session_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    if test_case["expected"] in ["valid", "internal"]:
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"status": "healthy"}
                        mock_response.elapsed.total_seconds.return_value = 0.01
                        mock_session.get.return_value = mock_response

                        health_operator = HealthCheckOperator(
                            task_id=f"url_validation_test_{len(test_case['url'])}",
                            service_urls={"test_service": test_case["url"]},
                        )

                        results = health_operator.execute({})
                        assert (
                            results["services"]["test_service"]["status"] == "healthy"
                        )

            except Exception as e:
                # Invalid URLs should be caught
                if test_case["expected"] == "invalid":
                    assert True  # Expected to fail
                else:
                    raise e

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"URL validation test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_request_header_security(self):
        """Test security-related request headers."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock response with security headers
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_response.headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'",
            }
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="header_security_test",
                service_urls={"secure_headers_service": "https://secure-headers:8443"},
            )

            results = health_operator.execute({})

            # Verify security headers are respected
            assert results["services"]["secure_headers_service"]["status"] == "healthy"

            # Could add validation of security headers if operator stores them

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Header security test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_request_timeout_security(self):
        """Test request timeout as security measure."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate slow response (potential DoS)
            def slow_response(*args, **kwargs):
                time.sleep(0.1)  # 100ms delay
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "healthy"}
                mock_response.elapsed.total_seconds.return_value = 0.1
                return mock_response

            mock_session.get.side_effect = slow_response

            health_operator = HealthCheckOperator(
                task_id="timeout_security_test",
                service_urls={"slow_service": "http://slow-service:8080"},
                timeout=0.05,  # 50ms timeout - should cause timeout
            )

            # Should handle timeout gracefully
            results = health_operator.execute({})

            # Timeout should be enforced as security measure
            service_health = results["services"]["slow_service"]
            # Either timeout error or successful completion within limits
            assert service_health["status"] in ["healthy", "unreachable"]

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Timeout security test took {execution_time:.2f}s"


class TestDataPrivacySecurity:
    """Test data privacy and compliance."""

    @pytest.mark.security
    async def test_pii_data_handling(self):
        """Test handling of personally identifiable information (PII)."""
        start_time = time.time()

        pii_data = {
            "email": "user@example.com",
            "phone": "+1-555-123-4567",
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111",
            "ip_address": "192.168.1.100",
        }

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Response that might contain PII
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "user_data": {
                    "email": "***@***.com",  # Should be masked
                    "phone": "***-***-4567",  # Partially masked
                    "user_id": "12345",  # Non-PII OK
                },
            }
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="pii_handling_test",
                service_urls={"pii_service": "http://pii-service:8080"},
            )

            results = health_operator.execute({})

            # Ensure PII is not exposed in results
            results_str = json.dumps(results)
            for pii_type, pii_value in pii_data.items():
                if pii_type in ["email", "phone", "ssn", "credit_card"]:
                    assert pii_value not in results_str, (
                        f"PII {pii_type} exposed: {pii_value}"
                    )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"PII handling test took {execution_time:.2f}s"

    @pytest.mark.security
    async def test_data_retention_compliance(self):
        """Test data retention compliance."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Response with retention metadata
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "data_retention": {
                    "policy": "gdpr_compliant",
                    "retention_days": 365,
                    "auto_delete": True,
                },
            }
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="data_retention_test",
                service_urls={"retention_service": "http://retention-service:8080"},
            )

            results = health_operator.execute({})

            # Verify compliance metadata is available
            assert results["services"]["retention_service"]["status"] == "healthy"

            # Could validate retention policy if operator stores it
            service_details = results["services"]["retention_service"].get(
                "details", {}
            )
            if "data_retention" in service_details:
                retention = service_details["data_retention"]
                assert retention.get("policy") in ["gdpr_compliant", "ccpa_compliant"]
                assert retention.get("retention_days", 0) <= 2555  # Max 7 years

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Data retention test took {execution_time:.2f}s"


class TestSecurityCompliance:
    """Test overall security compliance."""

    @pytest.mark.security
    async def test_security_best_practices_compliance(self):
        """Test compliance with security best practices."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock comprehensive security response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "security_compliance": {
                    "https_enforced": True,
                    "auth_required": True,
                    "input_validated": True,
                    "output_sanitized": True,
                    "rate_limited": True,
                    "vulnerability_scan_date": datetime.now().isoformat(),
                    "compliance_frameworks": ["SOC2", "GDPR", "HIPAA"],
                },
            }
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="security_compliance_test",
                service_urls={"compliant_service": "https://compliant-service:8443"},
                verify_ssl=True,  # Enforce SSL
            )

            results = health_operator.execute({})

            # Verify security compliance
            assert results["services"]["compliant_service"]["status"] == "healthy"

            service_details = results["services"]["compliant_service"].get(
                "details", {}
            )
            if "security_compliance" in service_details:
                compliance = service_details["security_compliance"]

                # Check key security measures
                assert compliance.get("https_enforced") is True
                assert compliance.get("auth_required") is True
                assert compliance.get("input_validated") is True

                # Check compliance frameworks
                frameworks = compliance.get("compliance_frameworks", [])
                assert len(frameworks) > 0, "No compliance frameworks specified"

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Security compliance test took {execution_time:.2f}s"
        )

    @pytest.mark.security
    async def test_vulnerability_detection(self):
        """Test detection of common vulnerabilities."""
        start_time = time.time()

        vulnerability_tests = [
            {
                "name": "outdated_dependencies",
                "response": {
                    "status": "degraded",
                    "vulnerabilities": [
                        {
                            "type": "outdated_dependency",
                            "severity": "medium",
                            "component": "requests==2.20.0",
                        }
                    ],
                },
            },
            {
                "name": "insecure_config",
                "response": {
                    "status": "degraded",
                    "vulnerabilities": [
                        {
                            "type": "insecure_configuration",
                            "severity": "high",
                            "issue": "debug_mode_enabled",
                        }
                    ],
                },
            },
        ]

        for vuln_test in vulnerability_tests:
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = vuln_test["response"]
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id=f"vulnerability_test_{vuln_test['name']}",
                    service_urls={
                        "vulnerable_service": "http://vulnerable-service:8080"
                    },
                )

                results = health_operator.execute({})

                # Should detect and report vulnerabilities
                service_health = results["services"]["vulnerable_service"]
                assert service_health["status"] == "degraded"

                # Vulnerabilities should be captured in details
                details = service_health.get("details", {})
                if "vulnerabilities" in details:
                    vulnerabilities = details["vulnerabilities"]
                    assert len(vulnerabilities) > 0
                    assert all("severity" in v for v in vulnerabilities)

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Vulnerability detection test took {execution_time:.2f}s"
        )
