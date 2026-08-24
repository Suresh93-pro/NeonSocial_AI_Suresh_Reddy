# ============================================================
# NEONSOCIAL AI
# AUTOMATIC POST SCHEDULER
#
# Human Approval
#       ↓
# Scheduled
#       ↓
# Scheduler detects due post
#       ↓
# LinkedIn OAuth token
#       ↓
# LinkedIn publish
#       ↓
# Published
# ============================================================

import threading
import time

from datetime import datetime, timezone


# ============================================================
# LINKEDIN API
# ============================================================

from backend.linkedin_api import (
    publish_text_post,
    LinkedInPublishError
)


# ============================================================
# SCHEDULER
# ============================================================

class NeonScheduler:

    def __init__(
    self,
    get_posts,
    update_post,
    get_access_token,
    get_linkedin_profile=None,
    log_activity=None,
    interval=10
):

        # ----------------------------------------------------
        # Database callbacks
        # ----------------------------------------------------

        self.get_posts = get_posts

        self.update_post = update_post

        self.get_access_token = (
            get_access_token
        )

        self.get_linkedin_profile = (
            get_linkedin_profile
        )

        self.log_activity = (
            log_activity
        )

        # ----------------------------------------------------
        # Scheduler configuration
        # ----------------------------------------------------

        self.interval = interval

        self.running = False

        self.thread = None

        self.lock = threading.Lock()


    # ========================================================
    # START
    # ========================================================

    def start(self):

        with self.lock:

            if self.running:

                return

            self.running = True

            self.thread = threading.Thread(

                target=self._worker,

                daemon=True,

                name="NeonSocial-Scheduler"

            )

            self.thread.start()

        print(
            "✓ NeonSocial scheduler started"
        )

        print(
            f"✓ Scheduler checking every "
            f"{self.interval} seconds"
        )


    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        with self.lock:

            self.running = False

        print(
            "✓ NeonSocial scheduler stopped"
        )


    # ========================================================
    # WORKER
    # ========================================================

    def _worker(self):

        while self.running:

            try:

                self.process_due_posts()

            except Exception as error:

                print(
                    "[SCHEDULER ERROR]",
                    error
                )

            # ------------------------------------------------
            # Wait before checking again
            # ------------------------------------------------

            time.sleep(
                self.interval
            )


    # ========================================================
    # PROCESS DUE POSTS
    # ========================================================

    def process_due_posts(self):

        posts = self.get_posts()

        if not posts:

            return

        now = datetime.now(
            timezone.utc
        )

        for post in posts:

            if not self.running:

                return

            # ------------------------------------------------
            # Only scheduled posts
            # ------------------------------------------------

            if post.get(
                "status"
            ) != "scheduled":

                continue

            # ------------------------------------------------
            # Get scheduled time
            # ------------------------------------------------

            scheduled_at = (
                post.get(
                    "scheduled_at"
                )
            )

            if not scheduled_at:

                continue

            # ------------------------------------------------
            # Parse scheduled time
            # ------------------------------------------------

            try:

                scheduled_time = (
                    self._parse_datetime(
                        scheduled_at
                    )
                )

            except Exception:

                self._mark_failed(

                    post,

                    "Invalid scheduled date/time."

                )

                continue

            # ------------------------------------------------
            # Not yet due
            # ------------------------------------------------

            if scheduled_time > now:

                continue

            # ------------------------------------------------
            # Post is due
            # ------------------------------------------------

            self.publish_post(
                post
            )


    # ========================================================
    # PUBLISH POST
    # ========================================================

    def publish_post(
        self,
        post
    ):

        session_id = post.get(
            "session_id"
        )

        if not session_id:

            print(
                "✕ Scheduled post has no session ID."
            )

            return

        print()
        print(
            "=" * 60
        )

        print(
            "NEONSOCIAL SCHEDULER"
        )

        print(
            f"Publishing post: {session_id}"
        )

        print(
            "=" * 60
        )


        # ====================================================
        # PREVENT DUPLICATE PUBLISHING
        # ====================================================

        try:

            current_post = None

            current_posts = (
                self.get_posts()
            )

            for item in current_posts:

                if item.get(
                    "session_id"
                ) == session_id:

                    current_post = item

                    break

            if current_post:

                if current_post.get(
                    "status"
                ) != "scheduled":

                    print(
                        f"Skipping {session_id}. "
                        f"Current status: "
                        f"{current_post.get('status')}"
                    )

                    return

        except Exception as error:

            print(
                "Unable to verify post status:",
                error
            )

            return


        # ====================================================
        # MARK AS PUBLISHING
        # ====================================================

        try:

            self.update_post(

                session_id,

                {
                    "status":
                        "publishing"
                }

            )

        except Exception as error:

            print(
                "Unable to mark post as publishing:",
                error
            )

            return


        try:

            # =================================================
            # GET LINKEDIN ACCESS TOKEN
            # =================================================

            access_token = (
                self.get_access_token()
            )

            if not access_token:

                raise LinkedInPublishError(
                    "LinkedIn is not connected."
                )


            # =================================================
            # GET LINKEDIN PROFILE
            # =================================================

            profile = (
                self.get_linkedin_profile()
            )

            if not profile:

                raise LinkedInPublishError(
                    "LinkedIn profile could not be retrieved."
                )


            # =================================================
            # GET LINKEDIN MEMBER ID
            # =================================================

            author_urn = (
                profile.get(
                    "author_urn"
                )
            )

            if not author_urn:

                profile_id = (
                    profile.get(
                        "id"
                    )
                )

                if profile_id:

                    # ------------------------------------------------
                    # If profile ID is already a URN
                    # ------------------------------------------------

                    if str(
                        profile_id
                    ).startswith(
                        "urn:li:"
                    ):

                        author_urn = (
                            profile_id
                        )

                    else:

                        author_urn = (
                            "urn:li:person:"
                            + str(profile_id)
                        )


            if not author_urn:

                raise LinkedInPublishError(
                    "LinkedIn member ID is missing."
                )


            # =================================================
            # POST CONTENT
            # =================================================

            content = str(
                post.get(
                    "content",
                    ""
                )
            ).strip()


            if not content:

                raise LinkedInPublishError(
                    "Post content is empty."
                )


            # =================================================
            # PUBLISH TO LINKEDIN
            # =================================================

            result = publish_text_post(

                access_token=
                    access_token,

                author_urn=
                    author_urn,

                content=
                    content

            )


            if not result:

                raise LinkedInPublishError(
                    "LinkedIn returned an empty response."
                )


            # =================================================
            # GET LINKEDIN POST ID
            # =================================================

            linkedin_post_id = (
                result.get(
                    "post_id"
                )
            )

            if not linkedin_post_id:

                linkedin_post_id = (
                    result.get(
                        "id"
                    )
                )


            # =================================================
            # PUBLISHED TIME
            # =================================================

            published_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )


            # =================================================
            # UPDATE DATABASE
            # =================================================

            self.update_post(

                session_id,

                {

                    "status":
                        "published",

                    "published_at":
                        published_at,

                    "linkedin_post_id":
                        linkedin_post_id,

                    "publish_error":
                        None

                }

            )


            # =================================================
            # ACTIVITY
            # =================================================

            self.log_activity(

                "Scheduled post published to LinkedIn",

                "publish"

            )


            # =================================================
            # SUCCESS
            # =================================================

            print()
            print(
                "✓ LINKEDIN POST PUBLISHED"
            )

            print(
                f"Session ID: {session_id}"
            )

            print(
                f"LinkedIn ID: "
                f"{linkedin_post_id}"
            )

            print()


        except Exception as error:

            self._mark_failed(

                post,

                str(error)

            )


    # ========================================================
    # FAILURE
    # ========================================================

    def _mark_failed(
        self,
        post,
        error_message
    ):

        session_id = post.get(
            "session_id"
        )

        if not session_id:

            print(
                "✕ Cannot mark post failed: "
                "session ID missing."
            )

            return


        try:

            self.update_post(

                session_id,

                {

                    "status":
                        "failed",

                    "publish_error":
                        error_message,

                    "failed_at":
                        datetime.now(
                            timezone.utc
                        ).isoformat()

                }

            )

        except Exception as error:

            print(
                "Unable to update failed post:",
                error
            )


        # ====================================================
        # ACTIVITY LOG
        # ====================================================

        try:

            self.log_activity(

                "Scheduled LinkedIn post failed",

                "error"

            )

        except Exception as error:

            print(
                "Unable to log scheduler failure:",
                error
            )


        # ====================================================
        # CONSOLE
        # ====================================================

        print()
        print(
            "✕ LINKEDIN POST FAILED"
        )

        print(
            f"Session ID: {session_id}"
        )

        print(
            f"Reason: {error_message}"
        )

        print()


    # ========================================================
    # DATETIME PARSER
    # ========================================================

    @staticmethod
    def _parse_datetime(
        value
    ):

        if not value:

            raise ValueError(
                "scheduled_at is empty"
            )


        value = str(
            value
        ).strip()


        # ====================================================
        # ISO FORMAT
        # ====================================================

        try:

            dt = datetime.fromisoformat(
                value
            )

        except ValueError:

            # Browser format:
            #
            # 2026-08-25 18:30
            #

            dt = datetime.strptime(

                value,

                "%Y-%m-%d %H:%M"

            )


        # ====================================================
        # NO TIMEZONE
        # ====================================================

        if dt.tzinfo is None:

            local_offset = (
                datetime.now()
                .astimezone()
                .utcoffset()
            )

            if local_offset is None:

                local_offset = (
                    timezone.utc.utcoffset(
                        datetime.now()
                    )
                )

            dt = dt.replace(

                tzinfo=timezone(
                    local_offset
                )

            )


        # ====================================================
        # CONVERT TO UTC
        # ====================================================

        return dt.astimezone(
            timezone.utc
        )


# ============================================================
# GLOBAL SCHEDULER
# ============================================================

scheduler = NeonScheduler(
    get_posts=lambda: [],
    update_post=lambda session_id, data: None,
    get_access_token=lambda: None,
    get_linkedin_profile=lambda: None,
    log_activity=lambda message, activity_type="info": None,
    interval=5
)