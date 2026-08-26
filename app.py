# ============================================================
# NEONSOCIAL AI — FLASK BACKEND
# Built by SURESH REDDY
#
# MODIFIED / STABLE VERSION
#
# IMPORTANT FIXES:
# 1. Scheduler is initialized correctly.
# 2. Scheduler starts before Flask server.
# 3. update_post() is defined.
# 4. Manual publish route is before app.run().
# 5. Scheduled posts can publish automatically.
# 6. LinkedIn profile ID is converted to author URN.
# 7. Duplicate publishing is prevented with atomic
#    "publishing" state protection.
# 8. Date/time parsing supports browser datetime values.
# 9. Thread locking is used for shared post data.
# 10. Scheduler and manual publishing use the same
#     LinkedIn publishing flow.
# 11. Failed publishing can be retried safely.
# 12. Published posts cannot be published again.
# ============================================================

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    session,
    render_template
)

from datetime import datetime, timezone
import uuid
import os
import threading
import requests
import json
import html

from dotenv import load_dotenv

from backend.linkedin_api import (
    publish_text_post,
    LinkedInPublishError
)

from backend.linkedin_oauth import (
    create_state,
    build_authorization_url,
    exchange_code_for_token
)

from backend.scheduler import NeonScheduler

from backend.auth import (
    init_auth_database,
    create_user,
    authenticate_user,
    get_current_user,
    login_user,
    logout_user,
    login_required_api,
    login_required_page,
    get_db,
    using_postgres
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

init_auth_database()


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

TEMPLATES_DIR = os.path.join(
    FRONTEND_DIR,
    "templates"
)

STATIC_DIR = os.path.join(
    FRONTEND_DIR,
    "static"
)


# ============================================================
# LINKEDIN STORAGE
# ============================================================

LINKEDIN_STORAGE_FILE = os.path.join(
    BASE_DIR,
    "linkedin_connection.json"
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "neonsocial-development-secret-change-this"
)


# ============================================================
# SESSION CONFIGURATION
# ============================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = False

app.config["PERMANENT_SESSION_LIFETIME"] = 3600


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3:8b"
)

PORT = int(
    os.getenv(
        "PORT",
        "5000"
    )
)


# ============================================================
# IN-MEMORY DATABASE
# ============================================================

posts = {}

activity = []


# ============================================================
# LOCKS
# ============================================================

data_lock = threading.RLock()

linkedin_storage_lock = threading.Lock()

linkedin_oauth_lock = threading.Lock()


# ============================================================
# LINKEDIN OAUTH STATES
# ============================================================

linkedin_oauth_states = set()


# ============================================================
# LINKEDIN USERINFO API
# ============================================================

LINKEDIN_USERINFO_URL = (
    "https://api.linkedin.com/v2/userinfo"
)


# ============================================================
# LOAD LINKEDIN CONNECTION
# ============================================================

def load_linkedin_connection():

    with linkedin_storage_lock:

        if not os.path.exists(
            LINKEDIN_STORAGE_FILE
        ):

            return None

        try:

            with open(
                LINKEDIN_STORAGE_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if not isinstance(
                data,
                dict
            ):

                return None

            access_token = data.get(
                "access_token"
            )

            if not access_token:

                return None

            return data

        except Exception as error:

            print(
                "LinkedIn storage read error:",
                error
            )

            return None


# ============================================================
# SAVE LINKEDIN CONNECTION
# ============================================================

def save_linkedin_connection(
    token_data,
    profile=None
):

    if not token_data:

        return False

    access_token = token_data.get(
        "access_token"
    )

    if not access_token:

        return False

    data = {

        "connected":
            True,

        "access_token":
            access_token,

        "token_data":
            token_data,

        "profile":
            profile or {},

        "connected_at":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    temporary_file = (
        LINKEDIN_STORAGE_FILE
        + ".tmp"
    )

    with linkedin_storage_lock:

        try:

            with open(
                temporary_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4
                )

            os.replace(
                temporary_file,
                LINKEDIN_STORAGE_FILE
            )

            return True

        except Exception as error:

            print(
                "LinkedIn storage write error:",
                error
            )

            try:

                if os.path.exists(
                    temporary_file
                ):

                    os.remove(
                        temporary_file
                    )

            except Exception:

                pass

            return False


# ============================================================
# DELETE LINKEDIN CONNECTION
# ============================================================

def delete_linkedin_connection():

    with linkedin_storage_lock:

        try:

            if os.path.exists(
                LINKEDIN_STORAGE_FILE
            ):

                os.remove(
                    LINKEDIN_STORAGE_FILE
                )

            return True

        except Exception as error:

            print(
                "LinkedIn storage delete error:",
                error
            )

            return False


# ============================================================
# GET LINKEDIN ACCESS TOKEN
# ============================================================

def get_linkedin_access_token():

    session_token = session.get(
        "linkedin_access_token"
    )

    if session_token:

        return session_token

    stored_connection = (
        load_linkedin_connection()
    )

    if stored_connection:

        stored_token = (
            stored_connection.get(
                "access_token"
            )
        )

        if stored_token:

            session[
                "linkedin_access_token"
            ] = stored_token

            token_data = (
                stored_connection.get(
                    "token_data"
                )
            )

            profile = (
                stored_connection.get(
                    "profile"
                )
            )

            if token_data:

                session[
                    "linkedin_token_data"
                ] = token_data

            if profile:

                session[
                    "linkedin_profile"
                ] = profile

            session.modified = True

            return stored_token

    return None


# ============================================================
# GET LINKEDIN PROFILE
# ============================================================

def get_linkedin_profile(
    access_token
):

    if not access_token:

        return None

    try:

        response = requests.get(
            LINKEDIN_USERINFO_URL,
            headers={
                "Authorization":
                    f"Bearer {access_token}",

                "Accept":
                    "application/json"
            },
            timeout=10
        )

        print(
            "LinkedIn profile status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "LinkedIn profile response:",
                response.text
            )

            return None

        data = response.json()

        if not isinstance(
            data,
            dict
        ):

            return None

        return data

    except Exception as error:

        print(
            "LinkedIn profile request failed:",
            error
        )

        return None


# ============================================================
# NORMALIZE LINKEDIN PROFILE
# ============================================================

def normalize_linkedin_profile(
    profile
):

    if not profile:

        return {

            "id":
                None,

            "name":
                None,

            "first_name":
                None,

            "last_name":
                None,

            "email":
                None,

            "picture":
                None
        }

    first_name = profile.get(
        "given_name"
    )

    last_name = profile.get(
        "family_name"
    )

    name = profile.get(
        "name"
    )

    if not name:

        name_parts = []

        if first_name:

            name_parts.append(
                first_name
            )

        if last_name:

            name_parts.append(
                last_name
            )

        name = " ".join(
            name_parts
        ).strip()

    return {

        "id":
            profile.get(
                "sub"
            ),

        "name":
            name,

        "first_name":
            first_name,

        "last_name":
            last_name,

        "email":
            profile.get(
                "email"
            ),

        "picture":
            profile.get(
                "picture"
            )
    }


# ============================================================
# GET STORED LINKEDIN PROFILE
# ============================================================

def get_stored_linkedin_profile():

    profile = session.get(
        "linkedin_profile"
    )

    if profile:

        return profile

    stored_connection = (
        load_linkedin_connection()
    )

    if stored_connection:

        profile = (
            stored_connection.get(
                "profile"
            )
        )

        if profile:

            session[
                "linkedin_profile"
            ] = profile

            session.modified = True

            return profile

    return None


# ============================================================
# LINKEDIN CONNECTED
# ============================================================

def linkedin_is_connected():

    token = get_linkedin_access_token()

    return bool(
        token
    )


# ============================================================
# ACTIVITY LOGGER
# ============================================================

def log_activity(
    message,
    activity_type="info"
):

    now = datetime.now(
        timezone.utc
    )

    event = {

        "id":
            str(uuid.uuid4()),

        "message":
            message,

        "type":
            activity_type,

        "time":
            now.isoformat(),

        "display_time":
            now.strftime(
                "%I:%M:%S %p"
            )
    }

    with data_lock:

        activity.insert(
            0,
            event
        )

        if len(activity) > 100:

            activity.pop()

    return event


# ============================================================
# GET POSTS
#
# USED BY NeonScheduler
# ============================================================

def get_all_posts():

    with data_lock:

        return [
            dict(post)
            for post in posts.values()
        ]


# ============================================================
# FIND POST
# ============================================================

def find_post(
    session_id
):

    if not session_id:

        return None

    with data_lock:

        return posts.get(
            session_id
        )


# ============================================================
# UPDATE POST
# ============================================================

def update_post(
    session_id,
    updates
):

    if not session_id:

        return False

    if not isinstance(
        updates,
        dict
    ):

        return False

    with data_lock:

        post = posts.get(
            session_id
        )

        if not post:

            return False

        post.update(
            updates
        )

        return True


# ============================================================
# ATOMIC CLAIM FOR PUBLISHING
#
# IMPORTANT:
# This prevents two scheduler/manual threads from publishing
# the same post simultaneously.
# ============================================================

def claim_post_for_publishing(
    session_id
):

    if not session_id:

        return False

    with data_lock:

        post = posts.get(
            session_id
        )

        if not post:

            return False

        current_status = post.get(
            "status"
        )

        if current_status == "publishing":

            return False

        if current_status == "published":

            return False

        if current_status not in (
            "approved",
            "scheduled"
        ):

            return False

        post["status"] = "publishing"

        post["publish_started_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        post["publish_error"] = None

        return True


# ============================================================
# OLLAMA AVAILABLE
# ============================================================

def ollama_available():

    try:

        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=2
        )

        return (
            response.status_code == 200
        )

    except Exception:

        return False


# ============================================================
# OLLAMA GENERATION
# ============================================================

def generate_with_ollama(
    prompt,
    system_prompt=None
):

    payload = {

        "model":
            OLLAMA_MODEL,

        "prompt":
            prompt,

        "stream":
            False
    }

    if system_prompt:

        payload[
            "system"
        ] = system_prompt

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "response",
        ""
    ).strip()


# ============================================================
# DEMO CONTENT GENERATOR
# ============================================================

def demo_generate_post(
    topic,
    platform,
    tone
):

    platform_lower = (
        platform.lower()
    )

    if platform_lower == "linkedin":

        return f"""🚀 {topic}

The future belongs to people who are willing to learn, experiment and build.

Technology is changing faster than ever, and the biggest advantage is not simply knowing a tool.

It's knowing how to use that tool to solve real problems.

Here are 3 things worth focusing on:

• Learn the fundamentals
• Build real projects
• Share what you learn

Small improvements every day eventually create massive results.

What are you currently learning or building?

#AI #Technology #Innovation #Learning #Career"""

    if platform_lower == "instagram":

        return f"""🚀 {topic}

Learn.
Build.
Experiment.
Repeat.

The people who keep improving are the ones who create the future.

Don't wait until you're perfect.

Start now. ⚡

#AI #Technology #Innovation #Growth #Learning"""

    if platform_lower == "x":

        return f"""🚀 {topic}

Don't just consume technology.

Build with it.

Learn the fundamentals.
Create projects.
Share your journey.

The future belongs to builders. ⚡"""

    return f"""🚀 {topic}

Technology is transforming the way we learn, work and create.

The key is simple:

Learn.
Build.
Improve.
Repeat.

Let's create the future together.

#AI #Technology #Innovation"""


# ============================================================
# AI CONTENT GENERATOR
# ============================================================

def generate_post_content(
    topic,
    platform,
    tone
):

    system_prompt = """
You are Neon AI, an expert social media content strategist.

Create high-quality original social media posts.

Rules:
- Do not mention that you are an AI.
- Do not use unnecessary introductions.
- Make the content engaging.
- Match the requested platform.
- Match the requested tone.
- Use appropriate hashtags when useful.
- Return only the final post.
"""

    prompt = f"""
Create a social media post.

Topic:
{topic}

Platform:
{platform}

Tone:
{tone}

Make it engaging, professional and ready to publish.
"""

    if ollama_available():

        try:

            result = generate_with_ollama(
                prompt,
                system_prompt
            )

            if result:

                return result

        except Exception as error:

            print(
                "Ollama generation failed:",
                error
            )

    return demo_generate_post(
        topic,
        platform,
        tone
    )


# ============================================================
# AI CHAT
# ============================================================

def ai_chat(
    message
):

    system_prompt = """
You are Neon AI, the universal AI assistant inside NeonSocial AI.

You are a highly capable general-purpose AI assistant.

Your job is to understand the user's question and provide the most useful,
accurate, practical and clear answer possible.

You are not limited to social media, programming, Java, C, DSA or career topics.

You can help with general knowledge, science, mathematics, technology,
artificial intelligence, cybersecurity, programming, web development,
databases, cloud computing, DevOps, operating systems, networking,
C, C++, Java, Python, JavaScript, SQL, DSA, algorithms, Git, GitHub,
career guidance, interview preparation, education, research, writing,
business, marketing, social media, productivity, projects and other
legitimate topics.

If the user asks a programming question, provide useful code when appropriate.

If the user is a beginner, explain the concept from the basics.

If the user asks an advanced question, provide technically detailed information.

Use headings, bullets, examples or code when they improve clarity.

Give step-by-step instructions when the user asks how to do something.

If the user provides an error message, diagnose it and explain the fix.

Do not claim that you performed an action that you did not perform.

Do not invent real-time information.

Always prioritize correctness and usefulness.

Do not unnecessarily restrict your answers to NeonSocial AI features.

You are Neon AI, the user's general-purpose AI assistant inside NeonSocial AI.
"""

    if ollama_available():

        try:

            result = generate_with_ollama(
                message,
                system_prompt
            )

            if result:

                return result

        except Exception as error:

            print(
                "Ollama chat failed:",
                error
            )

    return demo_chat_response(
        message
    )
# ============================================================
# DEMO CHAT
# ============================================================

def demo_chat_response(
    message
):

    text = message.lower()

    if "java" in text:

        return """Java is a great language to learn for DSA and software development.

Start in this order:

1. Variables and data types
2. Operators
3. if/else
4. Loops
5. Arrays
6. Methods
7. Strings
8. OOP
9. Collections
10. DSA

If you are starting from zero, don't jump directly into advanced topics. Build the fundamentals first."""

    if "dsa" in text:

        return """DSA means Data Structures and Algorithms.

A beginner-friendly path is:

Arrays → Strings → Searching → Sorting → Recursion → Linked Lists → Stacks → Queues → Trees → Graphs → Dynamic Programming.

The most important thing is solving problems regularly rather than only reading theory."""

    if (
        "social" in text
        or "linkedin" in text
    ):

        return """For social media growth, focus on three things:

1. Valuable content
2. Consistency
3. Genuine engagement

For LinkedIn, a strong student strategy is to share your projects, learning journey, technical lessons and practical experiments."""

    return """Neon AI is online.

I can help you with programming, Java, C, DSA, AI, projects, career planning and social media.

For the fastest results, tell me exactly what you want to build or learn."""


# ============================================================
# PHASE 1 — STEP 1
# UNIVERSAL NEON AI BRAIN
# ============================================================
# This section is intentionally added without deleting the
# existing AI implementation. The original ai_chat() is kept
# as _legacy_ai_chat() and the wrapper below upgrades Neon AI
# to behave as a broad general-purpose assistant.
# ============================================================

_legacy_ai_chat = ai_chat


UNIVERSAL_NEON_AI_SYSTEM_PROMPT = """
You are Neon AI, the general-purpose intelligence inside NeonSocial AI.

Your job is to be a highly capable, clear, practical assistant for a very
wide range of user questions. Do not artificially restrict yourself to
social media, programming, Java, C, DSA, or career topics.

You can help with topics such as:
- General knowledge and everyday questions
- Science, mathematics and technology
- Programming, software engineering and debugging
- Java, C, C++, Python, JavaScript and other languages
- DSA, algorithms, databases, APIs, Git and cloud computing
- AI, machine learning, deep learning and cybersecurity
- Web development, mobile development and system design
- Projects, architecture, deployment and DevOps
- Education, study plans, explanations and exam preparation
- Business, startups, productivity and professional development
- Social media strategy, content creation and marketing
- Writing, rewriting, summarization and brainstorming
- Travel, food, hobbies and practical life questions
- Reasoning, comparisons, calculations and step-by-step problem solving
- Creative ideas, stories, scripts and other appropriate creative work

IMPORTANT BEHAVIOR:
1. Answer the user's actual question directly.
2. Do not say that you can only answer a limited list of topics.
3. If the user is a beginner, explain from the basics and then build upward.
4. For technical questions, give accurate examples and code when useful.
5. For difficult questions, break the solution into logical steps.
6. If the request is ambiguous, ask a concise clarifying question only when
   it is genuinely necessary; otherwise make a reasonable assumption and
   continue.
7. Never invent actions, tool calls, searches, live data, or results that
   you did not actually perform.
8. Be honest when information is uncertain or when real-time verification
   would be required.
9. Keep answers useful and readable. Use headings, bullets and code blocks
   when they improve clarity.
10. For programming code, provide complete runnable code when the user asks
    for a complete program.
11. Respect safety requirements and refuse harmful instructions when needed.
12. The assistant is called Neon AI. Do not claim to be ChatGPT, Claude,
    Gemini, or another service.
"""


def universal_neon_ai_chat(message):

    if ollama_available():

        try:

            current_date = datetime.now().strftime("%Y-%m-%d")

            prompt = f"""
Current date: {current_date}

User request:
{message}

Answer the user directly and completely. Use your broad knowledge and
reasoning. Do not unnecessarily restrict the answer to social-media topics.
"""

            result = generate_with_ollama(
                prompt,
                UNIVERSAL_NEON_AI_SYSTEM_PROMPT
            )

            if result:

                return result

        except Exception as error:

            print(
                "Universal Neon AI generation failed:",
                error
            )

    # Preserve the existing fallback behavior if Ollama is unavailable.
    return _legacy_ai_chat(message)


# Keep the existing /api/ai-chat route unchanged. Python resolves the
# global ai_chat name when the route executes, so it now uses the upgraded
# universal assistant above while the original implementation remains
# available through _legacy_ai_chat().
ai_chat = universal_neon_ai_chat


# ============================================================
# AUTHENTICATION API
# ============================================================
# ============================================================
# TEMPORARY USER MIGRATION
# SQLITE -> RENDER POSTGRESQL
#
# IMPORTANT:
# This route is temporary.
# Remove it immediately after migration succeeds.
# ============================================================

@app.route(
    "/api/internal/migrate-users",
    methods=["POST"]
)
def temporary_migrate_users():

    migration_token = os.getenv(
        "MIGRATION_TOKEN",
        ""
    ).strip()

    supplied_token = request.headers.get(
        "X-Migration-Token",
        ""
    ).strip()

    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    if not migration_token:
        return jsonify({
            "success": False,
            "error": "Migration is not configured."
        }), 503

    if not supplied_token:
        return jsonify({
            "success": False,
            "error": "Migration token required."
        }), 401

    if supplied_token != migration_token:
        return jsonify({
            "success": False,
            "error": "Invalid migration token."
        }), 403

    # --------------------------------------------------------
    # ONLY ALLOW POSTGRESQL
    # --------------------------------------------------------

    if not using_postgres():

        return jsonify({
            "success": False,
            "error": "PostgreSQL is not active."
        }), 503

    # --------------------------------------------------------
    # READ PAYLOAD
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    users = data.get(
        "users",
        []
    )

    if not isinstance(
        users,
        list
    ):

        return jsonify({
            "success": False,
            "error": "Invalid users payload."
        }), 400

    if len(users) > 100:

        return jsonify({
            "success": False,
            "error": "Too many users."
        }), 400

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    connection = None

    migrated = 0
    already_exists = 0
    failed = 0

    try:

        connection = get_db()

        cursor = connection.cursor()

        for user in users:

            if not isinstance(
                user,
                dict
            ):
                failed += 1
                continue

            name = str(
                user.get(
                    "name",
                    ""
                )
            ).strip()

            email = str(
                user.get(
                    "email",
                    ""
                )
            ).strip().lower()

            password_hash = str(
                user.get(
                    "password_hash",
                    ""
                )
            ).strip()

            created_at = str(
                user.get(
                    "created_at",
                    ""
                )
            ).strip()

            # ------------------------------------------------
            # BASIC VALIDATION
            # ------------------------------------------------

            if not email:
                failed += 1
                continue

            if not password_hash:
                failed += 1
                continue

            if not created_at:

                from datetime import datetime, timezone

                created_at = datetime.now(
                    timezone.utc
                ).isoformat()

            # ------------------------------------------------
            # CHECK EXISTING USER
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (
                    email,
                )
            )

            existing = cursor.fetchone()

            if existing:

                already_exists += 1
                continue

            # ------------------------------------------------
            # INSERT EXISTING PASSWORD HASH
            #
            # We do NOT know or transfer the plaintext
            # password.
            #
            # The existing password hash is preserved.
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password_hash,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    email,
                    password_hash,
                    created_at
                )
            )

            migrated += 1

        connection.commit()

        cursor.close()

        return jsonify({

            "success":
                True,

            "message":
                "User migration completed.",

            "migrated":
                migrated,

            "already_exists":
                already_exists,

            "failed":
                failed,

            "total_received":
                len(users)

        })

    except Exception as error:

        if connection:

            try:
                connection.rollback()
            except Exception:
                pass

        print(
            "Temporary migration error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                "Migration failed."

        }), 500

    finally:

        if connection:

            try:
                connection.close()
            except Exception:
                pass
# ============================================================
# SIGNUP PAGE
# ============================================================

@app.route("/signup")
def signup_page():

    return render_template(
        "signup.html"
    )
@app.route("/login")
def login_page():

    return render_template(
        "login.html"
    )


# ============================================================
# SIGNUP API
# ============================================================


@app.route(
    "/api/auth/signup",
    methods=["POST"]
)
@app.route(
    "/api/auth/register",
    methods=["POST"]
)
def auth_signup():

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()

    password = str(
        data.get(
            "password",
            ""
        )
    )

    confirm_password = str(
        data.get(
            "confirm_password",
            data.get(
                "confirmPassword",
                ""
            )
        )
    )

    if not name:

        return jsonify({
            "success": False,
            "error": "Name is required."
        }), 400

    if not email:

        return jsonify({
            "success": False,
            "error": "Email is required."
        }), 400

    if not password:

        return jsonify({
            "success": False,
            "error": "Password is required."
        }), 400

    if len(password) < 8:

        return jsonify({
            "success": False,
            "error": "Password must contain at least 8 characters."
        }), 400

    if confirm_password and password != confirm_password:

        return jsonify({
            "success": False,
            "error": "Passwords do not match."
        }), 400

    try:

        success, result = create_user(
            name,
            email,
            password
        )

    except Exception as error:

        print(
            "Signup error:",
            error
        )

        return jsonify({
            "success": False,
            "error": "Account creation service unavailable."
        }), 500

    if not success:

        return jsonify({
            "success": False,
            "error": result
        }), 400

    return jsonify({

        "success":
            True,

        "message":
            "Account created successfully.",

        "user":
            result

    }), 201
@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def auth_login():

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()

    password = str(
        data.get(
            "password",
            ""
        )
    )

    if not email:

        return jsonify({
            "success": False,
            "error": "Email is required."
        }), 400

    if not password:

        return jsonify({
            "success": False,
            "error": "Password is required."
        }), 400

    try:

        user = authenticate_user(
            email,
            password
        )

    except Exception as error:

        print(
            "Authentication error:",
            error
        )

        return jsonify({
            "success": False,
            "error": "Authentication service unavailable."
        }), 500

    if not user:

        return jsonify({
            "success": False,
            "error": "Invalid email or password."
        }), 401

    login_user(
        user
    )

    session.permanent = True

    return jsonify({

        "success": True,

        "authenticated": True,

        "user": user

    })


@app.route(
    "/api/auth/me",
    methods=["GET"]
)
def auth_me():

    user = get_current_user()

    if not user:

        return jsonify({

            "success": True,

            "authenticated": False,

            "user": None

        })

    return jsonify({

        "success": True,

        "authenticated": True,

        "user": user

    })


@app.route(
    "/api/auth/logout",
    methods=["POST"]
)
def auth_logout():

    logout_user()

    return jsonify({

        "success": True,

        "authenticated": False,

        "message":
            "Logged out successfully."

    })
# ============================================================
# PASSWORD RESET
# ============================================================

@app.route(
    "/api/auth/reset-password",
    methods=["POST"]
)
def auth_reset_password():

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()

    new_password = str(
        data.get(
            "new_password",
            ""
        )
    )

    confirm_password = str(
        data.get(
            "confirm_password",
            ""
        )
    )

    if not email:
        return jsonify({
            "success": False,
            "error": "Email is required."
        }), 400

    if not new_password:
        return jsonify({
            "success": False,
            "error": "New password is required."
        }), 400

    if len(new_password) < 8:
        return jsonify({
            "success": False,
            "error": "Password must contain at least 8 characters."
        }), 400

    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "error": "Passwords do not match."
        }), 400

    try:

        success, result = reset_password(
            email,
            new_password
        )

        if not success:
            return jsonify({
                "success": False,
                "error": result
            }), 400

        return jsonify({
            "success": True,
            "message": result
        }), 200

    except Exception as error:

        print(
            "Password reset endpoint error:",
            error
        )

        return jsonify({
            "success": False,
            "error": "Password reset service unavailable."
        }), 500
# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def index():

    index_file = os.path.join(
        TEMPLATES_DIR,
        "index.html"
    )

    if not os.path.exists(
        index_file
    ):

        return """
        <h1>NeonSocial frontend not found</h1>
        <p>
            Expected:
            frontend/templates/index.html
        </p>
        """, 500

    return render_template(
        "index.html"
    )


# ============================================================
# GOOGLE SEARCH CONSOLE VERIFICATION
# ============================================================

@app.route(
    "/google3f3cea12632babe5.html",
    methods=["GET"]
)
def google_search_console_verification():

    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "backend"
        ),
        "google3f3cea12632babe5.html"
    )


# ============================================================
# STATIC FILES
# ============================================================

@app.route(
    "/static/<path:filename>"
)
def static_files(
    filename
):

    return send_from_directory(
        STATIC_DIR,
        filename
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    ollama = ollama_available()

    connected = (
        linkedin_is_connected()
    )

    profile = (
        get_stored_linkedin_profile()
        if connected
        else None
    )

    return jsonify({

        "ok":
            True,

        "demo_mode":
            not ollama,

        "ollama":
            ollama,

        "engine":
            "Ollama"
            if ollama
            else "Demo",

        "model":
            OLLAMA_MODEL,

        "linkedin_connected":
            connected,

        "linkedin_profile":
            profile,

        "scheduler_running":
            scheduler.running
            if "scheduler" in globals()
            else False
    })


# ============================================================
# DASHBOARD
# ============================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard():

    with data_lock:

        values = list(
            posts.values()
        )

        current_activity = list(
            activity[:20]
        )

    total = len(values)

    waiting = sum(
        1
        for post in values
        if post.get("status") == "waiting"
    )

    approved = sum(
        1
        for post in values
        if post.get("status") == "approved"
    )

    scheduled = sum(
        1
        for post in values
        if post.get("status") == "scheduled"
    )

    publishing = sum(
        1
        for post in values
        if post.get("status") == "publishing"
    )

    published = sum(
        1
        for post in values
        if post.get("status") == "published"
    )

    rejected = sum(
        1
        for post in values
        if post.get("status") == "rejected"
    )

    failed = sum(
        1
        for post in values
        if post.get("status") == "failed"
    )

    linkedin_connected = (
        linkedin_is_connected()
    )

    linkedin_profile = (
        get_stored_linkedin_profile()
        if linkedin_connected
        else None
    )

    return jsonify({

        "success":
            True,

        "total":
            total,

        "waiting":
            waiting,

        "approved":
            approved,

        "scheduled":
            scheduled,

        "publishing":
            publishing,

        "published":
            published,

        "rejected":
            rejected,

        "failed":
            failed,

        "activity":
            current_activity,

        "connections": {

            "linkedin": {

                "connected":
                    linkedin_connected,

                "platform":
                    "LinkedIn",

                "profile":
                    linkedin_profile
            }
        },

        "linkedin_connected":
            linkedin_connected,

        "linkedin_profile":
            linkedin_profile,

        "scheduler_running":
            scheduler.running
            if "scheduler" in globals()
            else False
    })


# ============================================================
# ACTIVITY
# ============================================================

@app.route(
    "/api/activity",
    methods=["GET"]
)
def get_activity():

    with data_lock:

        current_activity = list(
            activity[:50]
        )

    return jsonify({

        "success":
            True,

        "activity":
            current_activity
    })


# ============================================================
# GENERATE
# ============================================================

@app.route(
    "/api/generate",
    methods=["POST"]
)
def generate():

    data = request.get_json(
        silent=True
    ) or {}

    topic = str(
        data.get(
            "topic",
            ""
        )
    ).strip()

    platform = str(
        data.get(
            "platform",
            "LinkedIn"
        )
    ).strip()

    tone = str(
        data.get(
            "tone",
            "Professional"
        )
    ).strip()

    if not topic:

        return jsonify({

            "success":
                False,

            "error":
                "Topic is required."
        }), 400

    if len(topic) > 1000:

        return jsonify({

            "success":
                False,

            "error":
                "Topic must be less than 1000 characters."
        }), 400

    try:

        content = generate_post_content(
            topic,
            platform,
            tone
        )

    except Exception as error:

        print(
            "Generation error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                "Unable to generate content."
        }), 500

    session_id = str(
        uuid.uuid4()
    )

    post = {

        "session_id":
            session_id,

        "topic":
            topic,

        "platform":
            platform,

        "tone":
            tone,

        "content":
            content,

        "status":
            "waiting",

        "created_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "approved_at":
            None,

        "scheduled_at":
            None,

        "published_at":
            None,

        "publish_started_at":
            None,

        "linkedin_post_id":
            None,

        "publish_error":
            None,

        "failed_at":
            None
    }

    with data_lock:

        posts[
            session_id
        ] = post

    log_activity(
        "AI generated a new post",
        "generate"
    )

    return jsonify({

        "success":
            True,

        "session_id":
            session_id,

        "content":
            content,

        "platform":
            platform,

        "tone":
            tone,

        "status":
            "waiting"
    })


# ============================================================
# APPROVE
# ============================================================

@app.route(
    "/api/approve",
    methods=["POST"]
)
def approve():

    data = request.get_json(
        silent=True
    ) or {}

    session_id = data.get(
        "session_id"
    )

    post = find_post(
        session_id
    )

    if not post:

        return jsonify({

            "success":
                False,

            "error":
                "Post session not found."
        }), 404

    with data_lock:

        current_status = post.get(
            "status"
        )

        if current_status == "approved":

            return jsonify({

                "success":
                    True,

                "message":
                    "Post already approved.",

                "status":
                    "approved"
            })

        if current_status != "waiting":

            return jsonify({

                "success":
                    False,

                "error":
                    f"Post cannot be approved from "
                    f"{current_status} state."
            }), 400

        post["status"] = "approved"

        post["approved_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

    log_activity(
        "Post approved by human",
        "approve"
    )

    return jsonify({

        "success":
            True,

        "message":
            "Post approved.",

        "status":
            "approved",

        "session_id":
            session_id
    })


# ============================================================
# REJECT
# ============================================================

@app.route(
    "/api/reject",
    methods=["POST"]
)
def reject():

    data = request.get_json(
        silent=True
    ) or {}

    session_id = data.get(
        "session_id"
    )

    post = find_post(
        session_id
    )

    if not post:

        return jsonify({

            "success":
                False,

            "error":
                "Post session not found."
        }), 404

    with data_lock:

        current_status = post.get(
            "status"
        )

        if current_status in (
            "published",
            "publishing"
        ):

            return jsonify({

                "success":
                    False,

                "error":
                    "Published or publishing posts cannot be rejected."
            }), 400

        post["status"] = "rejected"

    log_activity(
        "Post rejected by human",
        "reject"
    )

    return jsonify({

        "success":
            True,

        "message":
            "Post rejected.",

        "status":
            "rejected",

        "session_id":
            session_id
    })


# ============================================================
# DATE/TIME PARSER
#
# Supports:
#
# YYYY-MM-DD HH:MM
# YYYY-MM-DDTHH:MM
# YYYY-MM-DDTHH:MM:SS
# browser datetime-local values
# ============================================================

def parse_scheduled_datetime(
    date_value,
    time_value=None
):

    date_value = str(
        date_value or ""
    ).strip()

    if time_value is not None:

        time_value = str(
            time_value or ""
        ).strip()

    if not date_value:

        return None

    candidates = []

    if time_value:

        candidates.append(
            f"{date_value} {time_value}"
        )

        candidates.append(
            f"{date_value}T{time_value}"
        )

    else:

        candidates.append(
            date_value
        )

    for candidate in candidates:

        candidate = candidate.strip()

        try:

            return datetime.fromisoformat(
                candidate
            )

        except ValueError:

            pass

        try:

            return datetime.strptime(
                candidate,
                "%Y-%m-%d %H:%M"
            )

        except ValueError:

            pass

        try:

            return datetime.strptime(
                candidate,
                "%Y-%m-%dT%H:%M"
            )

        except ValueError:

            pass

        try:

            return datetime.strptime(
                candidate,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            pass

        try:

            return datetime.strptime(
                candidate,
                "%Y-%m-%dT%H:%M:%S"
            )

        except ValueError:

            pass

    return None


# ============================================================
# SCHEDULE
# ============================================================

@app.route(
    "/api/schedule",
    methods=["POST"]
)
def schedule():

    data = request.get_json(
        silent=True
    ) or {}

    session_id = data.get(
        "session_id"
    )

    date_value = data.get(
        "date",
        ""
    )

    time_value = data.get(
        "time",
        ""
    )

    post = find_post(
        session_id
    )

    if not post:

        return jsonify({

            "success":
                False,

            "error":
                "Post session not found."
        }), 404

    with data_lock:

        current_status = post.get(
            "status"
        )

        if current_status != "approved":

            return jsonify({

                "success":
                    False,

                "error":
                    "Post must be approved before scheduling."
            }), 400

    if not date_value:

        return jsonify({

            "success":
                False,

            "error":
                "Date and time are required."
        }), 400

    scheduled_datetime = (
        parse_scheduled_datetime(
            date_value,
            time_value
        )
    )

    if scheduled_datetime is None:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid date/time. Use YYYY-MM-DD HH:MM or browser datetime-local format."
        }), 400

    # --------------------------------------------------------
    # Normalize timezone.
    #
    # Browser datetime-local has no timezone, so it is treated
    # as local server time when no timezone is supplied.
    # --------------------------------------------------------

    if scheduled_datetime.tzinfo is not None:

        scheduled_datetime = (
            scheduled_datetime.replace(
                tzinfo=None
            )
        )

    now_local = datetime.now()

    if scheduled_datetime <= now_local:

        return jsonify({

            "success":
                False,

            "error":
                "Scheduled time must be in the future."
        }), 400

    scheduled_at = (
        scheduled_datetime.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    update_post(
        session_id,
        {

            "status":
                "scheduled",

            "scheduled_at":
                scheduled_at,

            "publish_error":
                None,

            "failed_at":
                None,

            "publish_started_at":
                None
        }
    )

    log_activity(
        f"Post scheduled for {scheduled_at}",
        "schedule"
    )

    return jsonify({

        "success":
            True,

        "message":
            "Post scheduled.",

        "scheduled_at":
            scheduled_at,

        "status":
            "scheduled",

        "session_id":
            session_id
    })


# ============================================================
# AI CHAT
# ============================================================

@app.route(
    "/api/ai-chat",
    methods=["POST"]
)
def ai_chat_route():

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

        return jsonify({

            "success":
                False,

            "error":
                "Message is required."
        }), 400

    if len(message) > 10000:

        return jsonify({

            "success":
                False,

            "error":
                "Message is too long."
        }), 400

    try:

        response = ai_chat(
            message
        )

    except Exception as error:

        print(
            "AI chat error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                "AI assistant unavailable."
        }), 500

    log_activity(
        "Neon AI answered a user request",
        "ai"
    )

    return jsonify({

        "success":
            True,

        "response":
            response
    })


# ============================================================
# GET ONE POST
# ============================================================

@app.route(
    "/api/post/<session_id>",
    methods=["GET"]
)
def get_post(
    session_id
):

    post = find_post(
        session_id
    )

    if not post:

        return jsonify({

            "success":
                False,

            "error":
                "Post not found."
        }), 404

    with data_lock:

        post_copy = dict(
            post
        )

    return jsonify({

        "success":
            True,

        "post":
            post_copy
    })


# ============================================================
# ALL POSTS
# ============================================================

@app.route(
    "/api/posts",
    methods=["GET"]
)
def get_posts():

    with data_lock:

        values = [
            dict(post)
            for post in posts.values()
        ]

    values.reverse()

    return jsonify({

        "success":
            True,

        "posts":
            values
    })


# ============================================================
# COMMON LINKEDIN PUBLISH FUNCTION
#
# Both manual publishing and scheduler publishing can use this.
# ============================================================

def publish_post_to_linkedin(
    session_id
):

    post = find_post(
        session_id
    )

    if not post:

        return {
            "success": False,
            "error": "Post not found.",
            "status": "failed"
        }

    # --------------------------------------------------------
    # ATOMIC CLAIM
    #
    # This is extremely important.
    #
    # If scheduler and manual publish happen at exactly the
    # same time, only one of them will receive True.
    # --------------------------------------------------------

    claimed = claim_post_for_publishing(
        session_id
    )

    if not claimed:

        current_post = find_post(
            session_id
        )

        current_status = (
            current_post.get("status")
            if current_post
            else None
        )

        if current_status == "published":

            return {
                "success": True,
                "message": "Post is already published.",
                "status": "published",
                "linkedin_post_id":
                    current_post.get(
                        "linkedin_post_id"
                    )
            }

        if current_status == "publishing":

            return {
                "success": False,
                "error":
                    "Post is already being published.",
                "status":
                    "publishing"
            }

        return {
            "success": False,
            "error":
                "Post cannot be published from its current state.",
            "status":
                current_status
        }

    access_token = (
        get_linkedin_access_token()
    )

    if not access_token:

        update_post(
            session_id,
            {

                "status":
                    "failed",

                "publish_error":
                    "LinkedIn is not connected.",

                "failed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )

        return {
            "success":
                False,

            "error":
                "LinkedIn is not connected.",

            "status":
                "failed"
        }

    profile = (
        get_stored_linkedin_profile()
    ) or {}

    profile_id = profile.get(
        "id"
    )

    if not profile_id:

        update_post(
            session_id,
            {

                "status":
                    "failed",

                "publish_error":
                    "LinkedIn member ID unavailable.",

                "failed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )

        return {
            "success":
                False,

            "error":
                "LinkedIn member ID unavailable.",

            "status":
                "failed"
        }

    # --------------------------------------------------------
    # LINKEDIN AUTHOR URN
    # --------------------------------------------------------

    profile_id = str(
        profile_id
    ).strip()

    if profile_id.startswith(
        "urn:li:person:"
    ):

        author_urn = profile_id

    else:

        author_urn = (
            f"urn:li:person:{profile_id}"
        )

    # --------------------------------------------------------
    # GET CONTENT SAFELY
    # --------------------------------------------------------

    with data_lock:

        current_post = posts.get(
            session_id
        )

        if not current_post:

            return {
                "success":
                    False,

                "error":
                    "Post disappeared before publishing.",

                "status":
                    "failed"
            }

        content = str(
            current_post.get(
                "content",
                ""
            )
        ).strip()

    if not content:

        update_post(
            session_id,
            {

                "status":
                    "failed",

                "publish_error":
                    "Post content is empty.",

                "failed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )

        return {
            "success":
                False,

            "error":
                "Post content is empty.",

            "status":
                "failed"
        }

    # --------------------------------------------------------
    # PUBLISH
    # --------------------------------------------------------

    try:

        result = publish_text_post(
            access_token=access_token,
            author_urn=author_urn,
            content=content
        )

        if not isinstance(
            result,
            dict
        ):

            result = {}

        linkedin_post_id = (
            result.get(
                "post_id"
            )
        )

        update_post(
            session_id,
            {

                "status":
                    "published",

                "published_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                "linkedin_post_id":
                    linkedin_post_id,

                "publish_error":
                    None
            }
        )

        log_activity(
            "Post published to LinkedIn",
            "publish"
        )

        return {

            "success":
                True,

            "status":
                "published",

            "linkedin_post_id":
                linkedin_post_id
        }

    except LinkedInPublishError as error:

        update_post(
            session_id,
            {

                "status":
                    "failed",

                "publish_error":
                    str(error),

                "failed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )

        log_activity(
            "LinkedIn publishing failed",
            "error"
        )

        return {

            "success":
                False,

            "error":
                str(error),

            "status":
                "failed"
        }

    except Exception as error:

        update_post(
            session_id,
            {

                "status":
                    "failed",

                "publish_error":
                    str(error),

                "failed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )

        print(
            "LinkedIn publishing error:",
            error
        )

        log_activity(
            "LinkedIn publishing failed",
            "error"
        )

        return {

            "success":
                False,

            "error":
                str(error),

            "status":
                "failed"
        }


# ============================================================
# MANUAL PUBLISH
# ============================================================

@app.route(
    "/api/post/<session_id>/publish",
    methods=["POST"]
)
def manual_publish(
    session_id
):

    post = find_post(
        session_id
    )

    if not post:

        return jsonify({

            "success":
                False,

            "error":
                "Post not found."
        }), 404

    with data_lock:

        current_status = post.get(
            "status"
        )

    if current_status not in (
        "approved",
        "scheduled"
    ):

        if current_status == "published":

            return jsonify({

                "success":
                    True,

                "message":
                    "Post is already published.",

                "status":
                    "published",

                "linkedin_post_id":
                    post.get(
                        "linkedin_post_id"
                    )
            })

        if current_status == "publishing":

            return jsonify({

                "success":
                    False,

                "error":
                    "Post is already being published.",

                "status":
                    "publishing"
            }), 409

        return jsonify({

            "success":
                False,

            "error":
                "Post must be approved or scheduled.",

            "status":
                current_status
        }), 400

    result = publish_post_to_linkedin(
        session_id
    )

    if result.get(
        "success"
    ):

        return jsonify(
            result
        )

    status_code = 500

    if (
        result.get("status")
        == "publishing"
    ):

        status_code = 409

    elif (
        "LinkedIn is not connected"
        in result.get("error", "")
    ):

        status_code = 401

    elif (
        result.get("status")
        == "failed"
    ):

        status_code = 502

    return jsonify(
        result
    ), status_code


# ============================================================
# LINKEDIN STATUS
# ============================================================

@app.route(
    "/api/linkedin/status",
    methods=["GET"]
)
def linkedin_status():

    connected = (
        linkedin_is_connected()
    )

    profile = (
        get_stored_linkedin_profile()
        if connected
        else None
    )

    return jsonify({

        "success":
            True,

        "connected":
            connected,

        "platform":
            "LinkedIn",

        "profile":
            profile,

        "email":
            (
                profile.get("email")
                if profile
                else None
            ),

        "name":
            (
                profile.get("name")
                if profile
                else None
            ),

        "message":
            (
                "LinkedIn connected."
                if connected
                else
                "LinkedIn not connected."
            )
    })


# ============================================================
# LINKEDIN PROFILE
# ============================================================

@app.route(
    "/api/linkedin/profile",
    methods=["GET"]
)
def linkedin_profile():

    token = get_linkedin_access_token()

    if not token:

        return jsonify({

            "success":
                False,

            "connected":
                False,

            "error":
                "LinkedIn is not connected."
        }), 401

    profile = get_stored_linkedin_profile()

    if not profile:

        raw_profile = (
            get_linkedin_profile(
                token
            )
        )

        if raw_profile:

            profile = (
                normalize_linkedin_profile(
                    raw_profile
                )
            )

            session[
                "linkedin_profile"
            ] = profile

            stored = (
                load_linkedin_connection()
            )

            token_data = (
                stored.get(
                    "token_data",
                    {}
                )
                if stored
                else {}
            )

            save_linkedin_connection(
                token_data,
                profile
            )

    if not profile:

        return jsonify({

            "success":
                False,

            "connected":
                True,

            "error":
                "LinkedIn account connected, but profile information could not be retrieved."
        }), 502

    return jsonify({

        "success":
            True,

        "connected":
            True,

        "platform":
            "LinkedIn",

        "profile":
            profile
    })


# ============================================================
# LINKEDIN CONNECT
# ============================================================

@app.route(
    "/api/linkedin/connect",
    methods=["GET"]
)
def linkedin_connect():

    client_id = os.getenv(
        "LINKEDIN_CLIENT_ID"
    )

    if not client_id:

        return jsonify({

            "success":
                False,

            "error":
                "LinkedIn Client ID is not configured."
        }), 500

    try:

        state = create_state()

        session[
            "linkedin_oauth_state"
        ] = state

        session.permanent = True

        with linkedin_oauth_lock:

            linkedin_oauth_states.add(
                state
            )

        authorization_url = (
            build_authorization_url(
                state
            )
        )

        return jsonify({

            "success":
                True,

            "redirect":
                authorization_url
        })

    except Exception as error:

        print(
            "LinkedIn connect error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                "Unable to start LinkedIn OAuth."
        }), 500


# ============================================================
# LINKEDIN CALLBACK
# ============================================================

@app.route(
    "/oauth/linkedin/callback",
    methods=["GET"]
)
def linkedin_callback():

    existing_token = (
        get_linkedin_access_token()
    )

    code = request.args.get(
        "code"
    )

    returned_state = request.args.get(
        "state"
    )

    oauth_error = request.args.get(
        "error"
    )

    # ========================================================
    # OAUTH ERROR
    # ========================================================

    if oauth_error:

        description = request.args.get(
            "error_description",
            "LinkedIn authorization failed."
        )

        return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>LinkedIn Connection Failed</title>
<style>
html, body {{
    margin:0;
    padding:0;
    width:100%;
    height:100%;
}}

body {{
    display:flex;
    align-items:center;
    justify-content:center;
    background:
        radial-gradient(
            circle at 50% 40%,
            #172c63 0%,
            #080b1a 45%,
            #02030a 100%
        );
    color:white;
    font-family:Arial, Helvetica, sans-serif;
}}

.card {{
    width:min(90%,560px);
    padding:45px;
    text-align:center;
    border-radius:25px;
    background:rgba(10,16,40,.78);
    border:1px solid rgba(255,79,145,.5);
    box-shadow:
        0 0 35px rgba(255,79,145,.15),
        0 0 100px rgba(125,70,255,.12);
    backdrop-filter:blur(20px);
}}

h1 {{
    color:#ff4f91;
}}

p {{
    color:#cbd5ff;
    line-height:1.7;
}}

.button {{
    display:inline-block;
    margin-top:20px;
    padding:12px 24px;
    border-radius:12px;
    text-decoration:none;
    color:#00151b;
    background:
        linear-gradient(
            135deg,
            #00f5ff,
            #00ff9d
        );
    font-weight:bold;
}}
</style>
</head>

<body>

<div class="card">

<h1>
LinkedIn Connection Failed
</h1>

<p>
{html.escape(description)}
</p>

<a
    class="button"
    href="/"
>
Return to NeonSocial
</a>

</div>

</body>
</html>
"""


    # ========================================================
    # ALREADY CONNECTED
    # ========================================================

    if not code and existing_token:

        profile = (
            get_stored_linkedin_profile()
        )

        profile_name = (
            profile.get("name")
            if profile
            else "LinkedIn account"
        )

        profile_email = (
            profile.get("email")
            if profile
            else None
        )

        email_html = ""

        if profile_email:

            email_html = f"""
<p>
Email:
<strong>
{html.escape(profile_email)}
</strong>
</p>
"""

        return f"""
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<title>
LinkedIn Already Connected
</title>

<style>

html,
body {{
    margin:0;
    padding:0;
    width:100%;
    height:100%;
}}

body {{
    display:flex;
    align-items:center;
    justify-content:center;

    background:
        radial-gradient(
            circle at center,
            #102f64 0%,
            #070b19 48%,
            #02030a 100%
        );

    color:white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;
}}

.card {{
    width:min(90%,560px);
    padding:50px;
    text-align:center;
    border-radius:28px;

    background:
        rgba(9,17,42,.82);

    border:
        1px solid rgba(0,245,255,.55);

    box-shadow:
        0 0 30px rgba(0,245,255,.2),
        0 0 90px rgba(120,70,255,.16);

    backdrop-filter:
        blur(25px);
}}

.icon {{
    width:90px;
    height:90px;

    margin:
        0 auto 25px;

    border-radius:50%;

    display:flex;

    align-items:center;
    justify-content:center;

    font-size:50px;

    color:#00151b;

    background:
        linear-gradient(
            135deg,
            #00f5ff,
            #00ff9d
        );

    box-shadow:
        0 0 35px rgba(0,245,255,.5);
}}

h1 {{
    color:#00f5ff;
    margin-bottom:12px;
}}

p {{
    color:#cdd7ff;
    line-height:1.7;
}}

.button {{
    display:inline-block;

    margin-top:20px;

    padding:12px 24px;

    border-radius:12px;

    text-decoration:none;

    color:#00151b;

    background:
        linear-gradient(
            135deg,
            #00f5ff,
            #00ff9d
        );

    font-weight:bold;
}}

</style>

</head>

<body>

<div class="card">

<div class="icon">
✓
</div>

<h1>
LinkedIn Already Connected
</h1>

<p>
Connected account:
<strong>
{html.escape(profile_name)}
</strong>
</p>

{email_html}

<p>
Your LinkedIn account is already connected to NeonSocial.
</p>

<a
    class="button"
    href="/"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
"""


    # ========================================================
    # CODE REQUIRED
    # ========================================================

    if not code:

        return """
<!DOCTYPE html>

<html>

<body style="
background:#050816;
color:white;
font-family:Arial;
display:flex;
align-items:center;
justify-content:center;
height:100vh;
">

<div style="
text-align:center;
">

<h2>
LinkedIn authorization code is missing.
</h2>

<p>
Please start the LinkedIn connection from NeonSocial.
</p>

<a
href="/"
style="
color:#00f5ff;
"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
""", 400


    # ========================================================
    # STATE REQUIRED
    # ========================================================

    if not returned_state:

        return """
<!DOCTYPE html>

<html>

<body style="
background:#050816;
color:white;
font-family:Arial;
display:flex;
align-items:center;
justify-content:center;
height:100vh;
">

<div style="
text-align:center;
">

<h2>
LinkedIn OAuth state is missing.
</h2>

<p>
Please start the LinkedIn connection again.
</p>

<a
href="/"
style="
color:#00f5ff;
"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
""", 400


    # ========================================================
    # SESSION STATE
    # ========================================================

    saved_state = session.get(
        "linkedin_oauth_state"
    )


    # ========================================================
    # SERVER STATE
    # ========================================================

    state_is_valid_server_side = False

    with linkedin_oauth_lock:

        if (
            returned_state
            in linkedin_oauth_states
        ):

            state_is_valid_server_side = True


    # ========================================================
    # VALIDATE STATE
    # ========================================================

    if saved_state:

        if returned_state != saved_state:

            if not state_is_valid_server_side:

                return """
<!DOCTYPE html>

<html>

<body style="
background:#050816;
color:white;
font-family:Arial;
display:flex;
align-items:center;
justify-content:center;
height:100vh;
">

<div style="
text-align:center;
">

<h2>
Invalid LinkedIn OAuth state.
</h2>

<p>
Please start the LinkedIn connection again.
</p>

<a
href="/"
style="
color:#00f5ff;
"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
""", 400

    else:

        if not state_is_valid_server_side:

            if linkedin_is_connected():

                return """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
LinkedIn Already Connected
</title>

</head>

<body style="
background:#050816;
color:white;
font-family:Arial;
display:flex;
align-items:center;
justify-content:center;
height:100vh;
">

<div style="
text-align:center;
">

<h1 style="
color:#00f5ff;
">
LinkedIn Already Connected
</h1>

<p>
Your LinkedIn account is already connected.
</p>

<a
href="/"
style="
color:#00f5ff;
"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
"""

            return """
<!DOCTYPE html>

<html>

<body style="
background:#050816;
color:white;
font-family:Arial;
display:flex;
align-items:center;
justify-content:center;
height:100vh;
">

<div style="
text-align:center;
">

<h2>
OAuth session expired.
</h2>

<p>
Please start the LinkedIn connection again.
</p>

<a
href="/"
style="
color:#00f5ff;
"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
""", 400


    # ========================================================
    # REMOVE USED STATE
    # ========================================================

    with linkedin_oauth_lock:

        linkedin_oauth_states.discard(
            returned_state
        )


    # ========================================================
    # EXCHANGE CODE FOR TOKEN
    # ========================================================

    try:

        token_data = (
            exchange_code_for_token(
                code
            )
        )

        access_token = (
            token_data.get(
                "access_token"
            )
        )

        if not access_token:

            raise RuntimeError(
                "LinkedIn did not return an access token."
            )


        # ====================================================
        # SESSION TOKEN
        # ====================================================

        session[
            "linkedin_access_token"
        ] = access_token

        session[
            "linkedin_token_data"
        ] = token_data


        # ====================================================
        # GET PROFILE
        # ====================================================

        raw_profile = (
            get_linkedin_profile(
                access_token
            )
        )

        normalized_profile = (
            normalize_linkedin_profile(
                raw_profile
            )
        )


        # ====================================================
        # SESSION PROFILE
        # ====================================================

        session[
            "linkedin_profile"
        ] = normalized_profile


        # ====================================================
        # PERMANENT STORAGE
        # ====================================================

        saved_successfully = (
            save_linkedin_connection(
                token_data,
                normalized_profile
            )
        )

        if not saved_successfully:

            print(
                "WARNING: LinkedIn token could not be persisted."
            )


        # ====================================================
        # REMOVE OAUTH STATE
        # ====================================================

        session.pop(
            "linkedin_oauth_state",
            None
        )

        session.modified = True


        # ====================================================
        # LOG
        # ====================================================

        log_activity(
            "LinkedIn account connected",
            "linkedin"
        )


        # ====================================================
        # PROFILE DISPLAY
        # ====================================================

        profile_name = (
            normalized_profile.get(
                "name"
            )
            or "LinkedIn account"
        )

        profile_email = (
            normalized_profile.get(
                "email"
            )
        )

        profile_picture = (
            normalized_profile.get(
                "picture"
            )
        )

        picture_html = ""

        if profile_picture:

            picture_html = f"""
<img
src="{html.escape(profile_picture, quote=True)}"
alt="LinkedIn profile"
style="
width:90px;
height:90px;
border-radius:50%;
object-fit:cover;
margin-bottom:20px;
box-shadow:0 0 30px rgba(0,245,255,.4);
"
>
"""

        email_html = ""

        if profile_email:

            email_html = f"""
<p>
Email:
<strong>
{html.escape(profile_email)}
</strong>
</p>
"""

        else:

            email_html = """
<p>
Email:
<strong>
Not available
</strong>
</p>

<p style="
font-size:13px;
color:#8893b8;
">
Make sure your LinkedIn application requests
the <b>email</b> OpenID Connect scope.
</p>
"""


        # ====================================================
        # SUCCESS PAGE
        # ====================================================

        return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
LinkedIn Connected
</title>

<style>

html,
body {{
    margin:0;
    padding:0;
    width:100%;
    height:100%;
}}

body {{
    display:flex;
    align-items:center;
    justify-content:center;

    background:
        radial-gradient(
            circle at center,
            #102f64 0%,
            #070b19 48%,
            #02030a 100%
        );

    color:white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;
}}

.card {{
    width:min(90%,560px);

    padding:50px;

    text-align:center;

    border-radius:28px;

    background:
        rgba(9,17,42,.82);

    border:
        1px solid rgba(0,245,255,.55);

    box-shadow:
        0 0 30px rgba(0,245,255,.2),
        0 0 90px rgba(120,70,255,.16);

    backdrop-filter:
        blur(25px);
}}

.icon {{
    width:90px;
    height:90px;

    margin:
        0 auto 25px;

    border-radius:50%;

    display:flex;

    align-items:center;

    justify-content:center;

    font-size:50px;

    color:#00151b;

    background:
        linear-gradient(
            135deg,
            #00f5ff,
            #00ff9d
        );

    box-shadow:
        0 0 35px rgba(0,245,255,.5);
}}

h1 {{
    color:#00f5ff;
    margin-bottom:12px;
}}

p {{
    color:#cdd7ff;
    line-height:1.7;
}}

.button {{
    display:inline-block;

    margin-top:20px;

    padding:12px 24px;

    border-radius:12px;

    text-decoration:none;

    color:#00151b;

    background:
        linear-gradient(
            135deg,
            #00f5ff,
            #00ff9d
        );

    font-weight:bold;
}}

</style>

</head>

<body>

<div class="card">

<div class="icon">
✓
</div>

{picture_html}

<h1>
LinkedIn Connected
</h1>

<p>
Your LinkedIn account has been connected successfully.
</p>

<p>
Account:
<strong>
{html.escape(profile_name)}
</strong>
</p>

{email_html}

<p>
Your connection has been saved.
</p>

<a
    class="button"
    href="/"
>
Return to NeonSocial
</a>

</div>

</body>

</html>
"""


    # ========================================================
    # TOKEN EXCHANGE ERROR
    # ========================================================

    except Exception as error:

        print(
            "LinkedIn token exchange failed:",
            error
        )

        return """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
LinkedIn Connection Error
</title>

<style>

body {

    margin:0;

    min-height:100vh;

    display:flex;

    align-items:center;

    justify-content:center;

    background:#030511;

    color:white;

    font-family:Arial;
}

.card {

    padding:45px;

    text-align:center;

    background:
        rgba(15,20,45,.9);

    border:
        1px solid #ff3b81;

    border-radius:25px;

    box-shadow:
        0 0 40px rgba(255,59,129,.2);
}

h1 {

    color:#ff4f91;
}

p {

    color:#cbd5ff;
}

a {

    color:#00f5ff;
}

</style>

</head>

<body>

<div class="card">

<h1>
LinkedIn Connection Failed
</h1>

<p>
Unable to complete LinkedIn authentication.
</p>

<p>
Please check your LinkedIn OAuth configuration.
</p>

<a href="/">
Return to NeonSocial
</a>

</div>

</body>

</html>
""", 500


# ============================================================
# LINKEDIN DISCONNECT
# ============================================================

@app.route(
    "/api/linkedin/disconnect",
    methods=["POST"]
)
def linkedin_disconnect():

    try:

        session.pop(
            "linkedin_access_token",
            None
        )

        session.pop(
            "linkedin_token_data",
            None
        )

        session.pop(
            "linkedin_profile",
            None
        )

        session.pop(
            "linkedin_oauth_state",
            None
        )

        session.modified = True

        delete_linkedin_connection()

        log_activity(
            "LinkedIn account disconnected",
            "linkedin"
        )

        return jsonify({

            "success":
                True,

            "connected":
                False,

            "profile":
                None,

            "message":
                "LinkedIn disconnected."
        })

    except Exception as error:

        print(
            "LinkedIn disconnect error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                "Unable to disconnect LinkedIn."
        }), 500


# ============================================================
# SCHEDULER
#
# Created AFTER all callback functions are defined.
# ============================================================

scheduler = NeonScheduler(

    get_posts=get_all_posts,

    update_post=update_post,

    get_access_token=get_linkedin_access_token,

    log_activity=log_activity,

    interval=5
)


# ============================================================
# SCHEDULER START API
# ============================================================

@app.route(
    "/api/scheduler/start",
    methods=["POST"]
)
def start_scheduler():

    try:

        scheduler.start()

        log_activity(
            "Automatic post scheduler started",
            "scheduler"
        )

        return jsonify({

            "success":
                True,

            "running":
                scheduler.running,

            "message":
                "Scheduler started."
        })

    except Exception as error:

        print(
            "Scheduler start error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)
        }), 500


# ============================================================
# SCHEDULER STOP API
# ============================================================

@app.route(
    "/api/scheduler/stop",
    methods=["POST"]
)
def stop_scheduler():

    try:

        scheduler.stop()

        log_activity(
            "Automatic post scheduler stopped",
            "scheduler"
        )

        return jsonify({

            "success":
                True,

            "running":
                scheduler.running,

            "message":
                "Scheduler stopped."
        })

    except Exception as error:

        print(
            "Scheduler stop error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)
        }), 500


# ============================================================
# SCHEDULER STATUS
# ============================================================

@app.route(
    "/api/scheduler/status",
    methods=["GET"]
)
def scheduler_status():

    return jsonify({

        "success":
            True,

        "running":
            scheduler.running,

        "interval":
            scheduler.interval
    })


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success":
                False,

            "error":
                "API endpoint not found."
        }), 404

    return error


# ============================================================
# 500
# ============================================================

@app.errorhandler(500)
def internal_error(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success":
                False,

            "error":
                "Internal server error."
        }), 500

    return error


# ============================================================
# STARTUP
# ============================================================

def startup():

    print()

    print(
        "=" * 60
    )

    print(
        " NEONSOCIAL AI"
    )

    print(
        " AI COMMAND CENTER"
    )

    print(
        " Built by SURESH REDDY"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f" Frontend : {FRONTEND_DIR}"
    )

    print(
        f" Templates: {TEMPLATES_DIR}"
    )

    print(
        f" Static   : {STATIC_DIR}"
    )

    print()

    print(
        f" Ollama URL   : {OLLAMA_URL}"
    )

    print(
        f" Ollama Model : {OLLAMA_MODEL}"
    )

    print()

    if ollama_available():

        print(
            " ✓ OLLAMA ONLINE"
        )

        print(
            f" ✓ MODEL: {OLLAMA_MODEL}"
        )

    else:

        print(
            " ⚠ OLLAMA NOT AVAILABLE"
        )

        print(
            " ✓ DEMO MODE ENABLED"
        )

    print()

    if os.getenv(
        "LINKEDIN_CLIENT_ID"
    ):

        print(
            " ✓ LINKEDIN CLIENT ID CONFIGURED"
        )

    else:

        print(
            " ⚠ LINKEDIN CLIENT ID NOT CONFIGURED"
        )

    print()

    stored_connection = (
        load_linkedin_connection()
    )

    if stored_connection:

        print(
            " ✓ LINKEDIN CONNECTION PERSISTED"
        )

        stored_profile = (
            stored_connection.get(
                "profile"
            )
        )

        if stored_profile:

            print(
                f" ✓ LINKEDIN USER: "
                f"{stored_profile.get('name')}"
            )

            print(
                f" ✓ LINKEDIN EMAIL: "
                f"{stored_profile.get('email')}"
            )

    else:

        print(
            " ⚠ LINKEDIN NOT CONNECTED"
        )

    print()

    print(
        " ✓ AUTOMATIC SCHEDULER CONFIGURED"
    )

    print(
        f" ✓ SCHEDULER INTERVAL: "
        f"{scheduler.interval} seconds"
    )

    print()

    print(
        f" ✓ Server: http://127.0.0.1:{PORT}"
    )

    print()

    print(
        "=" * 60
    )

    print()


# ============================================================
# MAIN
#
# app.run() MUST BE THE LAST OPERATION.
# ============================================================
@app.route("/google3f3cea12632babe5.html")
def google_verification():
    return "google-site-verification: google3f3cea12632babe5.html"
if __name__ == "__main__":

    startup()

    # --------------------------------------------------------
    # Start automatic scheduler BEFORE Flask.
    # --------------------------------------------------------

    scheduler.start()

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True,
        threaded=True,
        use_reloader=False
    )
    