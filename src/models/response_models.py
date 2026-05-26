from pydantic import BaseModel

class ChatResponse(BaseModel):
    reply: str # <-- Must be named 'reply' if the error says 'reply' is missing