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