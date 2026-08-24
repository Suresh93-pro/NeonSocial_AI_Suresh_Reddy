# ============================================================
# NEONSOCIAL AI
# LINKEDIN PUBLISHER
# ============================================================

import os
import requests


LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"

# LinkedIn requires a YYYYMM API version.
# Keep this configurable through .env so it can be updated
# without changing Python code.
LINKEDIN_VERSION = os.getenv(
    "LINKEDIN_VERSION",
    "202604"
)


class LinkedInPublishError(Exception):
    """Raised when LinkedIn publishing fails."""


def _headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": LINKEDIN_VERSION,
    }


def publish_text_post(
    access_token,
    author_urn,
    content
):
    """
    Publish a text-only LinkedIn post.

    Example author:
        urn:li:person:123456

    Returns:
        {
            "success": True,
            "post_id": "...",
            "status_code": 201
        }
    """

    if not access_token:
        raise LinkedInPublishError(
            "LinkedIn access token is missing."
        )

    if not author_urn:
        raise LinkedInPublishError(
            "LinkedIn author URN is missing."
        )

    if not content:
        raise LinkedInPublishError(
            "Post content is empty."
        )

    payload = {
        "author": author_urn,

        "commentary": content,

        "visibility": "PUBLIC",

        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },

        "lifecycleState": "PUBLISHED",

        "isReshareDisabledByAuthor": False
    }

    try:

        response = requests.post(
            LINKEDIN_POSTS_URL,
            headers=_headers(
                access_token
            ),
            json=payload,
            timeout=20
        )

    except requests.RequestException as error:

        raise LinkedInPublishError(
            f"LinkedIn network error: {error}"
        ) from error

    if response.status_code not in (200, 201):

        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        raise LinkedInPublishError(
            f"LinkedIn API returned "
            f"{response.status_code}: "
            f"{error_data}"
        )

    post_id = (
        response.headers.get(
            "x-restli-id"
        )
        or response.headers.get(
            "X-RestLi-Id"
        )
    )

    return {
        "success": True,
        "post_id": post_id,
        "status_code": response.status_code
    }