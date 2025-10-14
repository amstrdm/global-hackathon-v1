import asyncio
import json
import os
from typing import Dict, Set

import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import WebSocket
from utils.logging_config import get_logger

logger = get_logger("routes.websockets.redis_manager")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)


# Establish a connection to the Redis server
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

if not REDIS_HOST:
    logger.error("REDIS_HOST environment variable missing")
    raise


if not REDIS_PORT:
    logger.error("REDIS_PORT environment variable missing")
    raise

redis_client = None


async def get_redis_client():
    """
    Returns the existing Redis client instance or creates a new one.
    """
    global redis_client
    if redis_client is None:
        try:
            # Use from_url for easier configuration
            redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0"
            redis_client = redis.from_url(redis_url, decode_responses=True)
            await redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.error(f"Could not connect to Redis: {e}")
            redis_client = None  # Ensure client is None on failure
    return redis_client


class RedisConnectionManager:
    def __init__(self):
        # This dictionary stores connections LOCAL to this server process
        self.local_connections: Dict[str, Set[WebSocket]] = {}
        # This tracks the background listening tasks for each room
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}

    async def _get_room_channel_name(self, room_phrase: str) -> str:
        return f"room:{room_phrase}"

    async def _get_room_occupancy_key(self, room_phrase: str) -> str:
        return f"room_occupancy:{room_phrase}"

    async def connect(
        self, websocket: WebSocket, room_phrase: str, user_id: str
    ) -> bool:
        """Adds a connection and subscribes to the room's Redis channel."""
        occupancy_key = await self._get_room_occupancy_key(room_phrase)

        # Use Redis to get an accurate count across all servers/processes
        current_occupancy = await redis_client.scard(occupancy_key)
        if current_occupancy >= 2:
            return False

        # Add user to the distributed set for occupancy tracking
        await redis_client.sadd(occupancy_key, user_id)

        # Add the connection to the LOCAL dictionary for this process
        if room_phrase not in self.local_connections:
            self.local_connections[room_phrase] = set()
        self.local_connections[room_phrase].add(websocket)

        # Start a background task to listen for messages from Redis
        channel = await self._get_room_channel_name(room_phrase)
        pubsub_task = asyncio.create_task(self._pubsub_reader(channel, room_phrase))
        self.pubsub_tasks[room_phrase] = pubsub_task

        return True

    async def disconnect(self, websocket: WebSocket, room_phrase: str, user_id: str):
        """Removes a connection and cleans up Redis state."""
        # Remove from local connections
        if room_phrase in self.local_connections:
            self.local_connections[room_phrase].discard(websocket)
            # If this was the last local connection, stop the listener task
            if not self.local_connections[room_phrase]:
                self.local_connections.pop(room_phrase)
                task = self.pubsub_tasks.pop(room_phrase, None)
                if task:
                    task.cancel()

        # Remove user from the distributed occupancy set
        occupancy_key = await self._get_room_occupancy_key(room_phrase)
        await redis_client.srem(occupancy_key, user_id)

    async def broadcast_to_room(self, room_phrase: str, message: dict):
        """Publishes a message to the room's Redis channel."""
        channel = await self._get_room_channel_name(room_phrase)
        await redis_client.publish(channel, json.dumps(message))

    async def _pubsub_reader(self, channel: str, room_phrase: str):
        """The background task that listens to Redis and forwards messages."""
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(channel)
            while True:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message:
                        data = json.loads(message["data"])
                        connections = self.local_connections.get(room_phrase, set())
                        for connection in connections:
                            try:
                                await connection.send_json(data)
                            except RuntimeError:
                                print(
                                    f"Failed to send to a websocket in room {room_phrase}; it may be closed."
                                )
                                # The main websocket_endpoint's finally block is responsible for cleanup.
                                # We just continue to the next connection.
                                pass

                except asyncio.CancelledError:
                    # Task was cancelled, exit the loop
                    break
                except Exception as e:
                    print(f"Error in pubsub reader for room {room_phrase}: {e}")
                    # In production, you might want more robust error handling
                    break
