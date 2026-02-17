import asyncpg
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from amaima.backend.app.billing import get_pool

logger = logging.getLogger(__name__)


async def create_conversation(
    api_key_id: str,
    title: str,
    operation_type: str,
    model: str,
    org_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new conversation thread.

    Args:
        api_key_id: The API key ID associated with the conversation
        title: The title of the conversation
        operation_type: Type of operation (e.g., 'query', 'analysis')
        model: The model used for the conversation
        org_id: Optional organization ID

    Returns:
        Dictionary containing conversation details

    Raises:
        Exception: If database operation fails
    """
    try:
        pool = await get_pool()
        conversation_id = secrets.token_hex(8)
        now = datetime.utcnow()

        await pool.execute(
            """INSERT INTO conversations 
               (id, api_key_id, org_id, title, model, operation_type, message_count, total_tokens, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            conversation_id,
            api_key_id,
            org_id,
            title,
            model,
            operation_type,
            0,  # message_count
            0,  # total_tokens
            now,
            now,
        )

        logger.info(
            f"Created conversation {conversation_id}"
        )

        return {
            "id": conversation_id,
            "api_key_id": api_key_id,
            "org_id": org_id,
            "title": title,
            "model": model,
            "operation_type": operation_type,
            "message_count": 0,
            "total_tokens": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise


async def list_conversations(
    api_key_id: str, limit: int = 20, offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List conversations for an API key with pagination.

    Args:
        api_key_id: The API key ID to filter conversations
        limit: Number of conversations to return (default: 20)
        offset: Number of conversations to skip (default: 0)

    Returns:
        List of conversation dictionaries

    Raises:
        Exception: If database operation fails
    """
    try:
        pool = await get_pool()

        rows = await pool.fetch(
            """SELECT id, api_key_id, org_id, title, model, operation_type, message_count, total_tokens, created_at, updated_at
               FROM conversations
               WHERE api_key_id = $1
               ORDER BY updated_at DESC
               LIMIT $2 OFFSET $3""",
            api_key_id,
            limit,
            offset,
        )

        conversations = [
            {
                "id": r["id"],
                "api_key_id": r["api_key_id"],
                "org_id": r["org_id"],
                "title": r["title"],
                "model": r["model"],
                "operation_type": r["operation_type"],
                "message_count": r["message_count"],
                "total_tokens": r["total_tokens"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ]

        logger.info("Listed %d conversations", len(conversations))

        return conversations

    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise


async def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a conversation with all its messages.

    Args:
        conversation_id: The ID of the conversation to retrieve

    Returns:
        Dictionary containing conversation and its messages, or None if not found

    Raises:
        Exception: If database operation fails
    """
    try:
        pool = await get_pool()

        # Get conversation
        conv_row = await pool.fetchrow(
            """SELECT id, api_key_id, org_id, title, model, operation_type, message_count, total_tokens, created_at, updated_at
               FROM conversations
               WHERE id = $1""",
            conversation_id,
        )

        if not conv_row:
            logger.warning(f"Conversation {conversation_id} not found")
            return None

        # Get messages
        message_rows = await pool.fetch(
            """SELECT id, conversation_id, role, content, model, tokens_used, latency_ms, attachments, metadata, created_at
               FROM messages
               WHERE conversation_id = $1
               ORDER BY created_at ASC""",
            conversation_id,
        )

        messages = [
            {
                "id": m["id"],
                "conversation_id": m["conversation_id"],
                "role": m["role"],
                "content": m["content"],
                "model": m["model"],
                "tokens_used": m["tokens_used"],
                "latency_ms": m["latency_ms"],
                "attachments": m["attachments"],
                "metadata": m["metadata"],
                "created_at": m["created_at"].isoformat() if m["created_at"] else None,
            }
            for m in message_rows
        ]

        conversation = {
            "id": conv_row["id"],
            "api_key_id": conv_row["api_key_id"],
            "org_id": conv_row["org_id"],
            "title": conv_row["title"],
            "model": conv_row["model"],
            "operation_type": conv_row["operation_type"],
            "message_count": conv_row["message_count"],
            "total_tokens": conv_row["total_tokens"],
            "created_at": conv_row["created_at"].isoformat()
            if conv_row["created_at"]
            else None,
            "updated_at": conv_row["updated_at"].isoformat()
            if conv_row["updated_at"]
            else None,
            "messages": messages,
        }

        logger.info(f"Retrieved conversation {conversation_id} with {len(messages)} messages")

        return conversation

    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise


async def add_message(
    conversation_id: str,
    role: str,
    content: str,
    model: str,
    tokens_used: int = 0,
    latency_ms: int = 0,
    attachments: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Add a message to a conversation and update conversation metadata.

    Args:
        conversation_id: The ID of the conversation
        role: The role of the message sender (e.g., 'user', 'assistant')
        content: The message content
        model: The model used to generate the message
        tokens_used: Number of tokens used (default: 0)
        latency_ms: Latency in milliseconds (default: 0)
        attachments: Optional JSON attachments data
        metadata: Optional JSON metadata

    Returns:
        Dictionary containing the created message

    Raises:
        Exception: If database operation fails
    """
    try:
        pool = await get_pool()
        message_id = secrets.token_hex(8)
        now = datetime.utcnow()

        # Insert message
        await pool.execute(
            """INSERT INTO messages
               (id, conversation_id, role, content, model, tokens_used, latency_ms, attachments, metadata, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            message_id,
            conversation_id,
            role,
            content,
            model,
            tokens_used,
            latency_ms,
            attachments,
            metadata,
            now,
        )

        # Update conversation metadata
        await pool.execute(
            """UPDATE conversations
               SET message_count = message_count + 1,
                   total_tokens = total_tokens + $1,
                   updated_at = $2
               WHERE id = $3""",
            tokens_used,
            now,
            conversation_id,
        )

        logger.info(
            f"Added message {message_id} to conversation {conversation_id} ({tokens_used} tokens)"
        )

        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "model": model,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "attachments": attachments,
            "metadata": metadata,
            "created_at": now.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error adding message to conversation: {str(e)}")
        raise


async def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation and all its associated messages.

    Args:
        conversation_id: The ID of the conversation to delete

    Returns:
        True if deletion was successful

    Raises:
        Exception: If database operation fails
    """
    try:
        pool = await get_pool()

        # Delete messages first (cascade)
        await pool.execute(
            "DELETE FROM messages WHERE conversation_id = $1", conversation_id
        )

        # Delete conversation
        result = await pool.execute(
            "DELETE FROM conversations WHERE id = $1", conversation_id
        )

        logger.info(f"Deleted conversation {conversation_id}")

        return True

    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise


async def search_conversations(api_key_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Search conversations by title or message content.

    Args:
        api_key_id: The API key ID to filter conversations
        query: Search query string

    Returns:
        List of matching conversation dictionaries

    Raises:
        Exception: If database operation fails
    """
    try:
        pool = await get_pool()

        # Search in conversation titles and message content
        rows = await pool.fetch(
            """SELECT DISTINCT c.id, c.api_key_id, c.org_id, c.title, c.model, c.operation_type, 
                       c.message_count, c.total_tokens, c.created_at, c.updated_at
               FROM conversations c
               LEFT JOIN messages m ON c.id = m.conversation_id
               WHERE c.api_key_id = $1
               AND (c.title ILIKE $2 OR m.content ILIKE $2)
               ORDER BY c.updated_at DESC""",
            api_key_id,
            f"%{query}%",
        )

        conversations = [
            {
                "id": r["id"],
                "api_key_id": r["api_key_id"],
                "org_id": r["org_id"],
                "title": r["title"],
                "model": r["model"],
                "operation_type": r["operation_type"],
                "message_count": r["message_count"],
                "total_tokens": r["total_tokens"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ]

        logger.info(
            "Found %d conversations matching search query", len(conversations)
        )

        return conversations

    except Exception as e:
        logger.error(f"Error searching conversations: {str(e)}")
        raise
