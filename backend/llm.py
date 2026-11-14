
import requests

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_LLM_MODEL
)


# ==================================================
# OPENROUTER CONFIGURATION
# ==================================================

DEFAULT_MAX_OUTPUT_TOKENS = 500
DEFAULT_TEMPERATURE = 0.2

CHAT_COMPLETIONS_URL = (
    f"{OPENROUTER_BASE_URL}/chat/completions"
)


# ==================================================
# VALIDATE API KEY
# ==================================================

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not configured. "
        "Add it to your .env file."
    )


# ==================================================
# GENERATE ANSWER
# ==================================================

def generate_answer(
    prompt,
    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
):
    """
    Generate an answer using OpenRouter.

    Parameters
    ----------
    prompt : str
        Complete RAG prompt.

    max_output_tokens : int
        Maximum number of tokens generated.

    Returns
    -------
    str
        Generated answer.
    """

    # Validate prompt
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    # Validate token limit
    if max_output_tokens <= 0:
        raise ValueError(
            "max_output_tokens must be greater than zero."
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_LLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt.strip()
            }
        ],
        "max_tokens": max_output_tokens,
        "temperature": DEFAULT_TEMPERATURE
    }

    # Generate response
    try:
        response = requests.post(
            CHAT_COMPLETIONS_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

    except requests.exceptions.RequestException as error:
        print(f"OpenRouter generation failed: {error}")

        raise RuntimeError(
            "Unable to generate an answer using OpenRouter."
        ) from error

    except ValueError as error:
        raise RuntimeError(
            "OpenRouter returned an invalid JSON response."
        ) from error

    # Extract generated text
    try:
        generated_text = result["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError):
        raise RuntimeError(
            "OpenRouter returned an unexpected response format."
        )

    # Validate generated text
    if isinstance(generated_text, str) and generated_text.strip():
        return generated_text.strip()

    raise RuntimeError(
        "OpenRouter returned an empty response."
    )
