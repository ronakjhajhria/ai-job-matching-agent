from typing import Literal

from pydantic import BaseModel, Field
from redis import Redis


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class RedisConversationStore:
    def __init__(
        self,
        client: Redis,
        ttl_seconds: int = 86400,
        max_messages: int = 30,
    ):
        self.client = client
        self.ttl_seconds = ttl_seconds
        self.max_messages = max_messages

    def append(self, session_id: str, message: ConversationMessage) -> list[ConversationMessage]:
        key = self._key(session_id)
        with self.client.pipeline(transaction=True) as pipeline:
            pipeline.rpush(key, message.model_dump_json())
            pipeline.ltrim(key, -self.max_messages, -1)
            pipeline.expire(key, self.ttl_seconds)
            pipeline.execute()
        return self.get_recent(session_id)

    def get_recent(self, session_id: str) -> list[ConversationMessage]:
        values = self.client.lrange(self._key(session_id), 0, -1)
        return [ConversationMessage.model_validate_json(value) for value in values]

    @staticmethod
    def _key(session_id: str) -> str:
        return f"jobmind:session:{session_id}:messages"