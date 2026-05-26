from fastapi import APIRouter,HTTPException, Header
from models.request_models import ChatRequest
from models.response_models import ChatResponse
from services.symptom_detector import SymptomDetector
# from src.services.llm_engine import LLMEngine

router = APIRouter()

# main.py (or your routes file)

import uuid
from fastapi import APIRouter
from typing import Dict, List, Any

from agents.supervisor_agent import SupervisorAgent
from state.conversation_state import ConversationState

# Assuming these are defined and imported from your project structure
# from .pydantic_models import ChatRequest, ChatResponse
supervisor = SupervisorAgent()

state = ConversationState()


# Initialize the FastAPI router
router = APIRouter()

@router.post("/respond")

async def respond(data: dict, authorization: str = Header(None)):
    print("TOKEN:", authorization)
    state.authorization = authorization
    user_message = data["message"]

    response = await supervisor.run(
        user_message,
        state
    )

    return response
# async def respond(request: ChatRequest):
#     """
#     Handles a single turn of conversation, manages session history, 
#     and uses the async StatelessChatbot with Function Calling.
#     """

#     chatbot = StatelessChatbot(history=request.history)
#     print("jdjd", request.history)
#     result: Dict[str, Any] = await chatbot.run_conversation_turn(request.message)
#     return ChatResponse(
#             reply=result["response_text"],
#         )
    
    # # 1. Session Management (Get or Create)
    # is_new_session = request.session_id is None
    # session_id = request.session_id if request.session_id else str(uuid.uuid4())
    
    # # Retrieve history
    # history: List[Content] = SESSION_STORE.get(session_id, [])

    # try:
    #     # 2. Run the Asynchronous Chatbot Turn
    #     chatbot = StatelessChatbot(history=history)
    #     result: Dict[str, Any] = await chatbot.run_conversation_turn(request.message)

    #     # 3. Save Updated History
    #     SESSION_STORE[session_id] = result["updated_history"]

    #     # 4. Return the Structured Response
    #     return ChatResponse(
    #         session_id=session_id,
    #         # FIX: Mapping the 'response_text' key to the required 'reply' field.
    #         reply=result["response_text"], 
    #         is_new_session=is_new_session
    #     )

    # except Exception as e:
    #     # 500 error handler
    #     print(f"Chatbot Error in session {session_id}: {e}")
    #     # Use HTTPException for consistent FastAPI error responses
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Internal AI service error: {e}"
    #     )