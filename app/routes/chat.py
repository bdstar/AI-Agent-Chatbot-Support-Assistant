import json
from uuid import uuid4, UUID as PyUUID
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, ChatHistoryItem, SessionItem, Reference
from app.database import get_db_cursor
from app.services.agent import process_query
from app.utils.helpers import safe_json_loads

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI agent and get a response.
    Creates or continues a chat session.
    """
    session_id = request.session_id or str(uuid4())

    # Convert to a proper uuid.UUID so psycopg2 can bind it to a
    # PostgreSQL UUID column without a type-cast error.
    try:
        session_uuid = PyUUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Load chat history for this session (for context)
    chat_history = []
    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT user_message, ai_response
                FROM chat_history
                WHERE session_id = %s
                ORDER BY created_at ASC
                LIMIT 20
                """,
                (session_uuid,),
            )
            rows = cur.fetchall()
            for row in rows:
                chat_history.append({"role": "user", "content": row[0]})
                chat_history.append({"role": "ai", "content": row[1]})
    except Exception as e:
        print(f"[WARN] Error loading chat history: {e}")

    # Process query through the LangGraph agent
    try:
        result = process_query(user_message, chat_history)
    except Exception as e:
        print(f"[ERROR] Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

    ai_response = result["response"]
    references = result.get("references", [])

    # Store in database
    try:
        refs_json = json.dumps([r if isinstance(r, dict) else r.dict() for r in references])
        with get_db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_history (session_id, user_message, ai_response, references_data)
                VALUES (%s, %s, %s, %s)
                """,
                (session_uuid, user_message, ai_response, refs_json),
            )
    except Exception as e:
        print(f"[ERROR] Error saving chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save chat history: {str(e)}")

    return ChatResponse(
        session_id=session_id,
        response=ai_response,
        references=[
            Reference(
                source=ref.get("source", "Unknown"),
                content=ref.get("content", ""),
                page=ref.get("page"),
            )
            for ref in references
        ],
    )


@router.get("/sessions", response_model=list[SessionItem])
async def list_sessions():
    """List all chat sessions, ordered by most recent."""
    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    session_id,
                    MIN(user_message) AS first_message,
                    COUNT(*) AS message_count,
                    MIN(created_at) AS created_at
                FROM chat_history
                GROUP BY session_id
                ORDER BY MAX(created_at) DESC
                """
            )
            rows = cur.fetchall()
            return [
                SessionItem(
                    session_id=str(row[0]),
                    first_message=row[1][:100] if row[1] else "New Chat",
                    message_count=row[2],
                    created_at=row[3],
                )
                for row in rows
            ]
    except Exception as e:
        print(f"[ERROR] Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/search")
async def search_sessions(q: str = ""):
    """Search across all chat sessions for matching messages."""
    if not q.strip():
        return []

    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    session_id,
                    user_message,
                    created_at
                FROM chat_history
                WHERE user_message ILIKE %s OR ai_response ILIKE %s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (f"%{q}%", f"%{q}%"),
            )
            rows = cur.fetchall()
            return [
                {
                    "session_id": str(row[0]),
                    "message_preview": row[1][:100],
                    "created_at": row[2].isoformat(),
                }
                for row in rows
            ]
    except Exception as e:
        print(f"[ERROR] Error searching sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=list[ChatHistoryItem])
async def get_session_history(session_id: str):
    """Get the full chat history for a specific session."""
    try:
        session_uuid = PyUUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT id, session_id, user_message, ai_response, references_data, created_at
                FROM chat_history
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_uuid,),
            )
            rows = cur.fetchall()

            if not rows:
                return []

            return [
                ChatHistoryItem(
                    id=row[0],
                    session_id=str(row[1]),
                    user_message=row[2],
                    ai_response=row[3],
                    references=[
                        Reference(**ref)
                        for ref in safe_json_loads(row[4] or "[]")
                    ],
                    created_at=row[5],
                )
                for row in rows
            ]
    except Exception as e:
        print(f"[ERROR] Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete an entire chat session."""
    try:
        session_uuid = PyUUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    try:
        with get_db_cursor() as cur:
            cur.execute(
                "DELETE FROM chat_history WHERE session_id = %s",
                (session_uuid,),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Session not found.")
        return {"detail": "Session deleted successfully.", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
