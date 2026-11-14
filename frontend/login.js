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
    // DOM
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
    // EXISTING SESSION
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
     * If the user is already authenticated,
     * don't make them sign in again.
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

            const showing =
                passwordInput.type ===
                "text";


            passwordInput.type =
                showing
                    ? "password"
                    : "text";


            togglePassword.textContent =
                showing
                    ? "Show"
                    : "Hide";


            togglePassword.setAttribute(
                "aria-label",
                showing
                    ? "Show password"
                    : "Hide password"
            );


            togglePassword.setAttribute(
                "title",
                showing
                    ? "Show password"
                    : "Hide password"
            );
        }
    );


    // =========================================================
    // VALIDATION
    // =========================================================

    function isValidEmail(
        email
    ) {

        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            .test(email);
    }


    function validateForm() {

        clearFieldErrors();


        const email =
            emailInput.value.trim();


        const password =
            passwordInput.value;


        let valid = true;


        if (!email) {

            setFieldError(
                emailInput,
                emailError,
                "Email address is required."
            );

            valid = false;

        } else if (
            !isValidEmail(email)
        ) {

            setFieldError(
                emailInput,
                emailError,
                "Enter a valid email address."
            );

            valid = false;
        }


        if (!password) {

            setFieldError(
                passwordInput,
                passwordError,
                "Password is required."
            );

            valid = false;
        }


        return valid;
    }


    // =========================================================
    // LOGIN
    // =========================================================

    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            clearAlerts();


            if (
                !validateForm()
            ) {

                return;
            }


            const email =
                emailInput.value.trim();


            const password =
                passwordInput.value;


            setLoading(true);


            try {

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
                                    email,
                                    password
                                })
                        }
                    );


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
                        "Invalid email or password."
                    );
                }


                if (
                    !data.access_token
                ) {

                    throw new Error(
                        "Login succeeded but no access token was returned."
                    );
                }


                /*
                 * Remember me controls where the JWT lives.
                 *
                 * Checked:
                 *     localStorage
                 *
                 * Unchecked:
                 *     sessionStorage
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

                    sessionStorage.removeItem(
                        ACCESS_TOKEN_KEY
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

                    localStorage.removeItem(
                        ACCESS_TOKEN_KEY
                    );

                    localStorage.removeItem(
                        REMEMBER_ME_KEY
                    );
                }


                showSuccess(
                    "Signed in successfully. Redirecting..."
                );


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

                setLoading(false);
            }
        }
    );


    // =========================================================
    // LIVE FIELD CLEANUP
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
     * There is currently no forgot-password backend endpoint
     * in the implemented API.
     *
     * Keep the UI honest instead of pretending this works.
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
    // INITIAL STATE
    // =========================================================

    clearAlerts();

    clearFieldErrors();

    emailInput.focus();

})();
