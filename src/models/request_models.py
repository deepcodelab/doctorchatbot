from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    # history: list
    session_id: Optional[str] = Field(None, description="The unique session ID to maintain history. Leave empty for a new session.")