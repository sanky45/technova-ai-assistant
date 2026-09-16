(() => {
    "use strict";


    // =========================================================
    // CONFIGURATION
    // =========================================================

    const LOGIN_ENDPOINT = "/login";

    const ACCESS_TOKEN_KEY =
        "kstore_ai_access_token";

    const REMEMBER_ME_KEY =
        "kstore_ai_remember_me";


    // =========================================================
    // DOM ELEMENTS
    // =========================================================

    const form =
        document.getElementById("loginForm");

    const emailInput =
        document.getElementById("email");

    const passwordInput =
        document.getElementById("password");

    const rememberMe =
        document.getElementById("rememberMe");

    const loginBtn =
        document.getElementById("loginBtn");

    const loginBtnText =
        document.getElementById("loginBtnText");

    const loginSpinner =
        document.getElementById("loginSpinner");

    const loginError =
        document.getElementById("loginError");

    const loginSuccess =
        document.getElementById("loginSuccess");

    const emailError =
        document.getElementById("emailError");

    const passwordError =
        document.getElementById("passwordError");

    const togglePassword =
        document.getElementById("togglePassword");

    const forgotPasswordBtn =
        document.getElementById(
            "forgotPasswordBtn"
        );


    // =========================================================
    // EXISTING SESSION CHECK
    // =========================================================

    function hasExistingToken() {

        return Boolean(
            localStorage.getItem(
                ACCESS_TOKEN_KEY
            ) ||
            sessionStorage.getItem(
                ACCESS_TOKEN_KEY
            )
        );
    }


    /*
     * If the user already has a valid-looking
     * session token, send them directly to chat.
     *
     * The backend will still validate the token
     * whenever an authenticated API request is made.
     */

    if (hasExistingToken()) {

        window.location.replace(
            "/chat.html"
        );

        return;
    }


    // =========================================================
    // UI HELPERS
    // =========================================================

    function showError(message) {

        loginError.textContent =
            message;

        loginError.hidden =
            false;

        loginSuccess.hidden =
            true;
    }


    function showSuccess(message) {

        loginSuccess.textContent =
            message;

        loginSuccess.hidden =
            false;

        loginError.hidden =
            true;
    }


    function clearAlerts() {

        loginError.hidden =
            true;

        loginSuccess.hidden =
            true;

        loginError.textContent =
            "";

        loginSuccess.textContent =
            "";
    }


    function clearFieldErrors() {

        emailError.textContent =
            "";

        passwordError.textContent =
            "";


        document
            .querySelectorAll(
                ".input-wrap.invalid"
            )
            .forEach(
                element => {

                    element.classList.remove(
                        "invalid"
                    );

                }
            );
    }


    function setFieldError(
        input,
        errorElement,
        message
    ) {

        errorElement.textContent =
            message;


        const wrapper =
            input.closest(
                ".input-wrap"
            );


        if (wrapper) {

            wrapper.classList.add(
                "invalid"
            );
        }
    }


    // =========================================================
    // LOADING STATE
    // =========================================================

    function setLoading(
        loading
    ) {

        loginBtn.disabled =
            loading;

        emailInput.disabled =
            loading;

        passwordInput.disabled =
            loading;

        rememberMe.disabled =
            loading;


        loginBtnText.textContent =
            loading
                ? "Signing in..."
                : "Sign in";


        loginSpinner.hidden =
            !loading;


        const arrow =
            loginBtn.querySelector(
                ".button-arrow"
            );


        if (arrow) {

            arrow.hidden =
                loading;
        }
    }


    // =========================================================
    // PASSWORD VISIBILITY
    // =========================================================

    togglePassword.addEventListener(
        "click",
        () => {

            const isPassword =
                passwordInput.type ===
                "password";


            if (isPassword) {

                passwordInput.type =
                    "text";

                togglePassword.textContent =
                    "Hide";

                togglePassword.setAttribute(
                    "aria-label",
                    "Hide password"
                );

                togglePassword.setAttribute(
                    "title",
                    "Hide password"
                );

            } else {

                passwordInput.type =
                    "password";

                togglePassword.textContent =
                    "Show";

                togglePassword.setAttribute(
                    "aria-label",
                    "Show password"
                );

                togglePassword.setAttribute(
                    "title",
                    "Show password"
                );
            }
        }
    );


    // =========================================================
    // EMAIL VALIDATION
    // =========================================================

    function isValidEmail(
        email
    ) {

        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            .test(email);
    }


    // =========================================================
    // FORM VALIDATION
    // =========================================================

    function validateForm() {

        clearFieldErrors();


        const email =
            emailInput.value.trim();

        const password =
            passwordInput.value;


        let valid =
            true;


        // Email

        if (!email) {

            setFieldError(
                emailInput,
                emailError,
                "Email address is required."
            );

            valid =
                false;

        } else if (
            !isValidEmail(email)
        ) {

            setFieldError(
                emailInput,
                emailError,
                "Enter a valid email address."
            );

            valid =
                false;
        }


        // Password

        if (!password) {

            setFieldError(
                passwordInput,
                passwordError,
                "Password is required."
            );

            valid =
                false;
        }


        return valid;
    }


    // =========================================================
    // LOGIN REQUEST
    // =========================================================

    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            clearAlerts();


            // Validate before calling backend

            if (!validateForm()) {

                return;
            }


            const email =
                emailInput.value.trim();

            const password =
                passwordInput.value;


            setLoading(
                true
            );


            try {

                // ---------------------------------------------
                // Call FastAPI login endpoint
                // ---------------------------------------------

                const response =
                    await fetch(
                        LOGIN_ENDPOINT,
                        {
                            method: "POST",

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

                                    password:
                                        password
                                })
                        }
                    );


                let data =
                    {};


                // ---------------------------------------------
                // Parse response
                // ---------------------------------------------

                try {

                    data =
                        await response.json();

                } catch {

                    throw new Error(
                        "The server returned an invalid response."
                    );
                }


                // ---------------------------------------------
                // Backend returned an error
                // ---------------------------------------------

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        data.error ||
                        "Invalid email or password."
                    );
                }


                // ---------------------------------------------
                // Validate JWT response
                // ---------------------------------------------

                if (
                    !data.access_token
                ) {

                    throw new Error(
                        "Login succeeded but no access token was returned."
                    );
                }


                // =================================================
                // STORE JWT
                // =================================================

                /*
                 * Remember me checked:
                 *
                 *     localStorage
                 *
                 * The token survives browser restarts.
                 *
                 *
                 * Remember me unchecked:
                 *
                 *     sessionStorage
                 *
                 * The token is removed when the browser
                 * session ends.
                 */


                if (
                    rememberMe.checked
                ) {

                    localStorage.setItem(
                        ACCESS_TOKEN_KEY,
                        data.access_token
                    );

                    localStorage.setItem(
                        REMEMBER_ME_KEY,
                        "true"
                    );


                    // Remove any old session token

                    sessionStorage.removeItem(
                        ACCESS_TOKEN_KEY
                    );

                    sessionStorage.removeItem(
                        REMEMBER_ME_KEY
                    );

                } else {

                    sessionStorage.setItem(
                        ACCESS_TOKEN_KEY,
                        data.access_token
                    );

                    sessionStorage.setItem(
                        REMEMBER_ME_KEY,
                        "false"
                    );


                    // Remove any old persistent token

                    localStorage.removeItem(
                        ACCESS_TOKEN_KEY
                    );

                    localStorage.removeItem(
                        REMEMBER_ME_KEY
                    );
                }


                // =================================================
                // SUCCESS
                // =================================================

                showSuccess(
                    "Signed in successfully. Redirecting..."
                );


                // Small delay so the user sees success state

                setTimeout(
                    () => {

                        window.location.replace(
                            "/chat.html"
                        );

                    },
                    350
                );


            } catch (error) {

                console.error(
                    "KStore AI login failed:",
                    error
                );


                showError(
                    error.message ||
                    "Unable to sign in. Please try again."
                );


            } finally {

                setLoading(
                    false
                );
            }
        }
    );


    // =========================================================
    // LIVE EMAIL VALIDATION
    // =========================================================

    emailInput.addEventListener(
        "input",
        () => {

            emailError.textContent =
                "";


            const wrapper =
                emailInput.closest(
                    ".input-wrap"
                );


            if (wrapper) {

                wrapper.classList.remove(
                    "invalid"
                );
            }


            clearAlerts();
        }
    );


    // =========================================================
    // LIVE PASSWORD VALIDATION
    // =========================================================

    passwordInput.addEventListener(
        "input",
        () => {

            passwordError.textContent =
                "";


            const wrapper =
                passwordInput.closest(
                    ".input-wrap"
                );


            if (wrapper) {

                wrapper.classList.remove(
                    "invalid"
                );
            }


            clearAlerts();
        }
    );


    // =========================================================
    // FORGOT PASSWORD
    // =========================================================

    /*
     * We don't currently have a password-reset
     * backend endpoint.
     *
     * Therefore we don't pretend that this feature
     * is functional yet.
     *
     * Later we can build:
     *
     *     POST /forgot-password
     *     POST /reset-password
     *
     * with email verification/token flow.
     */

    forgotPasswordBtn.addEventListener(
        "click",
        () => {

            showError(
                "Password recovery is not enabled yet. Please contact your administrator."
            );
        }
    );


    // =========================================================
    // INITIAL PAGE STATE
    // =========================================================

    clearAlerts();

    clearFieldErrors();


    // Put cursor in email field

    emailInput.focus();

})();