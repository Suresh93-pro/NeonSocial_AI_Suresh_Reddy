
# ============================================================
# NEONSOCIAL AI
# backend/routes.py
# API + LinkedIn OAuth
# ============================================================

from flask import (
    Blueprint,
    request,
    current_app,
    jsonify,
    redirect,
)

from .agent import SocialAgent

from datetime import datetime, timezone

import os
import secrets

from .linkedin_oauth import (
    build_authorization_url,
    exchange_code_for_token,
)


# ============================================================
# BLUEPRINT
# ============================================================

api = Blueprint(
    "api",
    __name__
)


# ============================================================
# AI AGENT
# ============================================================

agent = SocialAgent()


# ============================================================
# HELPERS
# ============================================================

def db():

    return current_app.extensions["db"]


def bad(message):

    return jsonify(
        ok=False,
        error=message
    ), 400


# ============================================================
# LINKEDIN OAUTH STATE
# ============================================================

linkedin_states = set()


# ============================================================
# DASHBOARD
# ============================================================

@api.get("/dashboard")
def dashboard():

    return jsonify(
        ok=True,
        stats=db().stats(),
        posts=db().posts(),
        activities=db().activities(),
        connections=db().connections()
    )


# ============================================================
# GENERATE
# ============================================================

@api.post("/generate")
def generate():

    data = request.get_json(
        silent=True
    ) or {}

    idea = str(
        data.get(
            "idea",
            ""
        )
    ).strip()

    platform = str(
        data.get(
            "platform",
            "linkedin"
        )
    ).strip()

    tone = str(
        data.get(
            "tone",
            "professional"
        )
    ).strip()

    audience = str(
        data.get(
            "audience",
            "technology professionals"
        )
    ).strip()


    if not idea:

        return bad(
            "Enter a content idea."
        )


    try:

        result = agent.run(
            idea,
            platform,
            tone,
            audience
        )

    except Exception as error:

        current_app.logger.exception(
            "AI generation failed"
        )

        return jsonify(
            ok=False,
            error=str(error)
        ), 500


    post_id = db().create(
        platform,
        result.get(
            "title",
            "NeonSocial AI Post"
        ),
        result.get(
            "content",
            ""
        )
    )


    db().activity(
        "generate",
        f"Draft #{post_id} created. "
        "Waiting for human approval."
    )


    return jsonify(
        ok=True,
        post=db().get(post_id),
        critique=result.get(
            "critique",
            ""
        )
    )


# ============================================================
# APPROVE
# ============================================================

@api.post("/posts/<int:i>/approve")
def approve(i):

    post = db().get(i)


    if not post:

        return bad(
            "Post not found."
        )


    if post["status"] != "pending_approval":

        return bad(
            "Post is not waiting for approval."
        )


    db().update(
        i,
        status="approved"
    )


    db().activity(
        "approval",
        f"Human approved post #{i}.",
        "success"
    )


    return jsonify(
        ok=True,
        post=db().get(i)
    )


# ============================================================
# REJECT
# ============================================================

@api.post("/posts/<int:i>/reject")
def reject(i):

    post = db().get(i)


    if not post:

        return bad(
            "Post not found."
        )


    db().update(
        i,
        status="rejected"
    )


    db().activity(
        "reject",
        f"Post #{i} rejected.",
        "warning"
    )


    return jsonify(
        ok=True,
        post=db().get(i)
    )


# ============================================================
# SCHEDULE
# ============================================================

@api.post("/posts/<int:i>/schedule")
def schedule(i):

    post = db().get(i)

    data = request.get_json(
        silent=True
    ) or {}


    if not post:

        return bad(
            "Post not found."
        )


    if post["status"] != "approved":

        return bad(
            "Human approval is required first."
        )


    scheduled_at = str(
        data.get(
            "scheduled_at",
            ""
        )
    ).strip()


    if not scheduled_at:

        return bad(
            "Schedule time required."
        )


    db().update(
        i,
        status="scheduled",
        scheduled_at=scheduled_at
    )


    db().activity(
        "schedule",
        f"Post #{i} scheduled.",
        "success"
    )


    return jsonify(
        ok=True,
        post=db().get(i)
    )


# ============================================================
# MANUAL PUBLISH
# ============================================================

@api.post("/posts/<int:i>/publish")
def publish(i):

    post = db().get(i)


    if not post:

        return bad(
            "Post not found."
        )


    if post["status"] != "approved":

        return bad(
            "Publishing is blocked until "
            "human approval."
        )


    # --------------------------------------------------------
    # DEMO MODE
    # --------------------------------------------------------

    if os.getenv(
        "DEMO_MODE",
        "true"
    ).lower() == "true":

        db().update(
            i,
            status="published",
            published_at=datetime.now(
                timezone.utc
            ).isoformat()
        )


        db().activity(
            "publish",
            f"Demo published post #{i}.",
            "success"
        )


        return jsonify(
            ok=True,
            post=db().get(i)
        )


    # --------------------------------------------------------
    # LIVE PROVIDER
    # --------------------------------------------------------

    return bad(
        "Configure a live LinkedIn provider "
        "before publishing."
    )


# ============================================================
# DEMO CONNECTION
# ============================================================

@api.post("/connections/<platform>/demo")
def demo(platform):

    platform = platform.lower().strip()

    db().connect(
        platform
    )


    db().activity(
        "connect",
        f"Connected demo {platform} account.",
        "success"
    )


    return jsonify(
        ok=True
    )


# ============================================================
# LINKEDIN CONNECT
# ============================================================

@api.get("/linkedin/connect")
def linkedin_connect():

    client_id = os.getenv(
        "LINKEDIN_CLIENT_ID"
    )


    if not client_id:

        return jsonify(
            success=False,
            error=(
                "LINKEDIN_CLIENT_ID is not "
                "configured in .env"
            )
        ), 500


    state = secrets.token_urlsafe(
        32
    )


    linkedin_states.add(
        state
    )


    try:

        authorization_url = (
            build_authorization_url(
                state
            )
        )

    except Exception as error:

        current_app.logger.exception(
            "Could not create LinkedIn OAuth URL"
        )

        return jsonify(
            success=False,
            error=str(error)
        ), 500


    return jsonify(
        success=True,
        redirect=authorization_url
    )


# ============================================================
# LINKEDIN CALLBACK
# ============================================================

@api.get("/oauth/linkedin/callback")
def linkedin_callback():

    error = request.args.get(
        "error"
    )


    if error:

        description = request.args.get(
            "error_description",
            "LinkedIn authorization failed."
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Connection Failed</title>
            <style>
                body {{
                    background:#050816;
                    color:white;
                    font-family:Arial,sans-serif;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    min-height:100vh;
                }}

                .card {{
                    padding:40px;
                    border:1px solid #24304d;
                    border-radius:20px;
                    background:#0b1020;
                    text-align:center;
                }}

                h1 {{
                    color:#ff4d7d;
                }}
            </style>
        </head>

        <body>

            <div class="card">

                <h1>
                    LinkedIn Connection Failed
                </h1>

                <p>
                    {description}
                </p>

            </div>

        </body>
        </html>
        """, 400


    code = request.args.get(
        "code"
    )

    state = request.args.get(
        "state"
    )


    if not code:

        return (
            "LinkedIn authorization code missing.",
            400
        )


    if not state:

        return (
            "LinkedIn OAuth state missing.",
            400
        )


    if state not in linkedin_states:

        return (
            "Invalid or expired LinkedIn OAuth state.",
            400
        )


    linkedin_states.discard(
        state
    )


    try:

        token_data = (
            exchange_code_for_token(
                code
            )
        )

    except Exception as error:

        current_app.logger.exception(
            "LinkedIn token exchange failed"
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Error</title>
            <style>
                body {{
                    background:#050816;
                    color:white;
                    font-family:Arial,sans-serif;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    min-height:100vh;
                }}

                .card {{
                    padding:40px;
                    background:#0b1020;
                    border:1px solid #24304d;
                    border-radius:20px;
                }}

                h1 {{
                    color:#00f5ff;
                }}
            </style>
        </head>

        <body>

            <div class="card">

                <h1>
                    LinkedIn OAuth Error
                </h1>

                <p>
                    Token exchange failed.
                </p>

                <small>
                    {error}
                </small>

            </div>

        </body>
        </html>
        """, 500


    access_token = token_data.get(
        "access_token"
    )


    if not access_token:

        return (
            "LinkedIn did not return an access token.",
            500
        )


    # --------------------------------------------------------
    # STORE TOKEN
    #
    # The database implementation can decide how it stores
    # the connection. We first try the existing connect()
    # method so the current application architecture remains
    # compatible.
    # --------------------------------------------------------

    try:

        db().connect(
            "linkedin"
        )

    except Exception:

        current_app.logger.exception(
            "Could not save LinkedIn connection"
        )


    # --------------------------------------------------------
    # Store token in Flask application memory.
    #
    # This keeps the current project working without forcing
    # a database schema change immediately.
    # --------------------------------------------------------

    current_app.config[
        "LINKEDIN_ACCESS_TOKEN"
    ] = access_token


    current_app.config[
        "LINKEDIN_TOKEN_DATA"
    ] = token_data


    db().activity(
        "connect",
        "LinkedIn account connected successfully.",
        "success"
    )


    # --------------------------------------------------------
    # Return to dashboard
    # --------------------------------------------------------

    return redirect(
        "/?linkedin=connected"
    )


# ============================================================
# LINKEDIN STATUS
# ============================================================

@api.get("/linkedin/status")
def linkedin_status():

    token = current_app.config.get(
        "LINKEDIN_ACCESS_TOKEN"
    )


    connected = bool(
        token
    )


    return jsonify(
        success=True,
        connected=connected,
        platform="LinkedIn",
        message=(
            "LinkedIn connected."
            if connected
            else
            "LinkedIn is not connected."
        )
    )


# ============================================================
# CHAT
# ============================================================

@api.post("/chat")
def chat():

    data = request.get_json(
        silent=True
    ) or {}


    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()


    if not message:

        return bad(
            "Message required."
        )


    db().chatadd(
        "user",
        message
    )


    try:

        answer = agent.chat(
            message
        )

    except Exception as error:

        current_app.logger.exception(
            "Chat failed"
        )

        return jsonify(
            ok=False,
            error=str(error)
        ), 500


    db().chatadd(
        "assistant",
        answer
    )


    return jsonify(
        ok=True,
        answer=answer
    )

