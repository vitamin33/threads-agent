"""
Viral Scraper Operator for Airflow (CRA-284)

Custom operator for interacting with the Viral Content Scraper Service.
Handles rate limiting, retry logic, and batch scraping operations.

Epic: E7 - Viral Learning Flywheel
"""

import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter, Retry

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import (
    AirflowException,
)
from airflow.utils.context import Context


class ViralScraperOperator(BaseOperator):
    """
    Custom Airflow operator for viral content scraping operations.

    This operator provides:
    - Rate-limited scraping with automatic retry handling
    - Batch processing for multiple accounts
    - Performance monitoring and metrics collection
    - Integration with viral pattern extraction pipeline

    Args:
        viral_scraper_url: Base URL for the viral scraper service
        account_ids: List of account IDs to scrape, or single account ID string
        max_posts_per_account: Maximum posts to scrape per account (default: 50)
        days_back: Number of days to look back for content (default: 7)
        min_performance_percentile: Minimum performance percentile filter (default: 95.0)
        rate_limit_retry_delay: Delay between rate limit retries in seconds (default: 60)
        max_rate_limit_retries: Maximum number of rate limit retries (default: 5)
        batch_size: Number of accounts to process in parallel (default: 3)
        timeout: Request timeout in seconds (default: 300)

    Example:
        ```python
        scrape_viral_accounts = ViralScraperOperator(
            task_id='scrape_viral_accounts',
            viral_scraper_url='http://viral-scraper:8080',
            account_ids=['viral_account_1', 'viral_account_2'],
            max_posts_per_account=100,
            days_back=14,
            min_performance_percentile=99.0,
            dag=dag
        )
        ```
    """

    template_fields = [
        "account_ids",
        "max_posts_per_account",
        "days_back",
        "min_performance_percentile",
        "viral_scraper_url",
    ]

    ui_color = "#e8f4fd"
    ui_fgcolor = "#1e5a96"

    @apply_defaults
    def __init__(
        self,
        viral_scraper_url: str,
        account_ids: Union[str, List[str]],
        max_posts_per_account: int = 50,
        days_back: int = 7,
        min_performance_percentile: float = 95.0,
        rate_limit_retry_delay: int = 60,
        max_rate_limit_retries: int = 5,
        batch_size: int = 3,
        timeout: int = 300,
        verify_ssl: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.viral_scraper_url = viral_scraper_url.rstrip("/")
        self.account_ids = (
            account_ids if isinstance(account_ids, list) else [account_ids]
        )
        self.max_posts_per_account = max_posts_per_account
        self.days_back = days_back
        self.min_performance_percentile = min_performance_percentile
        self.rate_limit_retry_delay = rate_limit_retry_delay
        self.max_rate_limit_retries = max_rate_limit_retries
        self.batch_size = batch_size
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Configure HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def execute(self, context: Context) -> Dict[str, Any]:
        """
        Execute viral content scraping for configured accounts.

        Returns:
            Dict containing scraping results and metrics
        """
        self.log.info(
            f"Starting viral content scraping for {len(self.account_ids)} accounts"
        )

        # Perform health check
        if not self._health_check():
            raise AirflowException("Viral Scraper service is not healthy")

        # Process accounts in batches
        results = {
            "total_accounts": len(self.account_ids),
            "successful_accounts": [],
            "failed_accounts": [],
            "rate_limited_accounts": [],
            "total_posts_scraped": 0,
            "execution_start": datetime.now().isoformat(),
            "batch_results": [],
        }

        for i in range(0, len(self.account_ids), self.batch_size):
            batch = self.account_ids[i : i + self.batch_size]
            batch_result = self._process_batch(batch, context)
            results["batch_results"].append(batch_result)

            # Aggregate results
            results["successful_accounts"].extend(batch_result["successful"])
            results["failed_accounts"].extend(batch_result["failed"])
            results["rate_limited_accounts"].extend(batch_result["rate_limited"])
            results["total_posts_scraped"] += batch_result["total_posts"]

        results["execution_end"] = datetime.now().isoformat()
        results["success_rate"] = len(results["successful_accounts"]) / len(
            self.account_ids
        )

        self.log.info(f"Scraping completed: {results['success_rate']:.1%} success rate")

        # Fail task if success rate is too low
        if results["success_rate"] < 0.5:
            raise AirflowException(
                f"Scraping success rate too low: {results['success_rate']:.1%}"
            )

        return results

    def _health_check(self) -> bool:
        """Perform health check on viral scraper service."""
        try:
            response = self.session.get(
                f"{self.viral_scraper_url}/health", timeout=10, verify=self.verify_ssl
            )
            return response.status_code == 200
        except Exception as e:
            self.log.error(f"Health check failed: {e}")
            return False

    def _process_batch(
        self, account_batch: List[str], context: Context
    ) -> Dict[str, Any]:
        """Process a batch of accounts for scraping."""
        batch_result = {
            "accounts": account_batch,
            "successful": [],
            "failed": [],
            "rate_limited": [],
            "total_posts": 0,
            "start_time": datetime.now().isoformat(),
        }

        for account_id in account_batch:
            try:
                account_result = self._scrape_account(account_id, context)

                if account_result["status"] == "success":
                    batch_result["successful"].append(account_id)
                    batch_result["total_posts"] += account_result.get(
                        "posts_scraped", 0
                    )
                elif account_result["status"] == "rate_limited":
                    batch_result["rate_limited"].append(account_id)
                else:
                    batch_result["failed"].append(account_id)

            except Exception as e:
                self.log.error(f"Failed to scrape account {account_id}: {e}")
                batch_result["failed"].append(account_id)

        batch_result["end_time"] = datetime.now().isoformat()
        return batch_result

    def _scrape_account(self, account_id: str, context: Context) -> Dict[str, Any]:
        """Scrape content for a single account with rate limit handling."""
        self.log.info(f"Starting scraping for account: {account_id}")

        # Check current rate limit status
        rate_status = self._check_rate_limit_status(account_id)
        if rate_status and rate_status.get("requests_remaining", 1) == 0:
            self.log.warning(f"Account {account_id} is rate limited, waiting...")
            self._handle_rate_limit(account_id, rate_status)

        # Prepare scraping request
        scrape_payload = {
            "max_posts": self.max_posts_per_account,
            "days_back": self.days_back,
            "min_performance_percentile": self.min_performance_percentile,
        }

        # Attempt scraping with rate limit retry logic
        for attempt in range(self.max_rate_limit_retries + 1):
            try:
                response = self.session.post(
                    f"{self.viral_scraper_url}/scrape/account/{account_id}",
                    json=scrape_payload,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result = response.json()
                    self.log.info(
                        f"Successfully queued scraping for {account_id}: {result.get('task_id')}"
                    )

                    # Wait for completion and get results
                    return self._wait_for_completion(account_id, result.get("task_id"))

                elif response.status_code == 429:
                    # Rate limited - handle retry
                    rate_limit_info = response.json().get("detail", {})
                    retry_after = rate_limit_info.get(
                        "retry_after", self.rate_limit_retry_delay
                    )

                    if attempt < self.max_rate_limit_retries:
                        self.log.warning(
                            f"Rate limited for {account_id}, retrying in {retry_after}s (attempt {attempt + 1})"
                        )
                        time.sleep(retry_after)
                        continue
                    else:
                        self.log.error(
                            f"Max rate limit retries exceeded for {account_id}"
                        )
                        return {
                            "status": "rate_limited",
                            "account_id": account_id,
                            "retry_after": retry_after,
                        }

                else:
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                if attempt < self.max_rate_limit_retries:
                    self.log.warning(f"Request failed for {account_id}, retrying: {e}")
                    time.sleep(5)
                    continue
                else:
                    raise AirflowException(
                        f"Failed to scrape {account_id} after {attempt + 1} attempts: {e}"
                    )

        return {
            "status": "failed",
            "account_id": account_id,
            "error": "Max retries exceeded",
        }

    def _check_rate_limit_status(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Check the current rate limit status for an account."""
        try:
            response = self.session.get(
                f"{self.viral_scraper_url}/rate-limit/status/{account_id}",
                timeout=10,
                verify=self.verify_ssl,
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.log.warning(f"Failed to check rate limit status for {account_id}: {e}")
        return None

    def _handle_rate_limit(self, account_id: str, rate_status: Dict[str, Any]) -> None:
        """Handle rate limiting by waiting for reset."""
        reset_time_str = rate_status.get("reset_time")
        if reset_time_str:
            try:
                reset_time = datetime.fromisoformat(
                    reset_time_str.replace("Z", "+00:00")
                )
                wait_seconds = (reset_time - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    self.log.info(
                        f"Waiting {wait_seconds:.0f}s for rate limit reset for {account_id}"
                    )
                    time.sleep(min(wait_seconds, 300))  # Cap wait time at 5 minutes
            except Exception as e:
                self.log.warning(
                    f"Failed to parse reset time, using default delay: {e}"
                )
                time.sleep(self.rate_limit_retry_delay)

    def _wait_for_completion(self, account_id: str, task_id: str) -> Dict[str, Any]:
        """Wait for scraping task completion and return results."""
        max_wait_time = 1800  # 30 minutes
        check_interval = 30  # 30 seconds
        start_time = time.time()

        self.log.info(
            f"Waiting for scraping completion: {account_id} (task: {task_id})"
        )

        while time.time() - start_time < max_wait_time:
            try:
                # Check task status (this would need to be implemented in viral scraper service)
                response = self.session.get(
                    f"{self.viral_scraper_url}/task/status/{task_id}",
                    timeout=10,
                    verify=self.verify_ssl,
                )

                if response.status_code == 200:
                    task_status = response.json()

                    if task_status.get("status") == "completed":
                        self.log.info(f"Scraping completed for {account_id}")
                        return {
                            "status": "success",
                            "account_id": account_id,
                            "task_id": task_id,
                            "posts_scraped": task_status.get("posts_scraped", 0),
                            "completion_time": datetime.now().isoformat(),
                        }
                    elif task_status.get("status") == "failed":
                        return {
                            "status": "failed",
                            "account_id": account_id,
                            "task_id": task_id,
                            "error": task_status.get("error", "Unknown error"),
                        }

                # Still processing, wait and check again
                time.sleep(check_interval)

            except Exception as e:
                self.log.warning(f"Failed to check task status for {task_id}: {e}")
                time.sleep(check_interval)

        # Timeout reached
        self.log.error(f"Scraping timeout for {account_id} (task: {task_id})")
        return {
            "status": "timeout",
            "account_id": account_id,
            "task_id": task_id,
            "error": "Scraping timeout exceeded",
        }

    def on_kill(self) -> None:
        """Clean up resources when task is killed."""
        if hasattr(self, "session"):
            self.session.close()
        self.log.info("ViralScraperOperator killed, cleaned up resources")
