
import os
import secrets
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# LINKEDIN ENDPOINTS
# ============================================================

LINKEDIN_AUTH_URL = (
    "https://www.linkedin.com/oauth/v2/authorization"
)

LINKEDIN_TOKEN_URL = (
    "https://www.linkedin.com/oauth/v2/accessToken"
)

LINKEDIN_USERINFO_URL = (
    "https://api.linkedin.com/v2/userinfo"
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_REDIRECT_URI = (
    "http://127.0.0.1:5000/oauth/linkedin/callback"
)


def get_client_id():
    """Return LinkedIn Client ID."""

    client_id = os.getenv(
        "LINKEDIN_CLIENT_ID"
    )

    if not client_id:
        raise RuntimeError(
            "LINKEDIN_CLIENT_ID is missing from .env"
        )

    return client_id


def get_client_secret():
    """Return LinkedIn Client Secret."""

    client_secret = os.getenv(
        "LINKEDIN_CLIENT_SECRET"
    )

    if not client_secret:
        raise RuntimeError(
            "LINKEDIN_CLIENT_SECRET is missing from .env"
        )

    return client_secret


def get_redirect_uri():
    """Return LinkedIn OAuth redirect URI."""

    return os.getenv(
        "LINKEDIN_REDIRECT_URI",
        DEFAULT_REDIRECT_URI
    )


# ============================================================
# OAUTH STATE
# ============================================================

def create_state():
    """
    Create a secure random OAuth state value.
    """

    return secrets.token_urlsafe(32)


# ============================================================
# BUILD LINKEDIN AUTHORIZATION URL
# ============================================================

def build_authorization_url(state):
    """
    Build the LinkedIn OAuth authorization URL.
    """

    if not state:
        raise ValueError(
            "OAuth state is required."
        )

    client_id = get_client_id()

    redirect_uri = get_redirect_uri()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": (
            "openid "
            "profile "
            "email "
            "w_member_social"
        ),
    }

    return (
        LINKEDIN_AUTH_URL
        + "?"
        + urlencode(params)
    )


# ============================================================
# EXCHANGE AUTHORIZATION CODE FOR TOKEN
# ============================================================

def exchange_code_for_token(code):
    """
    Exchange LinkedIn authorization code
    for an access token.
    """

    if not code:
        raise ValueError(
            "LinkedIn authorization code is missing."
        )

    client_id = get_client_id()

    client_secret = get_client_secret()

    redirect_uri = get_redirect_uri()

    response = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )

    if not response.ok:

        try:
            error_data = response.json()

        except ValueError:
            error_data = response.text

        raise RuntimeError(
            "LinkedIn token request failed: "
            f"{error_data}"
        )

    data = response.json()

    access_token = data.get(
        "access_token"
    )

    if not access_token:
        raise RuntimeError(
            "LinkedIn did not return an access token."
        )

    return data


# ============================================================
# GET LINKEDIN USER INFORMATION
# ============================================================

def get_linkedin_userinfo(access_token):
    """
    Get the authenticated LinkedIn member's
    OpenID Connect user information.
    """

    if not access_token:
        raise ValueError(
            "LinkedIn access token is missing."
        )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
    }

    response = requests.get(
        LINKEDIN_USERINFO_URL,
        headers=headers,
        timeout=30,
    )

    if not response.ok:

        try:
            error_data = response.json()

        except ValueError:
            error_data = response.text

        raise RuntimeError(
            "LinkedIn user information request failed: "
            f"{error_data}"
        )

    data = response.json()

    return data


# ============================================================
# TEST CONFIGURATION
# ============================================================

def check_configuration():
    """
    Check whether LinkedIn credentials exist.
    Does not expose the secret.
    """

    client_id = os.getenv(
        "LINKEDIN_CLIENT_ID"
    )

    client_secret = os.getenv(
        "LINKEDIN_CLIENT_SECRET"
    )

    redirect_uri = get_redirect_uri()

    return {
        "client_id_configured": bool(
            client_id
        ),
        "client_secret_configured": bool(
            client_secret
        ),
        "redirect_uri": redirect_uri,
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    configuration = check_configuration()

    print()
    print("=" * 60)
    print(" NEONSOCIAL - LINKEDIN OAUTH")
    print("=" * 60)
    print()

    print(
        "Client ID configured :",
        configuration[
            "client_id_configured"
        ],
    )

    print(
        "Client Secret configured :",
        configuration[
            "client_secret_configured"
        ],
    )

    print(
        "Redirect URI :",
        configuration[
            "redirect_uri"
        ],
    )

    print()
    print("=" * 60)

