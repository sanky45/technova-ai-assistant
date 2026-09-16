(() => {
    "use strict";


    // =========================================================
    // CONFIGURATION
    // =========================================================

    const API_ENDPOINT = "/api/ask";

    const CONVERSATIONS_ENDPOINT =
        "/api/conversations";

    const ACTIVE_CONVERSATION_KEY =
        "kstore_ai_active_conversation";

    const THEME_KEY =
        "kstore_ai_theme";

    const ACCESS_TOKEN_KEY =
        "kstore_ai_access_token";

    const REMEMBER_ME_KEY =
        "kstore_ai_remember_me";


    // =========================================================
    // DOM ELEMENTS
    // =========================================================

    const chatMessages =
        document.getElementById("chatMessages");

    const welcomeState =
        document.getElementById("welcomeState");

    const chatForm =
        document.getElementById("chatForm");

    const questionInput =
        document.getElementById("questionInput");

    const sendBtn =
        document.getElementById("sendBtn");

    const conversationList =
        document.getElementById("conversationList");

    const sidebar =
        document.getElementById("sidebar");

    const sidebarOverlay =
        document.getElementById("sidebarOverlay");

    const logoutBtn =
        document.getElementById("logoutBtn");


    // =========================================================
    // APPLICATION STATE
    // =========================================================

    let conversations = [];

    let activeConversation = null;

    let isRequestInProgress = false;


    // =========================================================
    // AUTHENTICATION
    // =========================================================

    function getAccessToken() {

        const rememberedToken =
            localStorage.getItem(
                ACCESS_TOKEN_KEY
            );

        if (rememberedToken) {
            return rememberedToken;
        }


        const sessionToken =
            sessionStorage.getItem(
                ACCESS_TOKEN_KEY
            );

        return sessionToken;
    }


    function requireAuthentication() {

        const token =
            getAccessToken();

        if (!token) {

            window.location.href =
                "/login.html";

            return false;
        }

        return true;
    }


    function handleUnauthorized() {

        localStorage.removeItem(
            ACCESS_TOKEN_KEY
        );

        localStorage.removeItem(
            REMEMBER_ME_KEY
        );

        sessionStorage.removeItem(
            ACCESS_TOKEN_KEY
        );


        alert(
            "Your session has expired. Please sign in again."
        );


        window.location.href =
            "/login.html";
    }


    function logout() {

        const confirmed =
            window.confirm(
                "Are you sure you want to sign out?"
            );

        if (!confirmed) {
            return;
        }


        localStorage.removeItem(
            ACCESS_TOKEN_KEY
        );

        localStorage.removeItem(
            REMEMBER_ME_KEY
        );

        sessionStorage.removeItem(
            ACCESS_TOKEN_KEY
        );

        localStorage.removeItem(
            ACTIVE_CONVERSATION_KEY
        );


        window.location.href =
            "/login.html";
    }


    // =========================================================
    // API HELPER
    // =========================================================

    async function apiFetch(
        url,
        options = {}
    ) {

        const token =
            getAccessToken();


        if (!token) {

            handleUnauthorized();

            return null;
        }


        const headers = {

            "Accept":
                "application/json",

            "Authorization":
                `Bearer ${token}`

        };


        if (options.body) {

            headers["Content-Type"] =
                "application/json";
        }


        if (options.headers) {

            Object.assign(
                headers,
                options.headers
            );
        }


        let response;


        try {

            response =
                await fetch(
                    url,
                    {
                        ...options,
                        headers
                    }
                );

        } catch (error) {

            throw new Error(
                "Unable to connect to the server. Please check your connection."
            );
        }


        if (
            response.status === 401
        ) {

            handleUnauthorized();

            return null;
        }


        return response;
    }


    async function parseApiResponse(
        response
    ) {

        if (!response) {
            return null;
        }


        let data = {};


        try {

            data =
                await response.json();

        } catch {

            throw new Error(
                "The server returned an invalid response."
            );
        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                `Request failed (${response.status})`
            );
        }


        return data;
    }


    // =========================================================
    // SESSION ID
    // =========================================================

    function createSessionId() {

        if (
            window.crypto &&
            window.crypto.randomUUID
        ) {

            return window.crypto.randomUUID();
        }


        return (
            "session-" +
            Date.now() +
            "-" +
            Math.random()
                .toString(36)
                .substring(2)
        );
    }


    // =========================================================
    // ACTIVE CONVERSATION
    // =========================================================

    function getActiveConversationId() {

        return localStorage.getItem(
            ACTIVE_CONVERSATION_KEY
        );
    }


    function setActiveConversationId(
        sessionId
    ) {

        localStorage.setItem(
            ACTIVE_CONVERSATION_KEY,
            sessionId
        );
    }


    function createNewConversation() {

        const sessionId =
            createSessionId();


        activeConversation = {

            id:
                sessionId,

            title:
                "New conversation",

            messages:
                []

        };


        setActiveConversationId(
            sessionId
        );


        renderActiveConversation();

        renderConversationList();

        questionInput.focus();

    }


    // =========================================================
    // LOAD CONVERSATION LIST
    // =========================================================

    async function loadConversationList() {

        try {

            const response =
                await apiFetch(
                    CONVERSATIONS_ENDPOINT
                );


            if (!response) {
                return false;
            }


            const data =
                await parseApiResponse(
                    response
                );


            conversations =
                Array.isArray(
                    data.conversations
                )
                    ? data.conversations
                    : [];


            renderConversationList();


            return true;

        } catch (error) {

            console.error(
                "Unable to load conversations:",
                error
            );


            conversationList.innerHTML = `

                <div class="empty-conversations">

                    Unable to load conversations

                </div>

            `;


            return false;
        }
    }


    // =========================================================
    // LOAD SINGLE CONVERSATION
    // =========================================================

    async function loadConversation(
        sessionId
    ) {

        if (!sessionId) {
            return false;
        }


        try {

            const response =
                await apiFetch(
                    `${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(sessionId)}`
                );


            if (!response) {
                return false;
            }


            const data =
                await parseApiResponse(
                    response
                );


            const existingConversation =
                conversations.find(
                    conversation =>
                        conversation.session_id ===
                        data.session_id
                );


            activeConversation = {

                id:
                    data.session_id,

                title:
                    existingConversation?.title ||
                    "New conversation",

                messages:
                    Array.isArray(
                        data.messages
                    )
                        ? data.messages
                        : []

            };


            setActiveConversationId(
                activeConversation.id
            );


            renderActiveConversation();

            renderConversationList();

            questionInput.focus();

            scrollToBottom();


            return true;

        } catch (error) {

            console.error(
                "Unable to load conversation:",
                error
            );


            return false;
        }
    }


    // =========================================================
    // INITIALIZE ACTIVE CONVERSATION
    // =========================================================

    async function initializeConversation() {

        const loaded =
            await loadConversationList();


        if (!loaded) {

            createNewConversation();

            return;
        }


        const savedConversationId =
            getActiveConversationId();


        if (savedConversationId) {

            const exists =
                conversations.some(
                    conversation =>
                        conversation.session_id ===
                        savedConversationId
                );


            if (exists) {

                const loadedConversation =
                    await loadConversation(
                        savedConversationId
                    );


                if (
                    loadedConversation
                ) {

                    return;
                }
            }
        }


        /*
         * No previously selected conversation.
         *
         * Open the newest existing conversation.
         */

        if (conversations.length > 0) {

            const newestConversation =
                conversations[0];


            const loadedConversation =
                await loadConversation(
                    newestConversation.session_id
                );


            if (
                loadedConversation
            ) {

                return;
            }
        }


        /*
         * User has no conversations yet.
         *
         * Create an empty frontend session.
         *
         * It will only exist in Redis after
         * the first message is sent.
         */

        createNewConversation();
    }


    // =========================================================
    // DELETE / CLEAR CONVERSATION
    // =========================================================

    async function clearCurrentConversation() {

        if (!activeConversation) {
            return;
        }


        if (
            !activeConversation.messages ||
            activeConversation.messages.length === 0
        ) {

            return;
        }


        const confirmed =
            window.confirm(
                "Clear this conversation?"
            );


        if (!confirmed) {
            return;
        }


        try {

            const response =
                await apiFetch(
                    `${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(
                        activeConversation.id
                    )}`,
                    {
                        method:
                            "DELETE"
                    }
                );


            if (!response) {
                return;
            }


            await parseApiResponse(
                response
            );


            /*
             * Remove from local UI state.
             */

            conversations =
                conversations.filter(
                    conversation =>
                        conversation.session_id !==
                        activeConversation.id
                );


            /*
             * Remove active conversation
             * reference.
             */

            activeConversation =
                null;


            localStorage.removeItem(
                ACTIVE_CONVERSATION_KEY
            );


            /*
             * Refresh sidebar.
             */

            renderConversationList();


            /*
             * Open another conversation
             * if one exists.
             */

            if (
                conversations.length > 0
            ) {

                await loadConversation(
                    conversations[0].session_id
                );

            } else {

                createNewConversation();
            }


        } catch (error) {

            console.error(
                "Unable to delete conversation:",
                error
            );


            alert(
                error.message ||
                "Unable to clear the conversation."
            );
        }
    }


    // =========================================================
    // SWITCH CONVERSATION
    // =========================================================

    async function switchConversation(
        conversationId
    ) {

        if (
            !conversationId ||
            isRequestInProgress
        ) {

            return;
        }


        if (
            activeConversation &&
            activeConversation.id ===
                conversationId
        ) {

            closeSidebar();

            questionInput.focus();

            return;
        }


        const previousConversation =
            activeConversation;


        /*
         * Prevent accidental duplicate clicks
         * while loading history.
         */

        isRequestInProgress = true;


        try {

            const loaded =
                await loadConversation(
                    conversationId
                );


            if (!loaded) {

                activeConversation =
                    previousConversation;

                return;
            }


            closeSidebar();

            scrollToBottom();

        } finally {

            isRequestInProgress = false;
        }
    }


    // =========================================================
    // HTML SAFETY
    // =========================================================

    function escapeHtml(
        value
    ) {

        return String(
            value ?? ""
        )

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


    // =========================================================
    // INLINE MARKDOWN
    // =========================================================

    function formatInlineMarkdown(
        text
    ) {

        let html =
            text;


        /*
         * Inline code
         */

        html =
            html.replace(
                /`([^`]+)`/g,
                '<code class="inline-code">$1</code>'
            );


        /*
         * Bold
         */

        html =
            html.replace(
                /\*\*(.+?)\*\*/g,
                "<strong>$1</strong>"
            );


        /*
         * Italic
         */

        html =
            html.replace(
                /(?<!\*)\*([^*]+)\*(?!\*)/g,
                "<em>$1</em>"
            );


        /*
         * Preserve multiple spaces.
         */

        html =
            html.replace(
                / {2,}/g,
                match =>
                    "&nbsp;".repeat(
                        match.length
                    )
            );


        return html;
    }


    // =========================================================
    // FORMAT AI ANSWER
    // =========================================================

    function formatAnswer(
        text
    ) {

        const escaped =
            escapeHtml(text);


        const lines =
            escaped.split("\n");


        const output = [];

        let inCodeBlock =
            false;

        let codeLines = [];


        for (
            let i = 0;
            i < lines.length;
            i++
        ) {

            const line =
                lines[i];


            // ---------------------------------------------
            // CODE BLOCK
            // ---------------------------------------------

            if (
                line.trim().startsWith("```")
            ) {

                if (!inCodeBlock) {

                    inCodeBlock = true;

                    codeLines = [];

                } else {

                    output.push(
                        `
                        <pre class="code-block"><code>${codeLines.join("\n")}</code></pre>
                        `
                    );


                    inCodeBlock = false;

                    codeLines = [];
                }


                continue;
            }


            if (inCodeBlock) {

                codeLines.push(
                    line
                );

                continue;
            }


            // ---------------------------------------------
            // EMPTY LINE
            // ---------------------------------------------

            if (!line.trim()) {

                output.push(
                    `<div class="answer-spacer"></div>`
                );

                continue;
            }


            // ---------------------------------------------
            // H3
            // ---------------------------------------------

            if (
                line.startsWith("### ")
            ) {

                output.push(
                    `
                    <h4>
                        ${formatInlineMarkdown(
                            line.substring(4)
                        )}
                    </h4>
                    `
                );

                continue;
            }


            // ---------------------------------------------
            // H2
            // ---------------------------------------------

            if (
                line.startsWith("## ")
            ) {

                output.push(
                    `
                    <h3>
                        ${formatInlineMarkdown(
                            line.substring(3)
                        )}
                    </h3>
                    `
                );

                continue;
            }


            // ---------------------------------------------
            // H1
            // ---------------------------------------------

            if (
                line.startsWith("# ")
            ) {

                output.push(
                    `
                    <h2>
                        ${formatInlineMarkdown(
                            line.substring(2)
                        )}
                    </h2>
                    `
                );

                continue;
            }


            // ---------------------------------------------
            // BULLET
            // ---------------------------------------------

            if (
                /^[-*]\s+/.test(line)
            ) {

                const bulletText =
                    line.replace(
                        /^[-*]\s+/,
                        ""
                    );


                output.push(
                    `
                    <div class="answer-list-item">

                        <span class="list-bullet">
                            •
                        </span>

                        <span>
                            ${formatInlineMarkdown(
                                bulletText
                            )}
                        </span>

                    </div>
                    `
                );

                continue;
            }


            // ---------------------------------------------
            // NUMBERED LIST
            // ---------------------------------------------

            const numberedMatch =
                line.match(
                    /^(\d+)\.\s+(.*)$/
                );


            if (numberedMatch) {

                output.push(
                    `
                    <div class="answer-list-item">

                        <span class="list-number">
                            ${numberedMatch[1]}.
                        </span>

                        <span>
                            ${formatInlineMarkdown(
                                numberedMatch[2]
                            )}
                        </span>

                    </div>
                    `
                );

                continue;
            }


            // ---------------------------------------------
            // NORMAL PARAGRAPH
            // ---------------------------------------------

            output.push(
                `
                <p>
                    ${formatInlineMarkdown(line)}
                </p>
                `
            );
        }


        /*
         * Handle unclosed code blocks.
         */

        if (
            inCodeBlock &&
            codeLines.length > 0
        ) {

            output.push(
                `
                <pre class="code-block"><code>${codeLines.join("\n")}</code></pre>
                `
            );
        }


        return output.join("");
    }


    // =========================================================
    // SOURCE LABEL
    // =========================================================

    function getSourceLabel(
        source
    ) {

        if (
            source.page !== null &&
            source.page !== undefined
        ) {

            return `Page ${source.page}`;
        }


        if (
            source.slide !== null &&
            source.slide !== undefined
        ) {

            return `Slide ${source.slide}`;
        }


        return "Document";
    }


    // =========================================================
    // SOURCE CARD
    // =========================================================

    function renderSource(
        source
    ) {

        const fileName =
            source.file_name ||
            "Unknown document";


        const lowerName =
            fileName.toLowerCase();


        let fileType =
            "FILE";


        if (
            lowerName.endsWith(".pdf")
        ) {

            fileType = "PDF";

        } else if (
            lowerName.endsWith(".pptx")
        ) {

            fileType = "PPT";

        } else if (
            lowerName.endsWith(".docx")
        ) {

            fileType = "DOC";

        } else if (
            lowerName.endsWith(".txt")
        ) {

            fileType = "TXT";

        } else if (
            lowerName.endsWith(".png") ||
            lowerName.endsWith(".jpg") ||
            lowerName.endsWith(".jpeg")
        ) {

            fileType = "IMG";
        }


        return `
            <div class="source-card">

                <div class="source-icon">
                    ${fileType}
                </div>

                <div class="source-info">

                    <strong>
                        ${escapeHtml(fileName)}
                    </strong>

                    <span>
                        ${escapeHtml(
                            getSourceLabel(source)
                        )}
                    </span>

                </div>

            </div>
        `;
    }


    // =========================================================
    // USER MESSAGE
    // =========================================================

    function renderUserMessage(
        text
    ) {

        return `
            <article class="message-row user-row">

                <div class="avatar user-avatar">
                    You
                </div>

                <div class="message-content">

                    <div class="message-name">
                        You
                    </div>

                    <div class="user-bubble">

                        ${escapeHtml(text)
                            .replace(
                                /\n/g,
                                "<br>"
                            )}

                    </div>

                </div>

            </article>
        `;
    }


    // =========================================================
    // ASSISTANT MESSAGE
    // =========================================================

    function renderAssistantMessage(
        answer,
        sources = []
    ) {

        let sourcesHtml =
            "";


        if (
            sources.length > 0
        ) {

            sourcesHtml = `
                <div class="sources-block">

                    <div class="sources-title">
                        Sources
                    </div>

                    ${sources
                        .map(renderSource)
                        .join("")}

                </div>
            `;
        }


        return `
            <article class="message-row assistant-row">

                <div class="avatar ai-avatar">
                    K
                </div>

                <div class="message-content">

                    <div class="message-name">
                        KStore AI
                    </div>

                    <div class="assistant-bubble">

                        <div class="answer-text">

                            ${formatAnswer(answer)}

                        </div>

                        ${sourcesHtml}

                    </div>

                </div>

            </article>
        `;
    }


    // =========================================================
    // LOADING MESSAGE
    // =========================================================

    function renderLoadingMessage() {

        return `
            <article
                class="message-row assistant-row"
                id="loadingMessage"
            >

                <div class="avatar ai-avatar">
                    K
                </div>

                <div class="message-content">

                    <div class="message-name">
                        KStore AI
                    </div>

                    <div class="assistant-bubble loading-bubble">

                        <span class="typing-dot"></span>

                        <span class="typing-dot"></span>

                        <span class="typing-dot"></span>

                    </div>

                </div>

            </article>
        `;
    }


    // =========================================================
    // ERROR MESSAGE
    // =========================================================

    function renderErrorMessage(
        errorMessage,
        question
    ) {

        return `
            <article
                class="message-row assistant-row"
            >

                <div class="avatar ai-avatar">
                    K
                </div>

                <div class="message-content">

                    <div class="message-name">
                        KStore AI
                    </div>

                    <div class="assistant-bubble error-bubble">

                        <strong>
                            Unable to get an answer
                        </strong>

                        <p>
                            ${escapeHtml(
                                errorMessage ||
                                "Something went wrong while contacting the server."
                            )}
                        </p>

                        <button
                            class="retry-btn"
                            type="button"
                            data-retry="${escapeHtml(
                                question
                            )}"
                        >
                            Try again
                        </button>

                    </div>

                </div>

            </article>
        `;
    }


    // =========================================================
    // RENDER ACTIVE CONVERSATION
    // =========================================================

    function renderActiveConversation() {

        if (
            !activeConversation ||
            !activeConversation.messages ||
            activeConversation.messages.length === 0
        ) {

            chatMessages.innerHTML =
                welcomeState
                    ? welcomeState.outerHTML
                    : "";


            attachSuggestionButtons();

            return;
        }


        chatMessages.innerHTML =
            activeConversation.messages
                .map(
                    message => {

                        if (
                            message.role ===
                            "user"
                        ) {

                            return renderUserMessage(
                                message.content
                            );
                        }


                        return renderAssistantMessage(
                            message.content,
                            message.sources ||
                            []
                        );
                    }
                )
                .join("");


        scrollToBottom();
    }


    // =========================================================
    // RENDER CONVERSATION LIST
    // =========================================================

    function renderConversationList() {

        conversationList.innerHTML =
            "";


        if (
            conversations.length === 0
        ) {

            conversationList.innerHTML = `
                <div class="empty-conversations">
                    No conversations yet
                </div>
            `;

            return;
        }


        conversations
            .forEach(
                conversation => {

                    const button =
                        document.createElement(
                            "button"
                        );


                    button.type =
                        "button";


                    button.className =
                        "conversation-item";


                    if (
                        activeConversation &&
                        conversation.session_id ===
                            activeConversation.id
                    ) {

                        button.classList.add(
                            "active"
                        );
                    }


                    button.textContent =
                        conversation.title ||
                        "New conversation";


                    button.title =
                        conversation.title ||
                        "New conversation";


                    button.addEventListener(
                        "click",
                        () => {

                            switchConversation(
                                conversation.session_id
                            );

                        }
                    );


                    conversationList.appendChild(
                        button
                    );

                }
            );
    }


    // =========================================================
    // SCROLL
    // =========================================================

    function scrollToBottom() {

        requestAnimationFrame(
            () => {

                chatMessages.scrollTop =
                    chatMessages.scrollHeight;

            }
        );
    }


    // =========================================================
    // LOADING STATE
    // =========================================================

    function setLoading(
        isLoading
    ) {

        isRequestInProgress =
            isLoading;


        sendBtn.disabled =
            isLoading;


        questionInput.disabled =
            isLoading;


        const existingLoading =
            document.getElementById(
                "loadingMessage"
            );


        if (
            isLoading &&
            !existingLoading
        ) {

            chatMessages.insertAdjacentHTML(
                "beforeend",
                renderLoadingMessage()
            );


            scrollToBottom();
        }


        if (
            !isLoading &&
            existingLoading
        ) {

            existingLoading.remove();
        }
    }


    // =========================================================
    // ASK QUESTION
    // =========================================================

    async function askQuestion(
        question
    ) {

        const cleanQuestion =
            question.trim();


        if (!cleanQuestion) {
            return;
        }


        if (isRequestInProgress) {
            return;
        }


        if (
            !requireAuthentication()
        ) {

            return;
        }


        /*
         * If no active conversation exists,
         * create one.
         */

        if (!activeConversation) {

            createNewConversation();
        }


        const conversation =
            activeConversation;


        /*
         * Remove welcome screen.
         */

        const currentWelcome =
            document.getElementById(
                "welcomeState"
            );


        if (currentWelcome) {

            currentWelcome.remove();
        }


        /*
         * Add user message immediately
         * for responsive UI.
         */

        conversation.messages.push({

            role:
                "user",

            content:
                cleanQuestion,

            timestamp:
                Date.now()

        });


        /*
         * Update local title for immediate UI.
         *
         * Backend remains the source of truth
         * after the request completes.
         */

        if (
            conversation.messages.length === 1
        ) {

            conversation.title =
                cleanQuestion.length > 45

                    ? cleanQuestion.substring(
                        0,
                        45
                    ) + "…"

                    : cleanQuestion;
        }


        renderActiveConversation();

        renderConversationList();


        questionInput.value =
            "";


        resizeInput();


        setLoading(true);


        try {

            const response =
                await apiFetch(
                    API_ENDPOINT,
                    {

                        method:
                            "POST",

                        body:
                            JSON.stringify({

                                session_id:
                                    conversation.id,

                                question:
                                    cleanQuestion

                            })

                    }
                );


            if (!response) {
                return;
            }


            const data =
                await parseApiResponse(
                    response
                );


            const answer =
                data.answer ||
                "I couldn't generate an answer.";


            const sources =
                Array.isArray(
                    data.sources
                )
                    ? data.sources
                    : [];


            /*
             * Add assistant response.
             */

            conversation.messages.push({

                role:
                    "assistant",

                content:
                    answer,

                sources:
                    sources,

                timestamp:
                    Date.now()

            });


            /*
             * Backend has now persisted
             * the conversation.
             *
             * Refresh sidebar so the title
             * and ordering match Redis.
             */

            await loadConversationList();


            setLoading(false);


            renderActiveConversation();

            renderConversationList();

            scrollToBottom();


        } catch (error) {

            console.error(
                "KStore AI request failed:",
                error
            );


            /*
             * Remove the optimistic user message
             * because the backend request failed.
             */

            conversation.messages =
                conversation.messages.filter(
                    message =>
                        !(
                            message.role ===
                                "user" &&
                            message.content ===
                                cleanQuestion &&
                            message.timestamp
                        )
                );


            setLoading(false);


            renderActiveConversation();


            chatMessages.insertAdjacentHTML(
                "beforeend",
                renderErrorMessage(
                    error.message,
                    cleanQuestion
                )
            );


            scrollToBottom();

        } finally {

            isRequestInProgress =
                false;


            questionInput.disabled =
                false;


            sendBtn.disabled =
                false;


            questionInput.focus();
        }
    }


    // =========================================================
    // NEW CHAT
    // =========================================================

    function newChat() {

        /*
         * IMPORTANT:
         *
         * We do NOT delete previous
         * conversations.
         *
         * We simply create a new session ID.
         *
         * The backend will create the Redis
         * conversation once the first message
         * is sent.
         */

        createNewConversation();

        closeSidebar();

        questionInput.focus();
    }


    // =========================================================
    // INPUT RESIZE
    // =========================================================

    function resizeInput() {

        questionInput.style.height =
            "auto";


        questionInput.style.height =
            Math.min(
                questionInput.scrollHeight,
                160
            ) + "px";
    }


    // =========================================================
    // SUGGESTED QUESTIONS
    // =========================================================

    function attachSuggestionButtons() {

        document
            .querySelectorAll(
                ".suggestion"
            )
            .forEach(
                button => {

                    /*
                     * Avoid attaching duplicate
                     * listeners when welcome screen
                     * is rendered repeatedly.
                     */

                    if (
                        button.dataset.bound ===
                        "true"
                    ) {

                        return;
                    }


                    button.dataset.bound =
                        "true";


                    button.addEventListener(
                        "click",
                        () => {

                            const question =
                                button.dataset.question;


                            askQuestion(
                                question
                            );

                        }
                    );

                }
            );
    }


    // =========================================================
    // THEME
    // =========================================================

    function setupTheme() {

        const savedTheme =
            localStorage.getItem(
                THEME_KEY
            );


        if (
            savedTheme === "light"
        ) {

            document.body.classList.add(
                "light-theme"
            );
        }


        updateThemeLabel();
    }


    function updateThemeLabel() {

        const isLight =
            document.body.classList.contains(
                "light-theme"
            );


        const themeLabel =
            document.getElementById(
                "themeLabel"
            );


        if (themeLabel) {

            themeLabel.textContent =
                isLight
                    ? "Dark mode"
                    : "Light mode";
        }
    }


    // =========================================================
    // SIDEBAR
    // =========================================================

    function openSidebar() {

        sidebar.classList.add(
            "open"
        );


        sidebarOverlay.classList.add(
            "visible"
        );
    }


    function closeSidebar() {

        sidebar.classList.remove(
            "open"
        );


        sidebarOverlay.classList.remove(
            "visible"
        );
    }


    // =========================================================
    // EVENT LISTENERS
    // =========================================================

    const newChatBtn =
        document.getElementById(
            "newChatBtn"
        );


    if (newChatBtn) {

        newChatBtn.addEventListener(
            "click",
            newChat
        );
    }


    const clearChatBtn =
        document.getElementById(
            "clearChatBtn"
        );


    if (clearChatBtn) {

        clearChatBtn.addEventListener(
            "click",
            clearCurrentConversation
        );
    }


    const themeBtn =
        document.getElementById(
            "themeBtn"
        );


    if (themeBtn) {

        themeBtn.addEventListener(
            "click",
            () => {

                document.body.classList.toggle(
                    "light-theme"
                );


                const isLight =
                    document.body.classList.contains(
                        "light-theme"
                    );


                localStorage.setItem(
                    THEME_KEY,
                    isLight
                        ? "light"
                        : "dark"
                );


                updateThemeLabel();

            }
        );
    }


    const openSidebarBtn =
        document.getElementById(
            "openSidebar"
        );


    if (openSidebarBtn) {

        openSidebarBtn.addEventListener(
            "click",
            openSidebar
        );
    }


    const closeSidebarBtn =
        document.getElementById(
            "closeSidebar"
        );


    if (closeSidebarBtn) {

        closeSidebarBtn.addEventListener(
            "click",
            closeSidebar
        );
    }


    if (sidebarOverlay) {

        sidebarOverlay.addEventListener(
            "click",
            closeSidebar
        );
    }


    if (logoutBtn) {

        logoutBtn.addEventListener(
            "click",
            logout
        );
    }


    // =========================================================
    // CHAT FORM
    // =========================================================

    if (chatForm) {

        chatForm.addEventListener(
            "submit",
            event => {

                event.preventDefault();


                askQuestion(
                    questionInput.value
                );

            }
        );
    }


    // =========================================================
    // ENTER / SHIFT + ENTER
    // =========================================================

    if (questionInput) {

        questionInput.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();


                    chatForm.requestSubmit();
                }
            }
        );


        questionInput.addEventListener(
            "input",
            resizeInput
        );
    }


    // =========================================================
    // RETRY
    // =========================================================

    if (chatMessages) {

        chatMessages.addEventListener(
            "click",
            event => {

                const retryButton =
                    event.target.closest(
                        ".retry-btn"
                    );


                if (!retryButton) {
                    return;
                }


                const question =
                    retryButton.dataset.retry;


                if (!question) {
                    return;
                }


                askQuestion(
                    question
                );

            }
        );
    }


    // =========================================================
    // INITIALIZATION
    // =========================================================

    async function initialize() {

        /*
         * Authentication first.
         */

        if (
            !requireAuthentication()
        ) {

            return;
        }


        /*
         * Theme.
         */

        setupTheme();


        /*
         * Load Redis-backed conversations.
         */

        await initializeConversation();


        /*
         * UI initialization.
         */

        resizeInput();

        attachSuggestionButtons();

        questionInput.focus();

    }


    initialize();

})();