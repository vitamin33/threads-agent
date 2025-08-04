# Webhook Routes for Automated Tracking

import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from services.achievement_collector.api.schemas import WebhookResponse
from services.achievement_collector.core.config import settings
from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import get_db
from services.achievement_collector.services.github_processor import GitHubProcessor
from services.achievement_collector.services.pr_value_analyzer_integration import (
    pr_value_integration,
)

logger = setup_logging(__name__)
router = APIRouter()

# Initialize processor
processor = GitHubProcessor()


def verify_github_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify GitHub webhook signature"""

    if not signature:
        return False

    # GitHub sends sha256=<signature>
    if not signature.startswith("sha256="):
        return False

    expected_signature = (
        "sha256="
        + hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(expected_signature, signature)


@router.post("/github", response_model=WebhookResponse)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db),
):
    """Handle GitHub webhook events"""

    # Get raw payload
    payload = await request.body()

    # Verify signature if secret is configured
    if settings.GITHUB_WEBHOOK_SECRET:
        if not verify_github_signature(
            payload,
            x_hub_signature_256,
            settings.GITHUB_WEBHOOK_SECRET,
        ):
            logger.warning("Invalid GitHub webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Log event
    logger.info(f"Received GitHub webhook: {x_github_event}")

    # Process based on event type
    achievement_created = False
    achievement_id = None

    try:
        if x_github_event == "pull_request":
            # Handle PR events
            if data.get("action") in ["closed", "merged"]:
                result = await processor.process_pull_request(data, db)
                if result:
                    achievement_created = True
                    achievement_id = result.id

                    # Run value analysis for merged PRs
                    if data.get("pull_request", {}).get("merged"):
                        pr_number = data["pull_request"]["number"]
                        try:
                            enriched = await pr_value_integration.analyze_and_create_achievement(
                                str(pr_number)
                            )
                            if enriched:
                                logger.info(
                                    f"Enriched PR #{pr_number} with value analysis"
                                )
                        except Exception as e:
                            logger.error(f"Failed to enrich PR #{pr_number}: {e}")

        elif x_github_event == "workflow_run":
            # Handle CI/CD events
            if data.get("action") == "completed":
                result = await processor.process_workflow_run(data, db)
                if result:
                    achievement_created = True
                    achievement_id = result.id

        elif x_github_event == "push":
            # Handle push events
            result = await processor.process_push(data, db)
            if result:
                achievement_created = True
                achievement_id = result.id

        elif x_github_event == "issues":
            # Handle issue events
            if data.get("action") in ["closed"]:
                result = await processor.process_issue(data, db)
                if result:
                    achievement_created = True
                    achievement_id = result.id

        else:
            logger.info(f"Unhandled event type: {x_github_event}")

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )

    return WebhookResponse(
        status="processed",
        message=f"Processed {x_github_event} event",
        achievement_created=achievement_created,
        achievement_id=achievement_id,
    )


@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(None),
    x_gitlab_token: str = Header(None),
    db: Session = Depends(get_db),
):
    """Handle GitLab webhook events (placeholder)"""

    # TODO: Implement GitLab webhook processing

    return WebhookResponse(
        status="not_implemented",
        message="GitLab webhooks not yet implemented",
        achievement_created=False,
    )


@router.post("/ci/{provider}")
async def ci_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle CI/CD provider webhooks"""

    supported_providers = ["jenkins", "circleci", "travis", "gitlab-ci"]

    if provider not in supported_providers:
        raise HTTPException(
            status_code=400, detail=f"Unsupported CI provider: {provider}"
        )

    # TODO: Implement CI provider webhook processing

    return WebhookResponse(
        status="not_implemented",
        message=f"{provider} webhooks not yet implemented",
        achievement_created=False,
    )


@router.get("/health")
async def webhook_health():
    """Check webhook endpoint health"""

    return {
        "status": "healthy",
        "github_configured": bool(settings.GITHUB_WEBHOOK_SECRET),
        "supported_events": [
            "pull_request",
            "workflow_run",
            "push",
            "issues",
        ],
    }
