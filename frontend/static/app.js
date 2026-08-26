/* ============================================================
   NEONSOCIAL AI
   FRONTEND ENGINE
============================================================ */

"use strict";


// ============================================================
// STATE
// ============================================================

let currentSession = null;

let generatedContent = "";


// ============================================================
// DOM
// ============================================================

const $ = (selector) =>
    document.querySelector(selector);

const $$ = (selector) =>
    document.querySelectorAll(selector);


// ============================================================
// PARTICLES
// ============================================================

function createParticles() {

    const container = $("#particles");

    if (!container) return;

    for (let i = 0; i < 70; i++) {

        const particle =
            document.createElement("span");

        particle.className =
            "particle";

        particle.style.left =
            Math.random() * 100 + "%";

        particle.style.animationDuration =
            (7 + Math.random() * 15) + "s";

        particle.style.animationDelay =
            (-Math.random() * 20) + "s";

        particle.style.opacity =
            Math.random();

        if (Math.random() > .65) {

            particle.style.background =
                "#8b5cff";
        }

        container.appendChild(
            particle
        );
    }
}


// ============================================================
// CLOCK
// ============================================================

function updateClock() {

    const clock = $("#clock");

    if (!clock) return;

    const now = new Date();

    clock.textContent =
        now.toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );
}

setInterval(
    updateClock,
    1000
);

updateClock();


// ============================================================
// NAVIGATION
// ============================================================

function showPage(id) {

    $$(".page").forEach(
        page => {
            page.classList.remove(
                "active-page"
            );
        }
    );

    const page =
        document.getElementById(id);

    if (page) {

        page.classList.add(
            "active-page"
        );
    }

    $$(".nav-item").forEach(
        item => {

            item.classList.toggle(
                "active",
                item.dataset.target === id
            );

        }
    );

    const names = {
        dashboard: "DASHBOARD",
        create: "CREATE",
        approval: "APPROVAL",
        schedule: "SCHEDULE",
        activity: "ACTIVITY",
        ai: "NEON AI"
    };

    const pageName =
        $("#pageName");

    if (pageName) {

        pageName.textContent =
            names[id] || "DASHBOARD";
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


$$("[data-target]").forEach(
    button => {

        button.addEventListener(
            "click",
            () => {

                const target =
                    button.dataset.target;

                if (target) {
                    showPage(target);
                }

            }
        );

    }
);


// ============================================================
// API HELPER
// ============================================================

async function api(
    url,
    options = {}
) {

    const response =
        await fetch(
            url,
            {
                headers: {
                    "Content-Type":
                        "application/json"
                },
                ...options
            }
        );

    let data;

    try {

        data =
            await response.json();

    } catch {

        data = {
            success: false,
            error: "Invalid server response."
        };
    }

    if (!response.ok) {

        throw new Error(
            data.error ||
            "Server error"
        );
    }

    return data;
}


// ============================================================
// HEALTH
// ============================================================

async function checkHealth() {

    try {

        const data =
            await api("/health");

        const engine =
            $("#engineName");

        const sideStatus =
            $("#sideAiStatus");

        const dot =
            $("#sideStatusDot");

        const coreEngine =
            $("#coreEngine");

        if (data.ollama) {

            if (engine)
                engine.textContent =
                    "OLLAMA";

            if (sideStatus)
                sideStatus.textContent =
                    "ONLINE • OLLAMA";

            if (coreEngine)
                coreEngine.textContent =
                    "99.8% • OLLAMA LIVE";

            if (dot)
                dot.style.background =
                    "#36ff9a";

        } else {

            if (engine)
                engine.textContent =
                    "DEMO";

            if (sideStatus)
                sideStatus.textContent =
                    "ONLINE • DEMO";

            if (coreEngine)
                coreEngine.textContent =
                    "DEMO • READY";

        }

    } catch (error) {

        console.error(
            "Health:",
            error
        );

        const engine =
            $("#engineName");

        if (engine) {

            engine.textContent =
                "OFFLINE";
        }
    }
}


// ============================================================
// COUNTER ANIMATION
// ============================================================

function animateNumber(
    element,
    target
) {

    if (!element) return;

    target =
        Number(target) || 0;

    const start =
        Number(element.textContent) || 0;

    const duration = 500;

    const startTime =
        performance.now();

    function frame(now) {

        const progress =
            Math.min(
                (now - startTime) /
                duration,
                1
            );

        const eased =
            1 -
            Math.pow(
                1 - progress,
                3
            );

        element.textContent =
            Math.round(
                start +
                (target - start) *
                eased
            );

        if (progress < 1) {

            requestAnimationFrame(
                frame
            );
        }
    }

    requestAnimationFrame(
        frame
    );
}


// ============================================================
// DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const data =
            await api(
                "/api/dashboard"
            );

        animateNumber(
            $("#totalPosts"),
            data.total
        );

        animateNumber(
            $("#waitingPosts"),
            data.waiting
        );

        animateNumber(
            $("#approvedPosts"),
            data.approved
        );

        animateNumber(
            $("#scheduledPosts"),
            data.scheduled
        );

        animateNumber(
            $("#publishedPosts"),
            data.published
        );

        const badge =
            $("#approvalBadge");

        if (badge) {

            badge.textContent =
                data.waiting;
        }

        renderMiniActivity(
            data.activity || []
        );

        renderActivity(
            data.activity || []
        );

    } catch (error) {

        console.error(
            "Dashboard:",
            error
        );
    }
}


// ============================================================
// ACTIVITY
// ============================================================

function renderMiniActivity(
    events
) {

    const box =
        $("#miniActivity");

    if (!box) return;

    if (!events.length) {

        box.innerHTML = `
            <div class="empty-event">
                <span>⌁</span>
                System ready
            </div>
        `;

        return;
    }

    box.innerHTML =
        events
            .slice(0, 5)
            .map(
                event => `
                    <div class="activity-event">
                        <span class="event-dot"></span>

                        <p>
                            ${escapeHtml(
                                event.message
                            )}
                        </p>

                        <time>
                            ${escapeHtml(
                                event.time || ""
                            )}
                        </time>
                    </div>
                `
            )
            .join("");
}


function renderActivity(
    events
) {

    const box =
        $("#activityList");

    if (!box) return;

    if (!events.length) {

        box.innerHTML = `
            <div class="empty-state">
                <div>⌁</div>
                <h3>Waiting for activity</h3>
                <p>
                    Your workflow events will appear here.
                </p>
            </div>
        `;

        return;
    }

    box.innerHTML =
        events
            .map(
                event => `
                    <div class="activity-event">
                        <span class="event-dot"></span>

                        <p>
                            ${escapeHtml(
                                event.message
                            )}
                        </p>

                        <time>
                            ${escapeHtml(
                                event.time || ""
                            )}
                        </time>
                    </div>
                `
            )
            .join("");
}


// ============================================================
// CREATE
// ============================================================

const topic =
    $("#topic");

if (topic) {

    topic.addEventListener(
        "input",
        () => {

            const count =
                $("#charCount");

            if (count) {

                count.textContent =
                    `${topic.value.length} / 1000`;
            }

        }
    );
}


const generateBtn =
    $("#generateBtn");

if (generateBtn) {

    generateBtn.addEventListener(
        "click",
        generatePost
    );
}


async function generatePost() {

    const topicValue =
        $("#topic").value.trim();

    const platform =
        $("#platform").value;

    const tone =
        $("#tone").value;

    if (!topicValue) {

        $("#topic").focus();

        $("#topic").style.borderColor =
            "#ff35d4";

        setTimeout(
            () => {
                $("#topic").style.borderColor =
                    "";
            },
            900
        );

        return;
    }

    const button =
        $("#generateBtn");

    button.disabled = true;

    button.innerHTML =
        `
        <span>◌</span>
        NEON AI IS THINKING...
        <b>...</b>
        `;

    try {

        const data =
            await api(
                "/api/generate",
                {
                    method: "POST",

                    body: JSON.stringify({
                        topic:
                            topicValue,

                        platform:
                            platform,

                        tone:
                            tone
                    })
                }
            );

        currentSession =
            data.session_id;

        generatedContent =
            data.content;

        showGeneratedPost(
            data.content
        );

        loadDashboard();

        renderApproval(
            data
        );

        showPage("create");

    } catch (error) {

        alert(
            error.message
        );

    } finally {

        button.disabled = false;

        button.innerHTML =
            `
            <span>✦</span>
            GENERATE WITH NEON AI
            <b>→</b>
            `;
    }
}


// ============================================================
// GENERATED POST
// ============================================================

function showGeneratedPost(
    content
) {

    const box =
        $("#previewContent");

    const status =
        $("#previewStatus");

    if (!box) return;

    if (status) {

        status.textContent =
            "READY";
    }

    box.innerHTML = `
        <div
            class="generated-post"
            id="generatedPost"
        ></div>
    `;

    typeText(
        $("#generatedPost"),
        content,
        4
    );
}


// ============================================================
// TYPING
// ============================================================

function typeText(
    element,
    text,
    speed = 8
) {

    if (!element) return;

    element.textContent = "";

    let index = 0;

    function next() {

        if (index >= text.length) {
            return;
        }

        element.textContent +=
            text[index];

        index++;

        setTimeout(
            next,
            speed
        );
    }

    next();
}


// ============================================================
// APPROVAL
// ============================================================

function renderApproval(
    data
) {

    const box =
        $("#approvalContent");

    if (!box) return;

    box.innerHTML = `
        <div class="approval-post">

            <div class="post-meta">

                <span>
                    ${escapeHtml(
                        data.platform
                    )}
                </span>

                <span>
                    ${escapeHtml(
                        data.tone
                    )}
                </span>

                <span>
                    WAITING APPROVAL
                </span>

            </div>

            <div class="post-text">
                ${escapeHtml(
                    data.content
                )}
            </div>

            <div class="preview-actions"
                 style="margin-top:20px">

                <button
                    id="approvalApprove"
                >
                    ✓ APPROVE
                </button>

                <button
                    id="approvalReject"
                >
                    ✕ REJECT
                </button>

            </div>

        </div>
    `;

    $("#approvalApprove")
        ?.addEventListener(
            "click",
            approvePost
        );

    $("#approvalReject")
        ?.addEventListener(
            "click",
            rejectPost
        );
}


// ============================================================
// APPROVE
// ============================================================

$("#approveBtn")
    ?.addEventListener(
        "click",
        approvePost
    );


async function approvePost() {

    if (!currentSession) {

        return;
    }

    try {

        await api(
            "/api/approve",
            {
                method: "POST",

                body: JSON.stringify({
                    session_id:
                        currentSession
                })
            }
        );

        $("#previewStatus").textContent =
            "APPROVED";

        loadDashboard();

        alert(
            "Post approved successfully."
        );

    } catch (error) {

        alert(
            error.message
        );
    }
}


// ============================================================
// REJECT
// ============================================================

$("#rejectBtn")
    ?.addEventListener(
        "click",
        rejectPost
    );


async function rejectPost() {

    if (!currentSession) {

        return;
    }

    try {

        await api(
            "/api/reject",
            {
                method: "POST",

                body: JSON.stringify({
                    session_id:
                        currentSession
                })
            }
        );

        $("#previewStatus").textContent =
            "REJECTED";

        loadDashboard();

        alert(
            "Post rejected."
        );

    } catch (error) {

        alert(
            error.message
        );
    }
}


// ============================================================
// COPY
// ============================================================

$("#copyBtn")
    ?.addEventListener(
        "click",
        async () => {

            if (!generatedContent)
                return;

            try {

                await navigator.clipboard.writeText(
                    generatedContent
                );

                $("#copyBtn").textContent =
                    "✓ COPIED";

                setTimeout(
                    () => {
                        $("#copyBtn").textContent =
                            "⧉ COPY";
                    },
                    1500
                );

            } catch {

                alert(
                    "Copy failed."
                );
            }
        }
    );


// ============================================================
// SCHEDULE
// ============================================================

$("#scheduleBtn")
    ?.addEventListener(
        "click",
        schedulePost
    );


async function schedulePost() {

    if (!currentSession) {

        alert(
            "Generate and approve a post first."
        );

        return;
    }

    const date =
        $("#scheduleDate").value;

    const time =
        $("#scheduleTime").value;

    if (!date || !time) {

        alert(
            "Choose date and time."
        );

        return;
    }

    try {

        const data =
            await api(
                "/api/schedule",
                {
                    method: "POST",

                    body: JSON.stringify({
                        session_id:
                            currentSession,

                        date:
                            date,

                        time:
                            time
                    })
                }
            );

        $("#scheduleMessage").textContent =
            `✓ Scheduled for ${data.scheduled_at}`;

        loadDashboard();

    } catch (error) {

        alert(
            error.message
        );
    }
}


// ============================================================
// AI CHAT
// ============================================================

$("#chatSend")
    ?.addEventListener(
        "click",
        sendChat
    );


$("#chatInput")
    ?.addEventListener(
        "keydown",
        event => {

            if (event.key === "Enter") {

                sendChat();
            }

        }
    );


async function sendChat(
    forcedMessage = null
) {

    const input =
        $("#chatInput");

    const message =
        forcedMessage ||
        input.value.trim();

    if (!message)
        return;

    if (!forcedMessage)
        input.value = "";

    addChatMessage(
        message,
        "user"
    );

    const typing =
        addTypingMessage();

    try {

        const data =
            await api(
                "/api/ai-chat",
                {
                    method: "POST",

                    body: JSON.stringify({
                        message:
                            message
                    })
                }
            );

        typing.remove();

        addChatMessage(
            data.response,
            "ai",
            true
        );

        loadDashboard();

    } catch (error) {

        typing.remove();

        addChatMessage(
            "Neon AI is temporarily unavailable.",
            "ai"
        );

        console.error(
            error
        );
    }
}


function addChatMessage(
    message,
    type,
    animate = false
) {

    const container =
        $("#chatMessages");

    const row =
        document.createElement("div");

    row.className =
        `chat-message ${type}`;

    const avatar =
        document.createElement("div");

    avatar.className =
        "chat-avatar";

    avatar.textContent =
        type === "ai"
            ? "N"
            : "SR";

    const bubble =
        document.createElement("div");

    bubble.className =
        "bubble";

    row.appendChild(
        avatar
    );

    row.appendChild(
        bubble
    );

    container.appendChild(
        row
    );

    if (animate) {

        typeText(
            bubble,
            message,
            7
        );

    } else {

        bubble.textContent =
            message;
    }

    container.scrollTop =
        container.scrollHeight;
}


function addTypingMessage() {

    const container =
        $("#chatMessages");

    const row =
        document.createElement("div");

    row.className =
        "chat-message ai";

    row.innerHTML = `
        <div class="chat-avatar">
            N
        </div>

        <div class="bubble">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    container.appendChild(
        row
    );

    container.scrollTop =
        container.scrollHeight;

    return row;
}


// ============================================================
// QUICK CHAT
// ============================================================

$$(".quick-chat").forEach(
    button => {

        button.addEventListener(
            "click",
            () => {

                const message =
                    button.dataset.message;

                if (message) {

                    showPage("ai");

                    sendChat(
                        message
                    );
                }

            }
        );

    }
);


// ============================================================
// LINKEDIN
// ============================================================

$("#linkedinBtn")
    ?.addEventListener(
        "click",
        async () => {

            try {

                const data =
                    await api(
                        "/api/linkedin/connect"
                    );

                if (
                    data.success &&
                    data.redirect
                ) {

                    // Redirect user to LinkedIn OAuth
                    window.location.href =
                        data.redirect;

                    return;
                }

                alert(
                    data.error ||
                    data.message ||
                    "LinkedIn connection failed."
                );

            } catch (error) {

                console.error(
                    "LinkedIn connection error:",
                    error
                );

                alert(
                    error.message ||
                    "Unable to connect to LinkedIn."
                );
            }
        }
    );

// ============================================================
// LINKEDIN CONNECTION STATUS
// ============================================================

async function checkLinkedInStatus() {

    const status =
        document.getElementById(
            "linkedinStatus"
        );

    const button =
        document.getElementById(
            "linkedinBtn"
        );

    const profileName =
        document.getElementById(
            "linkedinProfileName"
        );

    if (!status) {
        return;
    }

    try {

        status.textContent =
            "Checking...";


        const response =
            await fetch(
                "/api/linkedin/status",
                {
                    method: "GET",

                    credentials:
                        "include",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                "LinkedIn status request failed."
            );

        }


        const data =
            await response.json();


        if (
            data.success === true &&
            data.connected === true
        ) {

            status.textContent =
                "CONNECTED ✓";


            if (button) {

                button.textContent =
                    "CONNECTED ✓";

                button.disabled =
                    true;

                button.style.cursor =
                    "default";

            }


            if (
                profileName &&
                data.profile
            ) {

                const name =
                    data.profile.name ||
                    data.profile.first_name ||
                    "";

                if (name) {

                    profileName.textContent =
                        name;

                    profileName.style.display =
                        "block";

                }

            }

            return;
        }


        status.textContent =
            "Not connected";


        if (button) {

            button.textContent =
                "CONNECT ↗";

            button.disabled =
                false;

        }


        if (profileName) {

            profileName.textContent =
                "";

            profileName.style.display =
                "none";

        }

    }
    catch (error) {

        console.error(
            "LinkedIn status error:",
            error
        );

        status.textContent =
            "Not connected";

        if (button) {

            button.textContent =
                "CONNECT ↗";

            button.disabled =
                false;

        }

    }

}    


// ============================================================
// REFRESH
// ============================================================

$("#refreshBtn")
    ?.addEventListener(
        "click",
        async () => {

            await checkHealth();

            await loadDashboard();

        }
    );


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(
    value
) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


// ============================================================
// STARTUP
// ============================================================
async function startup() {

    createParticles();

    checkHealth();

    loadDashboard();

    checkLinkedInStatus();

    setInterval(
        checkLinkedInStatus,
        5000
    );

}

startup();
// ============================================================
// PROFILE MENU + LOGOUT
// ============================================================

(function initProfileMenu() {

    const profileMenu =
        document.getElementById("profileMenu");

    const profileTrigger =
        document.getElementById("profileTrigger");

    const profileDropdown =
        document.getElementById("profileDropdown");

    const logoutButton =
        document.getElementById("logoutButton");

    if (!profileMenu || !profileTrigger || !profileDropdown) {

        console.warn(
            "NeonSocial profile menu elements not found."
        );

        return;
    }


    // ========================================================
    // OPEN / CLOSE PROFILE DROPDOWN
    // ========================================================

    profileTrigger.addEventListener(
        "click",
        function (event) {

            event.preventDefault();
            event.stopPropagation();

            profileDropdown.classList.toggle(
                "show"
            );

        }
    );


    // ========================================================
    // CLICK OUTSIDE = CLOSE DROPDOWN
    // ========================================================

    document.addEventListener(
        "click",
        function (event) {

            if (
                !profileMenu.contains(
                    event.target
                )
            ) {

                profileDropdown.classList.remove(
                    "show"
                );

            }

        }
    );


    // ========================================================
    // ESC KEY = CLOSE DROPDOWN
    // ========================================================

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Escape") {

                profileDropdown.classList.remove(
                    "show"
                );

            }

        }
    );


    // ========================================================
    // LOGOUT
    // ========================================================

    if (logoutButton) {

        logoutButton.addEventListener(
            "click",
            async function (event) {

                event.preventDefault();

                logoutButton.disabled = true;

                logoutButton.innerHTML = `
                    <span class="menu-icon">◌</span>
                    <span>Logging out...</span>
                `;


                try {

                    const response =
                        await fetch(
                            "/api/auth/logout",
                            {
                                method: "POST",

                                credentials:
                                    "include",

                                headers: {
                                    "Accept":
                                        "application/json"
                                }
                            }
                        );


                    let data = {};

                    try {

                        data =
                            await response.json();

                    } catch {

                        data = {};

                    }


                    if (
                        response.ok &&
                        data.success !== false
                    ) {

                        /*
                         * Clear the frontend state.
                         */

                        currentSession =
                            null;

                        generatedContent =
                            "";


                        /*
                         * Close dropdown.
                         */

                        profileDropdown.classList.remove(
                            "show"
                        );


                        /*
                         * Return to login page.
                         */

                        window.location.href =
                            "/";

                        return;

                    }


                    throw new Error(
                        data.error ||
                        "Logout failed."
                    );


                } catch (error) {

                    console.error(
                        "Logout error:",
                        error
                    );

                    alert(
                        error.message ||
                        "Unable to logout."
                    );


                    logoutButton.disabled =
                        false;

                    logoutButton.innerHTML = `
                        <span class="menu-icon">↪</span>
                        <span>Logout</span>
                    `;

                }

            }
        );

    }

})();
/* ============================================================
   NEONSOCIAL LOGIN SYSTEM
   REAL BACKEND AUTHENTICATION
   ============================================================ */

(function initNeonSocialLogin() {

    const loginPage =
        document.getElementById("loginPage");

    const loginButton =
        document.getElementById("loginButton");

    const username =
        document.getElementById("loginUsername");

    const password =
        document.getElementById("loginPassword");

    const loginError =
        document.getElementById("loginError");

    /*
     * If this page does not contain the login elements,
     * do nothing.
     */
    if (
        !loginPage ||
        !loginButton ||
        !username ||
        !password
    ) {
        return;
    }


    /* ========================================================
       CHECK PREVIOUS LOGIN
       ======================================================== */

    async function checkAuthentication() {

    try {

        const response =
            await fetch(
                "/api/auth/me",
                {
                    method: "GET",

                    credentials:
                        "include",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        if (!response.ok) {

            document.body.classList.remove(
                "authenticated"
            );

            loginPage.classList.remove(
                "hidden"
            );

            return;
        }


        const data =
            await response.json();


        if (
            data.success === true &&
            data.authenticated === true
        ) {

            /*
             * USER IS LOGGED IN
             */

            document.body.classList.add(
                "authenticated"
            );

            loginPage.classList.add(
                "hidden"
            );


            /*
             * Make absolutely sure
             * profile dropdown is closed.
             */

            const dropdown =
                document.getElementById(
                    "profileDropdown"
                );

            if (dropdown) {

                dropdown.classList.remove(
                    "profile-dropdown-open"
                );

            }

        } else {

            /*
             * USER IS LOGGED OUT
             */

            document.body.classList.remove(
                "authenticated"
            );

            loginPage.classList.remove(
                "hidden"
            );


            /*
             * Close profile dropdown.
             */

            const dropdown =
                document.getElementById(
                    "profileDropdown"
                );

            if (dropdown) {

                dropdown.classList.remove(
                    "profile-dropdown-open"
                );

            }

        }

    } catch (error) {

        console.warn(
            "Authentication check failed:",
            error
        );


        /*
         * If authentication cannot be verified,
         * show login screen.
         */

        document.body.classList.remove(
            "authenticated"
        );

        loginPage.classList.remove(
            "hidden"
        );

    }
}

    /* ========================================================
       LOGIN
       ======================================================== */

    async function performLogin() {

        const email =
            username.value.trim();

        const accessKey =
            password.value;

        loginError.textContent = "";

        loginError.classList.remove(
            "show"
        );


        /* -----------------------------------------------
           VALIDATION
           ----------------------------------------------- */

        if (!email) {

            loginError.textContent =
                "Please enter your email.";

            loginError.classList.add(
                "show"
            );

            username.focus();

            return;
        }


        if (!accessKey) {

            loginError.textContent =
                "Please enter your access key.";

            loginError.classList.add(
                "show"
            );

            password.focus();

            return;
        }


        /* -----------------------------------------------
           BUTTON LOADING STATE
           ----------------------------------------------- */

        const originalButtonHTML =
            loginButton.innerHTML;

        loginButton.innerHTML =
            "AUTHENTICATING...";

        loginButton.disabled = true;


        try {

            /* ============================================
               REAL BACKEND LOGIN
               ============================================ */

            const response = await fetch(
                "/api/auth/login",
                {
                    method: "POST",

                    credentials: "include",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body: JSON.stringify({

                        email: email,

                        password: accessKey
                    })
                }
            );


            let data = {};

            try {

                data =
                    await response.json();

            } catch (jsonError) {

                data = {};
            }


            /* ============================================
               SUCCESS
               ============================================ */

            if (
                response.ok &&
                data.success === true
            ) {

                loginError.textContent = "";

                loginError.classList.remove(
                    "show"
                );


                /*
                 * Keep your existing interface.
                 * Only hide the login screen.
                 */

                loginPage.classList.add(
                    "hidden"
                );

                document.body.classList.add(
                    "authenticated"
                );


                /*
                 * Refresh the application so that
                 * authenticated backend state is loaded.
                 */

                setTimeout(function () {

                    window.location.href =
                        "/";

                }, 250);


                return;
            }


            /* ============================================
               BACKEND ERROR
               ============================================ */

            let errorMessage =
                "Login failed.";


            if (
                data &&
                typeof data.error === "string" &&
                data.error.trim()
            ) {

                errorMessage =
                    data.error;
            }


            loginError.textContent =
                errorMessage;

            loginError.classList.add(
                "show"
            );


        } catch (error) {

            console.error(
                "Login error:",
                error
            );


            loginError.textContent =
                "Unable to connect to NeonSocial AI server.";

            loginError.classList.add(
                "show"
            );


        } finally {

            loginButton.innerHTML =
                originalButtonHTML;

            loginButton.disabled = false;
        }
    }


    /* ========================================================
       LOGIN BUTTON
       ======================================================== */

    loginButton.addEventListener(
        "click",
        performLogin
    );


    /* ========================================================
       ENTER KEY
       ======================================================== */

    username.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                performLogin();
            }
        }
    );


    password.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                performLogin();
            }
        }
    );


    /* ========================================================
       CHECK AUTHENTICATION ON LOAD
       ======================================================== */

    checkAuthentication();

})();
/* ============================================================
   NEONSOCIAL PROFILE DROPDOWN
   LOGOUT SYSTEM
   ADDITION ONLY
============================================================ */

(function initProfileDropdown() {

    const profile =
        document.querySelector(".profile");

    if (!profile) {
        return;
    }


    /* ========================================================
       GET EXISTING PROFILE ELEMENTS
    ======================================================== */

    const avatar =
        profile.querySelector(".profile-avatar");

    const nameElement =
        profile.querySelector("span");


    /* ========================================================
       CREATE PROFILE BUTTON
       WITHOUT CHANGING EXISTING HTML
    ======================================================== */

    const profileTrigger =
        document.createElement("button");

    profileTrigger.type =
        "button";

    profileTrigger.className =
        "profile-trigger";


    /* Move existing profile content into trigger */

    if (avatar) {

        profile.removeChild(avatar);

        profileTrigger.appendChild(
            avatar
        );
    }


    if (nameElement) {

        profile.removeChild(nameElement);

        profileTrigger.appendChild(
            nameElement
        );
    }


    const arrow =
        document.createElement("span");

    arrow.className =
        "profile-arrow";

    arrow.textContent =
        "⌄";

    profileTrigger.appendChild(
        arrow
    );


    profile.appendChild(
        profileTrigger
    );


    /* ========================================================
       CREATE DROPDOWN
    ======================================================== */

    const dropdown =
        document.createElement("div");

    dropdown.className =
        "profile-dropdown";


    dropdown.innerHTML = `

        <div class="profile-dropdown-header">

            <div
                class="profile-dropdown-avatar"
                id="profileDropdownAvatar"
            >
                SR
            </div>

            <div>

                <div
                    class="profile-dropdown-name"
                    id="profileDropdownName"
                >
                    Suresh
                </div>

                <div
                    class="profile-dropdown-email"
                    id="profileDropdownEmail"
                >
                    Loading...
                </div>

            </div>

        </div>


        <div class="profile-divider"></div>


        <button
            type="button"
            class="profile-menu-item logout-item"
            id="logoutButton"
        >

            <span class="menu-icon">
                ⇥
            </span>

            <span>
                LOGOUT
            </span>

        </button>

    `;


    profile.appendChild(
        dropdown
    );


    /* ========================================================
       TOGGLE DROPDOWN
    ======================================================== */

    profileTrigger.addEventListener(
        "click",
        function(event) {

            event.stopPropagation();

            profile.classList.toggle(
                "open"
            );

        }
    );


    /* ========================================================
       CLOSE WHEN CLICKING OUTSIDE
    ======================================================== */

    document.addEventListener(
        "click",
        function(event) {

            if (
                !profile.contains(
                    event.target
                )
            ) {

                profile.classList.remove(
                    "open"
                );

            }

        }
    );


    /* ========================================================
       ESC KEY
    ======================================================== */

    document.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Escape"
            ) {

                profile.classList.remove(
                    "open"
                );

            }

        }
    );


    /* ========================================================
       LOAD CURRENT USER
    ======================================================== */

    async function loadCurrentUser() {

        try {

            const response =
                await fetch(
                    "/api/auth/me",
                    {
                        method: "GET",

                        credentials:
                            "include",

                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );


            if (!response.ok) {
                return;
            }


            const data =
                await response.json();


            if (
                data.success === true &&
                data.authenticated === true &&
                data.user
            ) {

                const user =
                    data.user;


                const userName =
                    user.name ||
                    "Suresh";


                const userEmail =
                    user.email ||
                    "";


                /* ----------------------------------------
                   TOP PROFILE NAME
                ---------------------------------------- */

                if (nameElement) {

                    nameElement.textContent =
                        userName;

                }


                /* ----------------------------------------
                   PROFILE DROPDOWN NAME
                ---------------------------------------- */

                const dropdownName =
                    document.getElementById(
                        "profileDropdownName"
                    );

                if (dropdownName) {

                    dropdownName.textContent =
                        userName;

                }


                /* ----------------------------------------
                   PROFILE EMAIL
                ---------------------------------------- */

                const dropdownEmail =
                    document.getElementById(
                        "profileDropdownEmail"
                    );

                if (dropdownEmail) {

                    dropdownEmail.textContent =
                        userEmail;

                }


                /* ----------------------------------------
                   INITIALS
                ---------------------------------------- */

                const initials =
                    getInitials(
                        userName
                    );


                if (avatar) {

                    avatar.textContent =
                        initials;

                }


                const dropdownAvatar =
                    document.getElementById(
                        "profileDropdownAvatar"
                    );

                if (dropdownAvatar) {

                    dropdownAvatar.textContent =
                        initials;

                }

            }

        } catch (error) {

            console.warn(
                "Unable to load current user:",
                error
            );

        }

    }


    /* ========================================================
       GET INITIALS
    ======================================================== */

    function getInitials(
        name
    ) {

        if (!name) {

            return "SR";

        }


        const parts =
            name
                .trim()
                .split(/\s+/);


        if (parts.length === 1) {

            return parts[0]
                .substring(0, 2)
                .toUpperCase();

        }


        return (
            parts[0][0] +
            parts[parts.length - 1][0]
        ).toUpperCase();

    }


    /* ========================================================
       LOGOUT
    ======================================================== */

    const logoutButton =
        document.getElementById(
            "logoutButton"
        );


    if (logoutButton) {

        logoutButton.addEventListener(
            "click",
            async function(event) {

                event.preventDefault();

                event.stopPropagation();


                /* ----------------------------------------
                   LOADING STATE
                ---------------------------------------- */

                const originalHTML =
                    logoutButton.innerHTML;


                logoutButton.disabled =
                    true;


                logoutButton.innerHTML = `
                    <span class="menu-icon">
                        ◌
                    </span>

                    <span>
                        LOGGING OUT...
                    </span>
                `;


                try {

                    const response =
                        await fetch(
                            "/api/auth/logout",
                            {
                                method: "POST",

                                credentials:
                                    "include",

                                headers: {
                                    "Accept":
                                        "application/json",

                                    "Content-Type":
                                        "application/json"
                                }
                            }
                        );


                    let data = {};

                    try {

                        data =
                            await response.json();

                    } catch {

                        data = {};

                    }


                    /* ------------------------------------
                       SUCCESS
                    ------------------------------------ */

                    if (
                        response.ok &&
                        data.success === true
                    ) {

                        profile.classList.remove(
                            "open"
                        );


                        /*
                         * Go back to login page.
                         */

                        window.location.href =
                            "/login";


                        return;

                    }


                    /* ------------------------------------
                       SERVER ERROR
                    ------------------------------------ */

                    alert(
                        data.error ||
                        "Logout failed. Please try again."
                    );


                } catch (error) {

                    console.error(
                        "Logout error:",
                        error
                    );


                    alert(
                        "Unable to connect to NeonSocial AI server."
                    );


                } finally {

                    logoutButton.disabled =
                        false;

                    logoutButton.innerHTML =
                        originalHTML;

                }

            }
        );

    }


    /* ========================================================
       INITIAL LOAD
    ======================================================== */

    loadCurrentUser();

})();
/* ============================================================
   PROFILE DROPDOWN + LOGOUT
============================================================ */

(function initProfileMenu() {

    const profileMenu =
        document.getElementById(
            "profileMenu"
        );

    const profileTrigger =
        document.getElementById(
            "profileTrigger"
        );

    const profileDropdown =
        document.getElementById(
            "profileDropdown"
        );

    const logoutButton =
        document.getElementById(
            "logoutButton"
        );

    const profileName =
        document.getElementById(
            "profileName"
        );

    const profileAvatar =
        document.getElementById(
            "profileAvatar"
        );

    const dropdownName =
        document.getElementById(
            "dropdownName"
        );

    const dropdownEmail =
        document.getElementById(
            "dropdownEmail"
        );

    const dropdownAvatar =
        document.getElementById(
            "dropdownAvatar"
        );


    /*
     * STOP IF PROFILE DOES NOT EXIST
     */

    if (
        !profileMenu ||
        !profileTrigger ||
        !profileDropdown
    ) {

        console.warn(
            "NeonSocial: Profile menu elements not found."
        );

        return;
    }


    /* ========================================================
       OPEN / CLOSE PROFILE
    ======================================================== */

    profileTrigger.addEventListener(
        "click",
        function(event) {

            event.preventDefault();

            event.stopPropagation();

            profileMenu.classList.toggle(
                "open"
            );

        }
    );


    /* ========================================================
       CLOSE WHEN CLICKING OUTSIDE
    ======================================================== */

    document.addEventListener(
        "click",
        function(event) {

            if (
                !profileMenu.contains(
                    event.target
                )
            ) {

                profileMenu.classList.remove(
                    "open"
                );

            }

        }
    );


    /* ========================================================
       LOAD CURRENT USER
    ======================================================== */

    async function loadProfileUser() {

        try {

            const response =
                await fetch(
                    "/api/auth/me",
                    {
                        method: "GET",

                        credentials:
                            "include",

                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );


            if (!response.ok) {

                return;
            }


            const data =
                await response.json();


            console.log(
                "NeonSocial auth user:",
                data
            );


            if (
                data.success === true &&
                data.authenticated === true
            ) {

                const user =
                    data.user || {};


                const name =
                    user.name ||
                    user.full_name ||
                    user.username ||
                    "User";


                const email =
                    user.email ||
                    "";


                /*
                 * INITIALS
                 */

                const initials =
                    name
                        .trim()
                        .split(/\s+/)
                        .map(
                            part =>
                                part
                                    .charAt(0)
                                    .toUpperCase()
                        )
                        .slice(0, 2)
                        .join("");


                /*
                 * TOP PROFILE
                 */

                if (profileName) {

                    profileName.textContent =
                        name;

                }


                if (profileAvatar) {

                    profileAvatar.textContent =
                        initials || "U";

                }


                /*
                 * DROPDOWN PROFILE
                 */

                if (dropdownName) {

                    dropdownName.textContent =
                        name;

                }


                if (dropdownEmail) {

                    dropdownEmail.textContent =
                        email || "Authenticated user";

                }


                if (dropdownAvatar) {

                    dropdownAvatar.textContent =
                        initials || "U";

                }

            }

        }
        catch (error) {

            console.error(
                "Profile loading error:",
                error
            );

        }

    }


    /* ========================================================
       LOGOUT
    ======================================================== */

    if (logoutButton) {

        logoutButton.addEventListener(
            "click",
            async function(event) {

                event.preventDefault();

                event.stopPropagation();


                const originalHTML =
                    logoutButton.innerHTML;


                logoutButton.disabled =
                    true;


                logoutButton.innerHTML =
                    `
                    <span class="menu-icon">
                        ◌
                    </span>

                    <span>
                        LOGGING OUT...
                    </span>
                    `;


                try {

                    const response =
                        await fetch(
                            "/api/auth/logout",
                            {
                                method: "POST",

                                credentials:
                                    "include",

                                headers: {
                                    "Accept":
                                        "application/json"
                                }
                            }
                        );


                    let data = {};

                    try {

                        data =
                            await response.json();

                    }
                    catch {

                        data = {};

                    }


                    if (
                        response.ok &&
                        (
                            data.success === true ||
                            response.status === 200
                        )
                    ) {

                        /*
                         * CLOSE MENU
                         */

                        profileMenu.classList.remove(
                            "open"
                        );


                        /*
                         * GO TO LOGIN
                         */

                        window.location.href =
                            "/";

                        return;
                    }


                    throw new Error(
                        data.error ||
                        "Logout failed."
                    );

                }
                catch (error) {

                    console.error(
                        "Logout error:",
                        error
                    );


                    alert(
                        error.message ||
                        "Unable to logout."
                    );


                    logoutButton.disabled =
                        false;

                    logoutButton.innerHTML =
                        originalHTML;

                }

            }
        );

    }


    /* ========================================================
       LOAD USER
    ======================================================== */

    loadProfileUser();

})();

/* ============================================================
   NEONSOCIAL AI
   FINAL AUTHENTICATION FIX
   ============================================================

   IMPORTANT:

   THIS BLOCK IS ADDED TO THE ORIGINAL APP.JS.

   DO NOT DELETE THE EXISTING CODE ABOVE.

   FEATURES:

   1. Existing registered email + correct password -> LOGIN
   2. Wrong password -> ERROR
   3. Forgot Access Key -> RESET PANEL
   4. Reset password -> BACKEND DATABASE
   5. New password -> LOGIN
   6. Existing users NEVER need to create another account
   7. Existing dashboard / AI / LinkedIn / scheduling remain
      untouched.
============================================================ */

(function () {

    "use strict";


    /* ========================================================
       HELPER
    ======================================================== */

    function neonGet(id) {

        return document.getElementById(id);

    }


    /* ========================================================
       LOGIN ERROR
    ======================================================== */

    function neonLoginMessage(
        message,
        success
    ) {

        const box =
            neonGet("loginError");


        if (!box) {

            return;

        }


        box.textContent =
            message || "";


        if (message) {

            box.classList.add(
                "show"
            );

        }
        else {

            box.classList.remove(
                "show"
            );

        }


        if (success) {

            box.style.color =
                "#00f5b0";

        }
        else {

            box.style.color =
                "#ff4f9a";

        }

    }


    /* ========================================================
       RESET MESSAGE
    ======================================================== */

    function neonResetMessage(
        message,
        success
    ) {

        const box =
            neonGet(
                "resetPasswordMessage"
            );


        if (!box) {

            return;

        }


        box.textContent =
            message || "";


        if (message) {

            box.classList.add(
                "show"
            );

        }
        else {

            box.classList.remove(
                "show"
            );

        }


        if (success) {

            box.style.color =
                "#00f5b0";

        }
        else {

            box.style.color =
                "#ff4f9a";

        }

    }


    /* ========================================================
       SERVER REQUEST
    ======================================================== */

    async function neonRequest(
        url,
        method,
        body
    ) {

        const response =
            await fetch(
                url,
                {

                    method:
                        method,

                    credentials:
                        "include",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        body
                            ? JSON.stringify(body)
                            : undefined

                }
            );


        let data = {};


        try {

            data =
                await response.json();

        }
        catch (error) {

            data = {};

        }


        return {

            response:
                response,

            data:
                data

        };

    }


    /* ========================================================
       UPDATE USER DETAILS
    ======================================================== */

    function updateNeonUser(
        user
    ) {

        if (!user) {

            return;

        }


        let name =
            user.name;


        if (
            !name &&
            user.email &&
            user.email.includes("@")
        ) {

            name =
                user.email
                    .split("@")[0]
                    .replace(
                        /[._-]+/g,
                        " "
                    )
                    .replace(
                        /\b\w/g,
                        function (letter) {

                            return letter
                                .toUpperCase();

                        }
                    );

        }


        if (!name) {

            name =
                "User";

        }


        const parts =
            name
                .trim()
                .split(/\s+/);


        let initials;


        if (
            parts.length ===
            1
        ) {

            initials =
                parts[0]
                    .substring(
                        0,
                        2
                    )
                    .toUpperCase();

        }
        else {

            initials =
                (
                    parts[0][0] +
                    parts[
                        parts.length - 1
                    ][0]
                ).toUpperCase();

        }


        /* LOGIN WELCOME */

        const welcome =
            neonGet(
                "loginWelcome"
            );


        if (welcome) {

            welcome.textContent =
                "Welcome back, " +
                name;

        }


        /* PROFILE */

        const profileName =
            neonGet(
                "profileName"
            );


        if (profileName) {

            profileName.textContent =
                name;

        }


        const profileAvatar =
            neonGet(
                "profileAvatar"
            );


        if (profileAvatar) {

            profileAvatar.textContent =
                initials;

        }


        /* DROPDOWN */

        const dropdownName =
            neonGet(
                "dropdownName"
            );


        if (dropdownName) {

            dropdownName.textContent =
                name;

        }


        const dropdownEmail =
            neonGet(
                "dropdownEmail"
            );


        if (dropdownEmail) {

            dropdownEmail.textContent =
                user.email || "";

        }


        const dropdownAvatar =
            neonGet(
                "dropdownAvatar"
            );


        if (dropdownAvatar) {

            dropdownAvatar.textContent =
                initials;

        }


        /* AI GREETING */

        const greeting =
            neonGet(
                "aiGreeting"
            );


        if (greeting) {

            greeting.textContent =
                "Hello, " +
                name +
                " 👋";

        }

    }


    /* ========================================================
       CHECK EXISTING SESSION
    ======================================================== */

    async function checkNeonSession() {

        try {

            const result =
                await neonRequest(
                    "/api/auth/me",
                    "GET",
                    null
                );


            if (
                result.response.ok &&
                result.data &&
                result.data.success === true &&
                result.data.authenticated === true &&
                result.data.user
            ) {

                document.body.classList.add(
                    "authenticated"
                );


                updateNeonUser(
                    result.data.user
                );


                const loginPage =
                    neonGet(
                        "loginPage"
                    );


                if (loginPage) {

                    loginPage.classList.add(
                        "hidden"
                    );

                    loginPage.style.display =
                        "none";

                }


                return true;

            }

        }
        catch (error) {

            console.warn(
                "NeonSocial session check:",
                error
            );

        }


        return false;

    }


    /* ========================================================
       FINAL LOGIN
    ======================================================== */

    async function neonFinalLogin(
        event
    ) {

        event.preventDefault();

        event.stopPropagation();

        event.stopImmediatePropagation();


        const emailInput =
            neonGet(
                "loginUsername"
            );


        const passwordInput =
            neonGet(
                "loginPassword"
            );


        const loginButton =
            neonGet(
                "loginButton"
            );


        if (
            !emailInput ||
            !passwordInput ||
            !loginButton
        ) {

            return;

        }


        const email =
            emailInput.value
                .trim()
                .toLowerCase();


        const password =
            passwordInput.value;


        neonLoginMessage(
            ""
        );


        /* ====================================================
           VALIDATION
        ==================================================== */

        if (!email) {

            neonLoginMessage(
                "Please enter your registered email."
            );

            emailInput.focus();

            return;

        }


        if (!password) {

            neonLoginMessage(
                "Please enter your access key."
            );

            passwordInput.focus();

            return;

        }


        const original =
            loginButton.innerHTML;


        loginButton.disabled =
            true;


        loginButton.innerHTML =
            "<span>AUTHENTICATING...</span><b>◌</b>";


        try {

            /* =================================================
               REAL BACKEND LOGIN

               IMPORTANT:

               This searches the existing users table through
               your backend.

               It DOES NOT create an account.

               Therefore an existing account can log in.
            ================================================= */

            const result =
                await neonRequest(

                    "/api/auth/login",

                    "POST",

                    {

                        email:
                            email,

                        password:
                            password

                    }

                );


            const response =
                result.response;


            const data =
                result.data;


            console.log(
                "NEONSOCIAL LOGIN:",
                response.status,
                data
            );


            /* =================================================
               SUCCESS
            ================================================= */

            if (
                response.ok &&
                data &&
                data.success === true
            ) {

                neonLoginMessage(
                    ""
                );


                document.body.classList.add(
                    "authenticated"
                );


                const loginPage =
                    neonGet(
                        "loginPage"
                    );


                if (loginPage) {

                    loginPage.classList.add(
                        "hidden"
                    );

                    loginPage.style.display =
                        "none";

                }


                /*
                 * Get the ACTUAL authenticated account.
                 */

                try {

                    const userResult =
                        await neonRequest(
                            "/api/auth/me",
                            "GET",
                            null
                        );


                    if (
                        userResult.response.ok &&
                        userResult.data &&
                        userResult.data.user
                    ) {

                        updateNeonUser(
                            userResult.data.user
                        );

                    }

                }
                catch (error) {

                    console.warn(
                        "Unable to load user:",
                        error
                    );

                }


                /*
                 * IMPORTANT:
                 *
                 * Existing account goes to the
                 * main NeonSocial application.
                 *
                 * It NEVER goes to signup.
                 */

                setTimeout(
                    function () {

                        window.location.replace(
                            "/"
                        );

                    },
                    200
                );


                return;

            }


            /* =================================================
               LOGIN FAILED
            ================================================= */

            neonLoginMessage(

                data.message ||
                data.error ||
                "Invalid email or password."

            );

        }
        catch (error) {

            console.error(
                "NEONSOCIAL LOGIN ERROR:",
                error
            );


            neonLoginMessage(
                "Unable to connect to NeonSocial AI server."
            );

        }
        finally {

            loginButton.disabled =
                false;


            loginButton.innerHTML =
                original;

        }

    }


    /* ========================================================
       FORGOT PASSWORD
    ======================================================== */

    function neonFinalForgotPassword(
        event
    ) {

        event.preventDefault();

        event.stopPropagation();

        event.stopImmediatePropagation();


        const panel =
            neonGet(
                "resetPasswordPanel"
            );


        const email =
    document.getElementById("resetEmail");


        const loginEmail =
            neonGet(
                "loginUsername"
            );


        if (!panel) {

            return;

        }


        const hidden =
            panel.style.display ===
                "none" ||

            getComputedStyle(
                panel
            ).display ===
                "none";


        if (hidden) {

            panel.style.display =
                "block";


            /*
             * Automatically copy the email
             * from login field.
             */

            if (
                resetEmail &&
                loginEmail &&
                loginEmail.value.trim()
            ) {

                resetEmail.value =
                    loginEmail.value
                        .trim()
                        .toLowerCase();

            }


            neonResetMessage(
                ""
            );


            if (resetEmail) {

                setTimeout(
                    function () {

                        resetEmail.focus();

                    },
                    50
                );

            }

        }
        else {

            panel.style.display =
                "none";

        }

    }


    /* ========================================================
       RESET PASSWORD
    ======================================================== */

    async function neonFinalResetPassword(
        event
    ) {

        event.preventDefault();

        event.stopPropagation();

        event.stopImmediatePropagation();


        const emailInput =
            neonGet(
                "resetEmail"
            );


        const newPasswordInput =
            neonGet(
                "resetNewPassword"
            );


        const confirmPasswordInput =
            neonGet(
                "resetConfirmPassword"
            );


        const resetButton =
            neonGet(
                "resetPasswordBtn"
            );


        if (
            !emailInput ||
            !newPasswordInput ||
            !confirmPasswordInput ||
            !resetButton
        ) {

            return;

        }


        const email =
            emailInput.value
                .trim()
                .toLowerCase();


        const newPassword =
            newPasswordInput.value;


        const confirmPassword =
            confirmPasswordInput.value;


        neonResetMessage(
            ""
        );


        /* ====================================================
           VALIDATION
        ==================================================== */

        if (!email) {

            neonResetMessage(
                "Enter your registered email."
            );

            emailInput.focus();

            return;

        }


        if (
            newPassword.length <
            8
        ) {

            neonResetMessage(
                "Password must contain at least 8 characters."
            );

            newPasswordInput.focus();

            return;

        }


        if (
            newPassword !==
            confirmPassword
        ) {

            neonResetMessage(
                "Passwords do not match."
            );

            confirmPasswordInput.focus();

            return;

        }


        const original =
            resetButton.innerHTML;


        resetButton.disabled =
            true;


        resetButton.innerHTML =
            "<span>RESETTING...</span><b>◌</b>";


        try {

            /* =================================================
               SEND PASSWORD CHANGE TO BACKEND

               This is what changes the password belonging to
               the EXISTING account.
            ================================================= */

            const result =
                await neonRequest(

                    "/api/auth/reset-password",

                    "POST",

                    {

                        email:
                            email,

                        new_password:
                            newPassword,

                        confirm_password:
                            confirmPassword,

                        /*
                         * Compatibility field.
                         */

                        password:
                            newPassword

                    }

                );


            const response =
                result.response;


            const data =
                result.data;


            console.log(
                "NEONSOCIAL PASSWORD RESET:",
                response.status,
                data
            );


            /* =================================================
               SUCCESS
            ================================================= */

            if (
                response.ok &&
                data &&
                data.success === true
            ) {

                neonResetMessage(

                    data.message ||

                    "✓ Password reset successfully. You can now login with your new access key.",

                    true

                );


                /*
                 * Put the email and NEW password into
                 * the login form automatically.
                 */

                const loginEmail =
                    neonGet(
                        "loginUsername"
                    );


                const loginPassword =
                    neonGet(
                        "loginPassword"
                    );


                if (loginEmail) {

                    loginEmail.value =
                        email;

                }


                if (loginPassword) {

                    loginPassword.value =
                        newPassword;

                }


                /*
                 * Clear reset password fields.
                 */

                newPasswordInput.value =
                    "";


                confirmPasswordInput.value =
                    "";


                /*
                 * Close reset panel.
                 */

                setTimeout(
                    function () {

                        if (panelExists()) {

                            neonGet(
                                "resetPasswordPanel"
                            ).style.display =
                                "none";

                        }


                        neonLoginMessage(

                            "Password reset successfully. Login with your new access key.",

                            true

                        );

                    },
                    1200
                );


                return;

            }


            /* =================================================
               RESET FAILED
            ================================================= */

            neonResetMessage(

                data.message ||
                data.error ||
                "Unable to reset password. Make sure this email belongs to an existing account."

            );

        }
        catch (error) {

            console.error(
                "NEONSOCIAL RESET ERROR:",
                error
            );


            neonResetMessage(
                "Unable to connect to NeonSocial AI server."
            );

        }
        finally {

            resetButton.disabled =
                false;


            resetButton.innerHTML =
                original;

        }

    }


    /* ========================================================
       PANEL EXISTS
    ======================================================== */

    function panelExists() {

        return Boolean(
            neonGet(
                "resetPasswordPanel"
            )
        );

    }


    /* ========================================================
       ENTER KEY
    ======================================================== */

    function neonEnterSupport() {

        const loginEmail =
            neonGet(
                "loginUsername"
            );


        const loginPassword =
            neonGet(
                "loginPassword"
            );


        const resetEmail =
            neonGet(
                "resetEmail"
            );


        const resetPassword =
            neonGet(
                "resetNewPassword"
            );


        const resetConfirm =
            neonGet(
                "resetConfirmPassword"
            );


        function loginEnter(
            event
        ) {

            if (
                event.key ===
                "Enter"
            ) {

                event.preventDefault();


                const button =
                    neonGet(
                        "loginButton"
                    );


                if (button) {

                    button.click();

                }

            }

        }


        function resetEnter(
            event
        ) {

            if (
                event.key ===
                "Enter"
            ) {

                event.preventDefault();


                const button =
                    neonGet(
                        "resetPasswordBtn"
                    );


                if (button) {

                    button.click();

                }

            }

        }


        if (loginEmail) {

            loginEmail.addEventListener(
                "keydown",
                loginEnter
            );

        }


        if (loginPassword) {

            loginPassword.addEventListener(
                "keydown",
                loginEnter
            );

        }


        if (resetEmail) {

            resetEmail.addEventListener(
                "keydown",
                resetEnter
            );

        }


        if (resetPassword) {

            resetPassword.addEventListener(
                "keydown",
                resetEnter
            );

        }


        if (resetConfirm) {

            resetConfirm.addEventListener(
                "keydown",
                resetEnter
            );

        }

    }


    /* ========================================================
       INSTALL
    ======================================================== */

    function installFinalFix() {

        const loginButton =
            neonGet(
                "loginButton"
            );


        const forgotButton =
            neonGet(
                "forgotPasswordBtn"
            );


        const resetButton =
            neonGet(
                "resetPasswordBtn"
            );


        /*
         * CAPTURE MODE IS IMPORTANT.
         *
         * Your original 3466-line app.js has old handlers.
         *
         * These handlers run first and stop the old handlers
         * from sending another request.
         */

        if (loginButton) {

            loginButton.addEventListener(
                "click",
                neonFinalLogin,
                true
            );

        }


        if (forgotButton) {

            forgotButton.addEventListener(
                "click",
                neonFinalForgotPassword,
                true
            );

        }


        if (resetButton) {

            resetButton.addEventListener(
                "click",
                neonFinalResetPassword,
                true
            );

        }


        neonEnterSupport();


        /*
         * Check existing login session.
         */

        checkNeonSession();

    }


    /* ========================================================
       START
    ======================================================== */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            installFinalFix
        );

    }
    else {

        installFinalFix();

    }

})();
/* ============================================================
   NEONSOCIAL FINAL AUTH COMPATIBILITY FIX
   - Existing account login
   - Forgot Access Key
   - Password reset
   - Does NOT disturb existing application features
   ============================================================ */

(function NeonSocialFinalAuthFix() {

    function init() {

        console.log("NeonSocial Final Auth Fix loaded.");

        /* =====================================================
           LOGIN
           ===================================================== */

        const loginButton =
            document.getElementById("loginButton");

        const loginEmail =
            document.getElementById("loginUsername");

        const loginPassword =
            document.getElementById("loginPassword");

        const loginError =
            document.getElementById("loginError");


        if (loginButton && loginEmail && loginPassword) {

            /*
             * Do not replace the existing login handler.
             * Only make sure Enter key works.
             */

            loginEmail.addEventListener(
                "keydown",
                function(event) {

                    if (event.key === "Enter") {

                        event.preventDefault();

                        loginButton.click();

                    }

                }
            );

            loginPassword.addEventListener(
                "keydown",
                function(event) {

                    if (event.key === "Enter") {

                        event.preventDefault();

                        loginButton.click();

                    }

                }
            );

        }


        /* =====================================================
           FORGOT ACCESS KEY
           ===================================================== */

        let forgotButton =
            document.getElementById(
                "forgotPasswordBtn"
            );


        /*
         * If the button does not exist, do nothing.
         */

        if (!forgotButton) {

            console.warn(
                "NeonSocial: forgotPasswordBtn not found."
            );

            return;

        }


        /*
         * Prevent duplicate event handlers.
         */

        if (
            forgotButton.dataset.neonFinalBound === "true"
        ) {

            return;

        }


        forgotButton.dataset.neonFinalBound =
            "true";


        /* =====================================================
           FIND / CREATE RESET PANEL
           ===================================================== */

        let resetPanel =
            document.getElementById(
                "resetPasswordPanel"
            );


        /*
         * If the HTML already has the panel,
         * use it.
         *
         * Otherwise create one automatically.
         */

        if (!resetPanel) {

            resetPanel =
                document.createElement("div");

            resetPanel.id =
                "resetPasswordPanel";

            resetPanel.style.display =
                "none";

            resetPanel.style.marginTop =
                "18px";

            resetPanel.style.padding =
                "20px";

            resetPanel.style.borderRadius =
                "18px";

            resetPanel.style.background =
                "rgba(5, 12, 32, 0.95)";

            resetPanel.style.border =
                "1px solid rgba(0,245,255,.25)";

            resetPanel.style.boxShadow =
                "0 0 30px rgba(0,245,255,.08)";


            resetPanel.innerHTML = `

                <div
                    style="
                        color:#00f5ff;
                        font-size:13px;
                        font-weight:700;
                        letter-spacing:2px;
                        margin-bottom:15px;
                    "
                >
                    RESET ACCESS KEY
                </div>


                <input
                    id="resetEmail"
                    type="email"
                    placeholder="Registered email"
                    autocomplete="email"
                    style="
                        width:100%;
                        box-sizing:border-box;
                        margin-bottom:10px;
                        padding:14px;
                        border-radius:10px;
                        border:1px solid rgba(0,245,255,.2);
                        background:#050b1c;
                        color:white;
                        outline:none;
                    "
                >


                <input
                    id="resetNewPassword"
                    type="password"
                    placeholder="New access key (8+ characters)"
                    autocomplete="new-password"
                    style="
                        width:100%;
                        box-sizing:border-box;
                        margin-bottom:10px;
                        padding:14px;
                        border-radius:10px;
                        border:1px solid rgba(0,245,255,.2);
                        background:#050b1c;
                        color:white;
                        outline:none;
                    "
                >


                <input
                    id="resetConfirmPassword"
                    type="password"
                    placeholder="Confirm new access key"
                    autocomplete="new-password"
                    style="
                        width:100%;
                        box-sizing:border-box;
                        margin-bottom:12px;
                        padding:14px;
                        border-radius:10px;
                        border:1px solid rgba(0,245,255,.2);
                        background:#050b1c;
                        color:white;
                        outline:none;
                    "
                >


                <button
                    type="button"
                    id="resetPasswordBtn"
                    style="
                        width:100%;
                        padding:14px;
                        border:0;
                        border-radius:10px;
                        cursor:pointer;
                        background:linear-gradient(
                            135deg,
                            #00f5ff,
                            #00ff9d
                        );
                        color:#00151b;
                        font-weight:800;
                        letter-spacing:1px;
                    "
                >
                    RESET ACCESS KEY →
                </button>


                <div
                    id="resetPasswordMessage"
                    style="
                        margin-top:12px;
                        font-size:13px;
                        text-align:center;
                        min-height:18px;
                    "
                ></div>

            `;


            /*
             * Put panel immediately after Forgot button.
             */

            forgotButton.parentNode.insertBefore(
                resetPanel,
                forgotButton.nextSibling
            );

        }


        /* =====================================================
           GET RESET ELEMENTS
           ===================================================== */

        const resetEmail =
            document.getElementById(
                "resetEmail"
            );

        const resetNewPassword =
            document.getElementById(
                "resetNewPassword"
            );

        const resetConfirmPassword =
            document.getElementById(
                "resetConfirmPassword"
            );

        const resetButton =
            document.getElementById(
                "resetPasswordBtn"
            );

        const resetMessage =
            document.getElementById(
                "resetPasswordMessage"
            );


        if (
            !resetEmail ||
            !resetNewPassword ||
            !resetConfirmPassword ||
            !resetButton ||
            !resetMessage
        ) {

            console.error(
                "NeonSocial: reset elements missing."
            );

            return;

        }


        /* =====================================================
           FORGOT BUTTON CLICK
           ===================================================== */

        forgotButton.addEventListener(
            "click",
            function(event) {

                event.preventDefault();
                event.stopPropagation();


                const isHidden =
                    resetPanel.style.display === "none" ||
                    resetPanel.style.display === "";


                if (isHidden) {

                    resetPanel.style.display =
                        "block";


                    /*
                     * Automatically use the email
                     * currently entered in login.
                     */

                    if (
                        loginEmail &&
                        loginEmail.value.trim()
                    ) {

                        resetEmail.value =
                            loginEmail.value.trim();

                    }


                    resetMessage.textContent =
                        "";

                    resetNewPassword.value =
                        "";

                    resetConfirmPassword.value =
                        "";


                    resetEmail.focus();


                    /*
                     * Scroll panel into view.
                     */

                    setTimeout(
                        function() {

                            resetPanel.scrollIntoView({
                                behavior: "smooth",
                                block: "center"
                            });

                        },
                        50
                    );

                }
                else {

                    resetPanel.style.display =
                        "none";

                }

            }
        );


        /* =====================================================
           RESET PASSWORD
           ===================================================== */

        resetButton.addEventListener(
            "click",
            async function(event) {

                event.preventDefault();
                event.stopPropagation();


                const email =
                    resetEmail.value
                        .trim()
                        .toLowerCase();


                const newPassword =
                    resetNewPassword.value;


                const confirmPassword =
                    resetConfirmPassword.value;


                resetMessage.textContent =
                    "";


                if (!email) {

                    resetMessage.textContent =
                        "Enter your registered email.";

                    resetEmail.focus();

                    return;

                }


                if (newPassword.length < 8) {

                    resetMessage.textContent =
                        "Password must contain at least 8 characters.";

                    resetNewPassword.focus();

                    return;

                }


                if (
                    newPassword !==
                    confirmPassword
                ) {

                    resetMessage.textContent =
                        "Passwords do not match.";

                    resetConfirmPassword.focus();

                    return;

                }


                const originalHTML =
                    resetButton.innerHTML;


                resetButton.disabled =
                    true;


                resetButton.innerHTML =
                    "RESETTING...";


                try {

                    console.log(
                        "NeonSocial: sending password reset request."
                    );


                    const response =
                        await fetch(
                            "/api/auth/reset-password",
                            {
                                method: "POST",

                                credentials:
                                    "include",

                                headers: {
                                    "Content-Type":
                                        "application/json",

                                    "Accept":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify({

                                        email:
                                            email,

                                        new_password:
                                            newPassword,

                                        confirm_password:
                                            confirmPassword

                                    })
                            }
                        );


                    let data = {};


                    try {

                        data =
                            await response.json();

                    }
                    catch(error) {

                        console.error(
                            "Reset response was not JSON:",
                            error
                        );

                    }


                    console.log(
                        "Password reset response:",
                        response.status,
                        data
                    );


                    if (
                        response.ok &&
                        data.success === true
                    ) {

                        resetMessage.textContent =
                            "✓ Password reset successfully. You can now login.";


                        resetMessage.style.color =
                            "#00ff9d";


                        /*
                         * Put the email back into
                         * the login box.
                         */

                        if (loginEmail) {

                            loginEmail.value =
                                email;

                        }


                        /*
                         * Put the NEW password
                         * into login automatically.
                         */

                        if (loginPassword) {

                            loginPassword.value =
                                newPassword;

                        }


                        resetNewPassword.value =
                            "";

                        resetConfirmPassword.value =
                            "";


                        /*
                         * Close reset panel after a short delay.
                         */

                        setTimeout(
                            function() {

                                resetPanel.style.display =
                                    "none";

                                resetMessage.textContent =
                                    "";

                                resetMessage.style.color =
                                    "";

                            },
                            1800
                        );


                        return;

                    }


                    resetMessage.textContent =
                        (
                            data &&
                            data.error
                        )
                            ? data.error
                            : "Unable to reset password.";


                    resetMessage.style.color =
                        "#ff4d8d";


                }
                catch(error) {

                    console.error(
                        "NeonSocial password reset error:",
                        error
                    );


                    resetMessage.textContent =
                        "Unable to connect to NeonSocial AI server.";


                    resetMessage.style.color =
                        "#ff4d8d";

                }
                finally {

                    resetButton.disabled =
                        false;

                    resetButton.innerHTML =
                        originalHTML;

                }

            }
        );


        console.log(
            "NeonSocial: Forgot Access Key is ready."
        );

    }


    /*
     * DOM READY
     */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            init
        );

    }
    else {

        init();

    }

})();
/* ============================================================
   NEONSOCIAL - FORGOT ACCESS KEY FINAL WORKING SYSTEM
   ============================================================ */

(function () {

    function initForgotAccessKey() {

        /* --------------------------------------------------------
           FIND FORGOT BUTTON
           -------------------------------------------------------- */

        let forgotBtn =
            document.getElementById("forgotPasswordBtn");

        /*
         * If the ID is missing, find the button by its text.
         */
        if (!forgotBtn) {

            const buttons =
                document.querySelectorAll("button");

            buttons.forEach(function (button) {

                const text =
                    button.textContent
                        .trim()
                        .toUpperCase();

                if (
                    text.includes("FORGOT ACCESS KEY") ||
                    text.includes("FORGOT PASSWORD")
                ) {
                    forgotBtn = button;
                }

            });

        }

        if (!forgotBtn) {

            console.warn(
                "NeonSocial: Forgot Access Key button not found."
            );

            return;

        }

        /* --------------------------------------------------------
           REMOVE OLD CLICK HANDLERS
           -------------------------------------------------------- */

        const cleanButton =
            forgotBtn.cloneNode(true);

        forgotBtn.parentNode.replaceChild(
            cleanButton,
            forgotBtn
        );

        forgotBtn = cleanButton;

        forgotBtn.id =
            "forgotPasswordBtn";

        forgotBtn.type =
            "button";

        /* --------------------------------------------------------
           FIND OR CREATE RESET PANEL
           -------------------------------------------------------- */

        let panel =
            document.getElementById(
                "resetPasswordPanel"
            );

        if (!panel) {

            panel =
                document.createElement("div");

            panel.id =
                "resetPasswordPanel";

            panel.style.display =
                "none";

            panel.innerHTML = `

                <div class="neon-reset-box">

                    <div class="neon-reset-title">
                        RESET ACCESS KEY
                    </div>

                    <div class="neon-reset-subtitle">
                        Enter your registered email and create
                        a new access key.
                    </div>

                    <input
                        id="resetEmail"
                        type="email"
                        placeholder="Registered email"
                        autocomplete="email"
                    >

                    <input
                        id="resetNewPassword"
                        type="password"
                        placeholder="New access key"
                        autocomplete="new-password"
                    >

                    <input
                        id="resetConfirmPassword"
                        type="password"
                        placeholder="Confirm new access key"
                        autocomplete="new-password"
                    >

                    <button
                        id="resetPasswordBtn"
                        type="button"
                    >
                        RESET ACCESS KEY
                        <span>→</span>
                    </button>

                    <div
                        id="resetPasswordMessage"
                    ></div>

                </div>

            `;

            /*
             * Put panel directly after forgot button.
             */
            forgotBtn.parentNode.insertBefore(
                panel,
                forgotBtn.nextSibling
            );

        }

        /* --------------------------------------------------------
           GET RESET ELEMENTS
           -------------------------------------------------------- */

        const resetBtn =
            document.getElementById(
                "resetPasswordBtn"
            );

        const email =
            document.getElementById(
                "resetEmail"
            );

        const newPassword =
            document.getElementById(
                "resetNewPassword"
            );

        const confirmPassword =
            document.getElementById(
                "resetConfirmPassword"
            );

        const message =
            document.getElementById(
                "resetPasswordMessage"
            );

        if (
            !resetBtn ||
            !email ||
            !newPassword ||
            !confirmPassword ||
            !message
        ) {

            console.error(
                "NeonSocial: Reset password elements missing."
            );

            return;

        }

        /* --------------------------------------------------------
           FORGOT BUTTON
           -------------------------------------------------------- */

        forgotBtn.addEventListener(
            "click",
            function (event) {

                event.preventDefault();
                event.stopPropagation();

                const currentlyHidden =
                    panel.style.display === "none" ||
                    getComputedStyle(panel).display === "none";

                if (currentlyHidden) {

                    /* OPEN */

                    panel.style.display =
                        "block";

                    /*
                     * Automatically use email
                     * already entered in login.
                     */
                    const loginEmail =
                        document.getElementById(
                            "loginUsername"
                        );

                    if (
                        loginEmail &&
                        loginEmail.value.trim()
                    ) {

                        email.value =
                            loginEmail.value.trim();

                    } else {

                        email.value = "";

                    }

                    newPassword.value = "";
                    confirmPassword.value = "";

                    message.textContent = "";

                    message.className = "";

                    /*
                     * Scroll reset panel into view.
                     */
                    setTimeout(
                        function () {

                            panel.scrollIntoView({
                                behavior: "smooth",
                                block: "center"
                            });

                            email.focus();

                        },
                        100
                    );

                } else {

                    /* CLOSE */

                    panel.style.display =
                        "none";

                }

            }
        );

        /* --------------------------------------------------------
           RESET PASSWORD
           -------------------------------------------------------- */

        resetBtn.addEventListener(
            "click",
            async function () {

                const emailValue =
                    email.value.trim();

                const newPasswordValue =
                    newPassword.value;

                const confirmPasswordValue =
                    confirmPassword.value;

                message.textContent = "";

                message.className = "";

                /* --------------------------------------------
                   VALIDATION
                   -------------------------------------------- */

                if (!emailValue) {

                    message.textContent =
                        "Enter your registered email.";

                    message.className =
                        "reset-error";

                    email.focus();

                    return;

                }

                if (
                    newPasswordValue.length < 8
                ) {

                    message.textContent =
                        "Access key must contain at least 8 characters.";

                    message.className =
                        "reset-error";

                    newPassword.focus();

                    return;

                }

                if (
                    newPasswordValue !==
                    confirmPasswordValue
                ) {

                    message.textContent =
                        "Access keys do not match.";

                    message.className =
                        "reset-error";

                    confirmPassword.focus();

                    return;

                }

                /* --------------------------------------------
                   LOADING
                   -------------------------------------------- */

                const originalText =
                    resetBtn.innerHTML;

                resetBtn.disabled =
                    true;

                resetBtn.innerHTML =
                    "RESETTING...";

                try {

                    const response =
                        await fetch(
                            "/api/auth/reset-password",
                            {
                                method: "POST",

                                credentials:
                                    "include",

                                headers: {
                                    "Content-Type":
                                        "application/json",

                                    "Accept":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify({

                                        email:
                                            emailValue,

                                        new_password:
                                            newPasswordValue,

                                        confirm_password:
                                            confirmPasswordValue

                                    })
                            }
                        );

                    let data = {};

                    try {

                        data =
                            await response.json();

                    } catch {

                        data = {};

                    }

                    /* ----------------------------------------
                       SUCCESS
                       ---------------------------------------- */

                    if (
                        response.ok &&
                        data.success === true
                    ) {

                        message.textContent =
                            "✓ Access key reset successfully.";

                        message.className =
                            "reset-success";

                        newPassword.value =
                            "";

                        confirmPassword.value =
                            "";

                        setTimeout(
                            function () {

                                panel.style.display =
                                    "none";

                                message.textContent =
                                    "";

                                message.className =
                                    "";

                            },
                            2500
                        );

                        return;

                    }

                    /* ----------------------------------------
                       SERVER ERROR
                       ---------------------------------------- */

                    message.textContent =
                        data.error ||
                        "Unable to reset access key.";

                    message.className =
                        "reset-error";

                } catch (error) {

                    console.error(
                        "Reset password error:",
                        error
                    );

                    message.textContent =
                        "Unable to connect to NeonSocial AI server.";

                    message.className =
                        "reset-error";

                } finally {

                    resetBtn.disabled =
                        false;

                    resetBtn.innerHTML =
                        originalText;

                }

            }
        );

        /* --------------------------------------------------------
           ENTER KEY SUPPORT
           -------------------------------------------------------- */

        [email, newPassword, confirmPassword]
            .forEach(function (input) {

                input.addEventListener(
                    "keydown",
                    function (event) {

                        if (
                            event.key === "Enter"
                        ) {

                            event.preventDefault();

                            resetBtn.click();

                        }

                    }
                );

            });

        console.log(
            "✓ NeonSocial Forgot Access Key system ready."
        );

    }


    /* ------------------------------------------------------------
       WAIT UNTIL DOM IS READY
       ------------------------------------------------------------ */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initForgotAccessKey
        );

    } else {

        initForgotAccessKey();

    }

})();
/* ============================================================
   CLOSE RESET PASSWORD PANEL
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const closeReset =
            document.getElementById(
                "closeResetPassword"
            );

        const resetPanel =
            document.getElementById(
                "resetPasswordPanel"
            );

        if (
            closeReset &&
            resetPanel
        ) {

            closeReset.addEventListener(
                "click",
                function () {

                    resetPanel.style.display =
                        "none";

                }
            );

        }

    }
);
/* ============================================================
   NEONSOCIAL - FINAL PASSWORD RESET
   ============================================================ */

(function finalPasswordReset() {

    function setupPasswordReset() {

        const forgotButton =
            document.getElementById("forgotPasswordBtn");

        const panel =
            document.getElementById("resetPasswordPanel");

        const resetButton =
            document.getElementById("resetPasswordBtn");

        const resetEmail =
            document.getElementById("resetEmail");

        const newPassword =
            document.getElementById("resetNewPassword");

        const confirmPassword =
            document.getElementById("resetConfirmPassword");

        const message =
            document.getElementById("resetPasswordMessage");

        const loginEmail =
            document.getElementById("loginUsername");

        const loginPassword =
            document.getElementById("loginPassword");


        /*
         * Make sure the elements actually exist.
         */

        if (
            !forgotButton ||
            !panel ||
            !resetButton ||
            !resetEmail ||
            !newPassword ||
            !confirmPassword ||
            !message
        ) {

            console.warn(
                "NeonSocial reset elements not found."
            );

            return;

        }


        /*
         * Prevent duplicate listeners.
         */

        if (
            forgotButton.dataset.resetReady === "true"
        ) {

            return;

        }

        forgotButton.dataset.resetReady = "true";


        /*
         * FORGOT ACCESS KEY
         */

        forgotButton.addEventListener(
            "click",
            function(event) {

                event.preventDefault();
                event.stopPropagation();

                const hidden =
                    window.getComputedStyle(panel).display ===
                    "none";

                if (hidden) {

                    panel.style.display = "block";

                    if (
                        loginEmail &&
                        loginEmail.value.trim()
                    ) {

                        resetEmail.value =
                            loginEmail.value.trim();

                    }

                    message.textContent = "";

                    message.classList.remove(
                        "show"
                    );

                    setTimeout(
                        function() {

                            panel.scrollIntoView({
                                behavior: "smooth",
                                block: "center"
                            });

                            resetEmail.focus();

                        },
                        100
                    );

                }
                else {

                    panel.style.display = "none";

                }

            }
        );


        /*
         * RESET PASSWORD
         */

        resetButton.addEventListener(
            "click",
            async function(event) {

                event.preventDefault();
                event.stopPropagation();


                const email =
                    resetEmail.value
                        .trim()
                        .toLowerCase();

                const password =
                    newPassword.value;

                const confirm =
                    confirmPassword.value;


                /*
                 * Clear previous message.
                 */

                message.textContent = "";

                message.classList.remove(
                    "show"
                );


                /*
                 * Validate email.
                 */

                if (!email) {

                    message.textContent =
                        "Enter your registered email.";

                    message.classList.add(
                        "show"
                    );

                    resetEmail.focus();

                    return;

                }


                /*
                 * Validate password.
                 */

                if (password.length < 8) {

                    message.textContent =
                        "Password must contain at least 8 characters.";

                    message.classList.add(
                        "show"
                    );

                    newPassword.focus();

                    return;

                }


                /*
                 * Confirm password.
                 */

                if (password !== confirm) {

                    message.textContent =
                        "Passwords do not match.";

                    message.classList.add(
                        "show"
                    );

                    confirmPassword.focus();

                    return;

                }


                /*
                 * Save original button.
                 */

                const originalHTML =
                    resetButton.innerHTML;


                /*
                 * Disable button.
                 */

                resetButton.disabled =
                    true;

                resetButton.innerHTML =
                    "<span>RESETTING...</span><b>◌</b>";


                try {

                    console.log(
                        "NeonSocial: sending password reset request..."
                    );


                    const response =
                        await fetch(
                            "/api/auth/reset-password",
                            {

                                method: "POST",

                                credentials: "include",

                                headers: {

                                    "Content-Type":
                                        "application/json",

                                    "Accept":
                                        "application/json"

                                },

                                body:
                                    JSON.stringify({

                                        email:
                                            email,

                                        new_password:
                                            password,

                                        confirm_password:
                                            confirm

                                    })

                            }
                        );


                    console.log(
                        "NeonSocial reset response:",
                        response.status
                    );


                    let data = {};

                    try {

                        data =
                            await response.json();

                    }
                    catch(error) {

                        console.error(
                            "Could not parse reset response:",
                            error
                        );

                    }


                    console.log(
                        "NeonSocial reset data:",
                        data
                    );


                    /*
                     * SUCCESS
                     */

                    if (
                        response.ok &&
                        data.success === true
                    ) {

                        message.textContent =
                            "✓ Password reset successfully. You can now login.";

                        message.classList.add(
                            "show"
                        );


                        /*
                         * Put the registered email
                         * back into the login field.
                         */

                        if (loginEmail) {

                            loginEmail.value =
                                email;

                        }


                        /*
                         * Put the NEW password into
                         * the login password field.
                         */

                        if (loginPassword) {

                            loginPassword.value =
                                password;

                        }


                        /*
                         * Clear reset fields.
                         */

                        newPassword.value =
                            "";

                        confirmPassword.value =
                            "";


                        /*
                         * Close reset panel after
                         * successful reset.
                         */

                        setTimeout(
                            function() {

                                panel.style.display =
                                    "none";

                                message.textContent =
                                    "";

                                message.classList.remove(
                                    "show"
                                );

                                if (loginPassword) {

                                    loginPassword.focus();

                                }

                            },
                            1800
                        );


                        return;

                    }


                    /*
                     * BACKEND ERROR
                     */

                    message.textContent =
                        data.error ||
                        data.message ||
                        "Unable to reset password.";

                    message.classList.add(
                        "show"
                    );


                }
                catch(error) {

                    console.error(
                        "NeonSocial password reset error:",
                        error
                    );


                    message.textContent =
                        "Unable to connect to NeonSocial AI server.";

                    message.classList.add(
                        "show"
                    );

                }
                finally {

                    resetButton.disabled =
                        false;

                    resetButton.innerHTML =
                        originalHTML;

                }

            }
        );


        console.log(
            "NeonSocial: password reset system ready."
        );

    }


    /*
     * Wait until DOM is ready.
     */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            setupPasswordReset
        );

    }
    else {

        setupPasswordReset();

    }

})();
