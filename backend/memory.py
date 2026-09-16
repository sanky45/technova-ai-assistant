import json
import time

from redis_client import redis_client


# ==================================================
# CONFIGURATION
# ==================================================

CONVERSATION_PREFIX = "conversation:"
USER_CONVERSATIONS_PREFIX = "user:conversations:"

MAX_MESSAGES = 10

MEMORY_EXPIRATION_SECONDS = 60 * 60 * 24


# ==================================================
# BUILD REDIS KEYS
# ==================================================

def _get_conversation_key(
    user_id,
    session_id
):
    """
    Create the Redis key for a
    specific user's conversation.
    """

    return (
        f"{CONVERSATION_PREFIX}"
        f"{user_id}:"
        f"{session_id}"
    )


def _get_user_conversations_key(
    user_id
):
    """
    Create the Redis key that stores
    all conversation session IDs
    belonging to a user.
    """

    return (
        f"{USER_CONVERSATIONS_PREFIX}"
        f"{user_id}"
    )


# ==================================================
# GET CONVERSATION
# ==================================================

def get_conversation(
    user_id,
    session_id
):
    """
    Retrieve conversation history
    for a specific authenticated user
    and session.
    """

    key = _get_conversation_key(
        user_id,
        session_id
    )

    data = redis_client.get(key)

    if not data:
        return []

    return json.loads(data)


# ==================================================
# SAVE MESSAGE
# ==================================================

def save_message(
    user_id,
    session_id,
    role,
    content
):
    """
    Save one message to a
    user-specific conversation.

    Also registers/updates the conversation
    in the user's conversation index.
    """

    conversation = get_conversation(
        user_id,
        session_id
    )

    conversation.append({

        "role": role,

        "content": content

    })

    # ----------------------------------------------
    # Keep only the most recent messages
    # ----------------------------------------------

    conversation = conversation[
        -MAX_MESSAGES:
    ]

    # ----------------------------------------------
    # Save conversation
    # ----------------------------------------------

    conversation_key = _get_conversation_key(
        user_id,
        session_id
    )

    redis_client.set(
        conversation_key,
        json.dumps(conversation),
        ex=MEMORY_EXPIRATION_SECONDS
    )

    # ----------------------------------------------
    # Register conversation for the user
    # ----------------------------------------------

    conversations_key = _get_user_conversations_key(
        user_id
    )

    redis_client.zadd(
        conversations_key,
        {
            session_id: time.time()
        }
    )


# ==================================================
# LIST CONVERSATIONS
# ==================================================

def list_conversations(
    user_id
):
    """
    Return all conversations belonging
    to the authenticated user.

    Conversations are returned with the
    most recently updated conversation first.
    """

    conversations_key = _get_user_conversations_key(
        user_id
    )

    session_ids = redis_client.zrevrange(
        conversations_key,
        0,
        -1
    )

    conversations = []

    for session_id in session_ids:

        # Redis may return bytes depending
        # on Redis client configuration.
        if isinstance(session_id, bytes):
            session_id = session_id.decode("utf-8")

        conversation = get_conversation(
            user_id,
            session_id
        )

        # ------------------------------------------
        # Conversation expired from Redis
        # ------------------------------------------

        if not conversation:

            redis_client.zrem(
                conversations_key,
                session_id
            )

            continue

        # ------------------------------------------
        # Find first user question
        # ------------------------------------------

        title = "New conversation"

        for message in conversation:

            if message.get("role") == "user":

                content = message.get(
                    "content",
                    ""
                ).strip()

                if content:

                    title = content

                    # Keep sidebar title short
                    if len(title) > 60:
                        title = (
                            title[:60]
                            + "..."
                        )

                    break

        conversations.append({

            "session_id": session_id,

            "title": title,

            "message_count": len(
                conversation
            )

        })

    return conversations


# ==================================================
# CLEAR CONVERSATION
# ==================================================

def clear_conversation(
    user_id,
    session_id
):
    """
    Delete a specific user's
    conversation history and remove
    it from the user's conversation index.
    """

    conversation_key = _get_conversation_key(
        user_id,
        session_id
    )

    conversations_key = _get_user_conversations_key(
        user_id
    )

    # Delete actual conversation
    redis_client.delete(
        conversation_key
    )

    # Remove conversation from user's list
    redis_client.zrem(
        conversations_key,
        session_id
    )