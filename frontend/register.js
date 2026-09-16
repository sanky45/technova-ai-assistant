(() => {

    "use strict";


    /* =================================================
       CONFIGURATION
    ================================================= */

    const REGISTER_ENDPOINT = "/register";

    const ACCESS_TOKEN_KEY =
        "kstore_ai_access_token";


    /* =================================================
       ELEMENTS
    ================================================= */

    const form =
        document.getElementById(
            "registerForm"
        );

    const usernameInput =
        document.getElementById(
            "username"
        );

    const emailInput =
        document.getElementById(
            "email"
        );

    const passwordInput =
        document.getElementById(
            "password"
        );

    const confirmPasswordInput =
        document.getElementById(
            "confirmPassword"
        );


    const registerBtn =
        document.getElementById(
            "registerBtn"
        );

    const registerBtnText =
        document.getElementById(
            "registerBtnText"
        );

    const registerSpinner =
        document.getElementById(
            "registerSpinner"
        );


    const registerError =
        document.getElementById(
            "registerError"
        );

    const registerSuccess =
        document.getElementById(
            "registerSuccess"
        );


    const usernameError =
        document.getElementById(
            "usernameError"
        );

    const emailError =
        document.getElementById(
            "emailError"
        );

    const passwordError =
        document.getElementById(
            "passwordError"
        );

    const confirmPasswordError =
        document.getElementById(
            "confirmPasswordError"
        );


    const togglePassword =
        document.getElementById(
            "togglePassword"
        );

    const toggleConfirmPassword =
        document.getElementById(
            "toggleConfirmPassword"
        );


    const passwordStrength =
        document.getElementById(
            "passwordStrength"
        );

    const strengthLabel =
        document.getElementById(
            "strengthLabel"
        );

    const strengthFill =
        document.getElementById(
            "strengthFill"
        );


    /* =================================================
       EXISTING LOGIN CHECK
    ================================================= */

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
     * there is no reason to show registration.
     */

    if (hasExistingToken()) {

        window.location.replace(
            "/chat.html"
        );

        return;
    }


    /* =================================================
       ALERTS
    ================================================= */

    function showError(message) {

        registerError.textContent =
            message;

        registerError.hidden =
            false;

        registerSuccess.hidden =
            true;

    }


    function showSuccess(message) {

        registerSuccess.textContent =
            message;

        registerSuccess.hidden =
            false;

        registerError.hidden =
            true;

    }


    function clearAlerts() {

        registerError.hidden =
            true;

        registerSuccess.hidden =
            true;

        registerError.textContent =
            "";

        registerSuccess.textContent =
            "";

    }


    /* =================================================
       FIELD ERRORS
    ================================================= */

    function clearFieldErrors() {

        usernameError.textContent =
            "";

        emailError.textContent =
            "";

        passwordError.textContent =
            "";

        confirmPasswordError.textContent =
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


    /* =================================================
       PASSWORD VISIBILITY
    ================================================= */

    function setupPasswordToggle(
        button,
        input
    ) {

        button.addEventListener(
            "click",
            () => {

                const isPassword =
                    input.type ===
                    "password";


                if (isPassword) {

                    input.type =
                        "text";

                    button.textContent =
                        "Hide";

                    button.setAttribute(
                        "aria-label",
                        "Hide password"
                    );

                    button.setAttribute(
                        "title",
                        "Hide password"
                    );

                } else {

                    input.type =
                        "password";

                    button.textContent =
                        "Show";

                    button.setAttribute(
                        "aria-label",
                        "Show password"
                    );

                    button.setAttribute(
                        "title",
                        "Show password"
                    );

                }

            }
        );

    }


    setupPasswordToggle(
        togglePassword,
        passwordInput
    );


    setupPasswordToggle(
        toggleConfirmPassword,
        confirmPasswordInput
    );


    /* =================================================
       EMAIL VALIDATION
    ================================================= */

    function isValidEmail(email) {

        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            .test(email);

    }


    /* =================================================
       PASSWORD STRENGTH
    ================================================= */

    function calculatePasswordStrength(
        password
    ) {

        let score = 0;


        if (!password) {

            return 0;

        }


        if (password.length >= 8) {

            score++;

        }


        if (password.length >= 12) {

            score++;

        }


        if (/[A-Z]/.test(password)) {

            score++;

        }


        if (/[a-z]/.test(password)) {

            score++;

        }


        if (/[0-9]/.test(password)) {

            score++;

        }


        if (/[^A-Za-z0-9]/.test(password)) {

            score++;

        }


        return score;

    }


    function updatePasswordStrength() {

        const password =
            passwordInput.value;


        if (!password) {

            passwordStrength.hidden =
                true;

            strengthFill.style.width =
                "0%";

            strengthLabel.textContent =
                "-";

            return;

        }


        passwordStrength.hidden =
            false;


        const score =
            calculatePasswordStrength(
                password
            );


        let percentage =
            0;

        let label =
            "";


        if (score <= 2) {

            percentage = 25;

            label = "Weak";

        } else if (score <= 4) {

            percentage = 60;

            label = "Good";

        } else {

            percentage = 100;

            label = "Strong";

        }


        strengthFill.style.width =
            `${percentage}%`;

        strengthLabel.textContent =
            label;

    }


    passwordInput.addEventListener(
        "input",
        updatePasswordStrength
    );


    /* =================================================
       VALIDATION
    ================================================= */

    function validateForm() {

        clearFieldErrors();


        const username =
            usernameInput.value.trim();

        const email =
            emailInput.value.trim();

        const password =
            passwordInput.value;

        const confirmPassword =
            confirmPasswordInput.value;


        let valid = true;


        /* Username */

        if (!username) {

            setFieldError(
                usernameInput,
                usernameError,
                "Username is required."
            );

            valid = false;

        } else if (
            username.length < 2
        ) {

            setFieldError(
                usernameInput,
                usernameError,
                "Username must contain at least 2 characters."
            );

            valid = false;

        }


        /* Email */

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


        /* Password */

        if (!password) {

            setFieldError(
                passwordInput,
                passwordError,
                "Password is required."
            );

            valid = false;

        } else if (
            password.length < 8
        ) {

            setFieldError(
                passwordInput,
                passwordError,
                "Password must contain at least 8 characters."
            );

            valid = false;

        }


        /* Confirm password */

        if (!confirmPassword) {

            setFieldError(
                confirmPasswordInput,
                confirmPasswordError,
                "Please confirm your password."
            );

            valid = false;

        } else if (
            password !==
            confirmPassword
        ) {

            setFieldError(
                confirmPasswordInput,
                confirmPasswordError,
                "Passwords do not match."
            );

            valid = false;

        }


        return valid;

    }


    /* =================================================
       LOADING STATE
    ================================================= */

    function setLoading(
        loading
    ) {

        registerBtn.disabled =
            loading;


        usernameInput.disabled =
            loading;

        emailInput.disabled =
            loading;

        passwordInput.disabled =
            loading;

        confirmPasswordInput.disabled =
            loading;


        registerBtnText.textContent =
            loading
                ? "Creating account..."
                : "Create account";


        registerSpinner.hidden =
            !loading;


        const arrow =
            registerBtn.querySelector(
                ".button-arrow"
            );


        if (arrow) {

            arrow.hidden =
                loading;

        }

    }


    /* =================================================
       REGISTER REQUEST
    ================================================= */

    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            clearAlerts();


            if (!validateForm()) {

                return;

            }


            const username =
                usernameInput.value.trim();

            const email =
                emailInput.value.trim();

            const password =
                passwordInput.value;


            setLoading(true);


            try {

                const response =
                    await fetch(
                        REGISTER_ENDPOINT,
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
                                    username:
                                        username,

                                    email:
                                        email,

                                    password:
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

                    let message =
                        "Unable to create your account.";


                    if (
                        typeof data.detail ===
                        "string"
                    ) {

                        message =
                            data.detail;

                    } else if (
                        Array.isArray(
                            data.detail
                        )
                    ) {

                        message =
                            data.detail
                                .map(
                                    error =>
                                        error.msg
                                )
                                .join(
                                    ", "
                                );

                    } else if (
                        data.error
                    ) {

                        message =
                            data.error;

                    }


                    throw new Error(
                        message
                    );

                }


                showSuccess(
                    data.message ||
                    "Account created successfully. Redirecting to sign in..."
                );


                /*
                 * Registration does not return a JWT.
                 * The user must authenticate through login.
                 */

                setTimeout(
                    () => {

                        window.location.replace(
                            "/login.html"
                        );

                    },
                    900
                );


            } catch (error) {

                console.error(
                    "KStore AI registration failed:",
                    error
                );


                showError(
                    error.message ||
                    "Unable to create your account. Please try again."
                );


            } finally {

                setLoading(false);

            }

        }
    );


    /* =================================================
       LIVE FIELD CLEANUP
    ================================================= */

    function clearInputError(
        input,
        errorElement
    ) {

        errorElement.textContent =
            "";


        const wrapper =
            input.closest(
                ".input-wrap"
            );


        if (wrapper) {

            wrapper.classList.remove(
                "invalid"
            );

        }


        clearAlerts();

    }


    usernameInput.addEventListener(
        "input",
        () => {

            clearInputError(
                usernameInput,
                usernameError
            );

        }
    );


    emailInput.addEventListener(
        "input",
        () => {

            clearInputError(
                emailInput,
                emailError
            );

        }
    );


    passwordInput.addEventListener(
        "input",
        () => {

            clearInputError(
                passwordInput,
                passwordError
            );

            clearAlerts();

        }
    );


    confirmPasswordInput.addEventListener(
        "input",
        () => {

            clearInputError(
                confirmPasswordInput,
                confirmPasswordError
            );

        }
    );


    /* =================================================
       INITIAL STATE
    ================================================= */

    clearAlerts();

    clearFieldErrors();

    usernameInput.focus();

})();