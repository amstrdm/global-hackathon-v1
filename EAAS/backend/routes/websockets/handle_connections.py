import asyncio
from typing import Dict, Set

from fastapi import WebSocket, status

room_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages websocket connections"""

    @staticmethod
    async def connect(websocket: WebSocket, room_phrase: str) -> bool:
        """Add connection to room"""
        current_connections = room_connections.get(room_phrase, set())
        if len(current_connections) >= 2:
            await websocket.accept()
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Room is full"
            )
            return False

        await websocket.accept()
        if room_phrase not in room_connections:
            room_connections[room_phrase] = set()
        room_connections[room_phrase].add(websocket)
        return True

    @staticmethod
    def disconnect(websocket: WebSocket, room_phrase: str):
        """Remove connections from room"""
        if room_phrase in room_connections:
            room_connections[room_phrase].discard(websocket)

    @staticmethod
    async def broadcast_to_room(room_phrase: str, message: dict):
        """Send message to all connections in a room"""
        if room_phrase not in room_connections:
            return

        disconnected = set()
        for connection in room_connections[room_phrase]:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            room_connections[room_phrase].discard(connection)
