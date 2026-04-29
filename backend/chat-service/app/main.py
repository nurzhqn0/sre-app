from __future__ import annotations

from collections import defaultdict
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status

from shared.auth import decode_access_token, require_user_claims
from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response

settings = get_settings()
app = FastAPI(title="Chat Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms[room].append(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        room_connections = self.rooms.get(room, [])
        if websocket in room_connections:
            room_connections.remove(websocket)
        if not room_connections and room in self.rooms:
            del self.rooms[room]

    async def broadcast(self, room: str, payload: dict):
        disconnected: list[WebSocket] = []
        for connection in self.rooms.get(room, []):
            try:
                await connection.send_json(payload)
            except RuntimeError:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(room, connection)


manager = ConnectionManager()


def current_user(authorization: Annotated[str | None, Header()] = None):
    return require_user_claims(settings.jwt_secret_key, authorization)


def normalize_message(message: dict) -> dict:
    normalized = dict(message)
    created_at = normalized.get("created_at")
    if created_at is not None:
        normalized["created_at"] = created_at.isoformat()
    return normalized


def run_health_check():
    check_database(settings.database_url)


def store_message(room: str, user_id: str, username: str, content: str) -> dict:
    message_id = str(uuid4())
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages (id, room, user_id, username, content)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, room, user_id, username, content, created_at
                """,
                (message_id, room, user_id, username, content),
            )
            message = cursor.fetchone()
        connection.commit()
    return normalize_message(message)


@app.get("/health")
def health():
    run_health_check()
    return {"service": settings.service_name, "status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response(settings.service_name, run_health_check)


@app.get("/rooms/{room}/messages")
def get_room_messages(room: str, _: Annotated[dict, Depends(current_user)]):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, room, user_id, username, content, created_at
                FROM messages
                WHERE room = %s
                ORDER BY created_at ASC
                LIMIT 50
                """,
                (room,),
            )
            messages = [normalize_message(message) for message in cursor.fetchall()]
    return {"messages": messages}


@app.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    room = websocket.query_params.get("room") or settings.default_chat_room
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        claims = decode_access_token(token, settings.jwt_secret_key)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(room, websocket)
    try:
        while True:
            content = await websocket.receive_text()
            if not content.strip():
                continue
            message = store_message(room, claims["sub"], claims["username"], content.strip())
            await manager.broadcast(room, message)
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
