from pydantic import BaseModel

class ChatResponse(BaseModel):
    session_id: str
    reply: str # <-- Must be named 'reply' if the error says 'reply' is missing
    is_new_session: bool