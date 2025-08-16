"""
UTM Parameter Processing and Analytics Tracking

This module implements UTM parameter extraction, validation, and storage
for conversion tracking and analytics.

Following TDD principles - implementing minimal functionality to make tests pass.
"""

from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs


class UTMValidationError(Exception):
    """Raised when UTM parameters fail validation"""

    pass


class UTMParameterProcessor:
    """
    Processes UTM parameters for conversion tracking and analytics.

    Supports extraction, validation, and storage of UTM parameters
    to track content attribution and measure conversion effectiveness.
    """

    def __init__(self):
        # Define allowed UTM sources based on existing auto_content_pipeline.py
        self.allowed_sources = {
            "linkedin",
            "devto",
            "medium",
            "twitter",
            "threads",
            "github",
            "google",
            "direct",
            "email",
            "organic",
        }

        # Required UTM parameters
        self.required_params = {"utm_source", "utm_campaign"}

        # In-memory storage for TDD - will replace with database later
        self.analytics_store = {}

    def extract_utm_parameters(self, url: str) -> Dict[str, str]:
        """
        Extract UTM parameters from URL.

        Args:
            url: URL containing UTM parameters

        Returns:
            Dictionary of UTM parameters found in URL
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        utm_params = {}
        utm_keys = [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
        ]

        for key in utm_keys:
            if key in query_params:
                # parse_qs returns lists, we want the first value
                utm_params[key] = query_params[key][0]

        return utm_params

    def validate_utm_parameters(self, utm_params: Dict[str, str]) -> bool:
        """
        Validate UTM parameters according to business rules.

        Args:
            utm_params: Dictionary of UTM parameters to validate

        Returns:
            True if valid

        Raises:
            UTMValidationError: If validation fails
        """
        # Check required parameters
        for required_param in self.required_params:
            if required_param not in utm_params:
                raise UTMValidationError(f"{required_param} is required")

        # Validate utm_source against allowed values
        utm_source = utm_params.get("utm_source")
        if utm_source and utm_source not in self.allowed_sources:
            raise UTMValidationError(
                f"Invalid utm_source: {utm_source}. Allowed: {self.allowed_sources}"
            )

        return True

    def store_utm_analytics(
        self, utm_params: Dict[str, str], visitor_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store UTM parameters and visitor information for analytics.

        Args:
            utm_params: UTM parameters extracted from URL
            visitor_info: Visitor information (IP, user agent, timestamp, etc.)

        Returns:
            Dictionary with storage result and tracking ID
        """
        # Generate tracking ID
        tracking_id = f"utm_{len(self.analytics_store) + 1:06d}"

        # Store analytics record
        self.analytics_store[tracking_id] = {
            "tracking_id": tracking_id,
            "utm_params": utm_params,
            "visitor_info": visitor_info,
            "platform": utm_params.get("utm_source", "unknown"),
            "campaign": utm_params.get("utm_campaign", "unknown"),
            "stored_at": visitor_info.get("timestamp"),
        }

        return {
            "success": True,
            "tracking_id": tracking_id,
            "platform": utm_params.get("utm_source", "unknown"),
            "campaign": utm_params.get("utm_campaign", "unknown"),
        }

    def get_analytics_record(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """Get stored analytics record by tracking ID"""
        return self.analytics_store.get(tracking_id)

    def get_platform_analytics(self, platform: str) -> List[Dict[str, Any]]:
        """Get all analytics records for a specific platform"""
        return [
            record
            for record in self.analytics_store.values()
            if record.get("platform") == platform
        ]
