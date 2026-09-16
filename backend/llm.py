from google import genai

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_NAME
)


# ==================================================
# GEMINI CONFIGURATION
# ==================================================

DEFAULT_MAX_OUTPUT_TOKENS = 500
DEFAULT_TEMPERATURE = 0.2


# ==================================================
# VALIDATE API KEY
# ==================================================

if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY is not configured. "
        "Add it to your .env file."
    )


# ==================================================
# GEMINI CLIENT
# ==================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==================================================
# GENERATE ANSWER
# ==================================================

def generate_answer(
    prompt,
    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
):
    """
    Generate an answer using Gemini.

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

    # --------------------------------------------------
    # Validate prompt
    # --------------------------------------------------

    if not prompt or not prompt.strip():

        raise ValueError(
            "Prompt cannot be empty."
        )

    # --------------------------------------------------
    # Validate output token limit
    # --------------------------------------------------

    if max_output_tokens <= 0:

        raise ValueError(
            "max_output_tokens must be "
            "greater than zero."
        )

    # --------------------------------------------------
    # Generate response
    # --------------------------------------------------

    try:

        response = client.models.generate_content(

            model=GEMINI_MODEL_NAME,

            contents=prompt,

            config={
                "max_output_tokens":
                    max_output_tokens,

                "temperature":
                    DEFAULT_TEMPERATURE
            }
        )

    except Exception as error:

        print(
            "Gemini generation failed:"
        )

        print(
            f"  → Error: {error}"
        )

        raise RuntimeError(
            "Unable to generate an answer "
            "using the LLM."
        ) from error

    # --------------------------------------------------
    # Extract generated text
    # --------------------------------------------------

    if response is None:

        raise RuntimeError(
            "LLM returned an empty response."
        )

    generated_text = getattr(
        response,
        "text",
        None
    )

    # --------------------------------------------------
    # Validate generated text
    # --------------------------------------------------

    if generated_text:

        generated_text = (
            generated_text.strip()
        )

        if generated_text:

            return generated_text

    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------

    return (
        "I was unable to generate an answer."
    )