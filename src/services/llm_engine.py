import json
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from google.genai import types
from google.genai.types import Content, Part, GenerateContentResponse
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment variable for security
# API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
# if not API_KEY:
#     raise ValueError("GOOGLE_GENAI_API_KEY environment variable not set")

try:
    client = genai.Client(api_key="AIzaSyDKIPOC2GvUsyMir6hbJhapfWsrdyQWGUE")
except Exception as e:
    logger.error(f"Failed to initialize Genai client: {e}")
    raise

# FIX: Added SESSION_STORE definition at the top level
SESSION_STORE: Dict[str, List[Content]] = {} 

# Define function declarations using the proper format
search_doctors_func = types.FunctionDeclaration(
    name="search_doctors",
    description="Search doctors based on it's specilization and optional city",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symptom": types.Schema(type=types.Type.STRING, description="The medical symptom mentioned by the user."),
            "city": types.Schema(type=types.Type.STRING, description="The city or location, if provided by the user."),
        },
        required=["symptom"],
    ),
)

check_slots_func = types.FunctionDeclaration(
    name="check_available_slots",
    description="Get availability slots for a doctor using their unique ID",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "doctor_id": types.Schema(type=types.Type.INTEGER, description="The unique ID of the doctor."),
        },
        required=["doctor_id"],
    ),
)

# Create Tool object with function declarations
TOOLS = [types.Tool(function_declarations=[search_doctors_func, check_slots_func])]

SYSTEM_PROMPT = """
You are a concise, helpful medical AI assistant. Your primary function is to recommend doctors and check their availability using the provided tools.

RULES:
1. If the user mentions any medical symptom (fever, cough, pain, headache, vomiting, etc.):
      When the user mentions any medical symptom, DO NOT suggest a doctor directly.
        First ask the user: “Would you like me to suggest a doctor?”
        If the user gives consent, you may then call the search_doctors tool.
        You must decide the correct doctor specialization based on the user’s symptoms.
        Do not use any fixed mapping. Let the model infer the best specialization.
2. If the user mentions a specific doctor ID or asks about booking/slots → ALWAYS call `check_available_slots`.
3. Do not reply with normal text if a tool should be called.
4. When reporting tool results, summarize the information clearly and politely.
5. If no doctors are found, politely inform the user.
"""


# =======================================================================
# MOCK ASYNCHRONOUS BACKEND FUNCTIONS
# =======================================================================

async def search_doctors(symptom: str, city: str = None) -> str:
    """Simulates searching a doctor database."""
    symptom_lower = symptom.lower()
    doctors = []
    print(symptom_lower,"-----")

    # Mock symptom to specialty mapping
    if "fever" in symptom_lower or "cough" in symptom_lower or "cold" in symptom_lower:
        doctors = [
            {"id": 101, "name": "Dr. Alex Johnson", "specialty": "Internal Medicine"},
            {"id": 102, "name": "Dr. Sarah Lee", "specialty": "Family Practice"}
        ]
    elif "headache" in symptom_lower or "migraine" in symptom_lower:
        doctors = [
            {"id": 103, "name": "Dr. Robert Chen", "specialty": "Neurology"},
            {"id": 104, "name": "Dr. Emily Davis", "specialty": "Internal Medicine"}
        ]
    elif "chest pain" in symptom_lower or "heart" in symptom_lower:
        doctors = [
            {"id": 105, "name": "Dr. Michael Brown", "specialty": "Cardiology"},
            {"id": 106, "name": "Dr. Lisa Anderson", "specialty": "Emergency Medicine"}
        ]
    elif "stomach" in symptom_lower or "nausea" in symptom_lower or "vomiting" in symptom_lower:
        doctors = [
            {"id": 107, "name": "Dr. James Wilson", "specialty": "Gastroenterology"},
            {"id": 108, "name": "Dr. Patricia Moore", "specialty": "Internal Medicine"}
        ]
    else:
        return json.dumps({"doctors": [], "message": f"No doctors found for symptom: {symptom}"})

    return json.dumps({"doctors": doctors, "city": city if city else "Anywhere"})

async def check_available_slots(doctor_id: int) -> str:
    """Simulates checking appointment slots."""
    # Mock doctor availability
    doctor_slots = {
        101: {"slots": ["10:00 AM", "2:00 PM"], "date": "Thursday, Nov 21"},
        102: {"slots": ["9:00 AM", "11:30 AM", "3:00 PM"], "date": "Friday, Nov 22"},
        103: {"slots": ["1:00 PM", "4:30 PM"], "date": "Monday, Nov 25"},
        104: {"slots": ["10:30 AM"], "date": "Wednesday, Nov 27"},
        105: {"slots": ["2:00 PM"], "date": "Tuesday, Nov 26"},
        106: {"slots": ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"], "date": "Thursday, Nov 21"},
        107: {"slots": ["10:00 AM", "3:30 PM"], "date": "Monday, Nov 25"},
        108: {"slots": ["11:00 AM", "1:30 PM"], "date": "Friday, Nov 22"},
    }

    if doctor_id in doctor_slots:
        return json.dumps({"doctor_id": doctor_id, **doctor_slots[doctor_id]})
    else:
        return json.dumps({"doctor_id": doctor_id, "slots": [], "message": "Doctor not found or no available slots."})


# IMPORTANT: Define FUNCTION_MAP after the async functions are defined
FUNCTION_MAP = {
    "search_doctors": search_doctors,
    "check_available_slots": check_available_slots,
}

# =======================================================================
# ASYNCHRONOUS ENGINE LOGIC (StatelessChatbot)
# =======================================================================

class StatelessChatbot:

    def __init__(self, history: List[Content]):
        self.history = history

    async def run_conversation_turn(self, prompt: str) -> Dict[str, Any]:
        """
        Execute a single conversation turn with the LLM.
        Handles function calling for tool invocations.
        """
        try:
            # 1. Prepare contents: Add the new user prompt to the history list
            new_user_content = Content(role="user", parts=[Part(text=prompt)])
            contents_to_send = self.history + [new_user_content]

            # 2. First API Call
            try:
                response: GenerateContentResponse = await asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=contents_to_send,
                    config=genai.types.GenerateContentConfig(
                        tools=TOOLS,
                        system_instruction=SYSTEM_PROMPT
                    )
                )
            except Exception as e:
                logger.error(f"First API call failed: {e}")
                return {
                    "response_text": f"Error communicating with AI service: {str(e)}",
                    "updated_history": self.history,
                    "error": True
                }

            # Validate response has candidates
            if not response.candidates or len(response.candidates) == 0:
                logger.warning("Response has no candidates")
                return {
                    "response_text": "Error: No response from AI service",
                    "updated_history": self.history,
                    "error": True
                }

            # Update history with the user content and the model's first response
            self.history.append(new_user_content)
            self.history.append(response.candidates[0].content)

            final_response_text = response.text if response.text else ""

            # 3. Check for Function Call and Execute
            if response.function_calls:
                try:
                    call = response.function_calls[0]
                    function_name = call.name
                    function_args = dict(call.args)
                    print(function_args,"function_args")

                    logger.info(f"Executing function: {function_name} with args: {function_args}")

                    # Get function and validate it exists
                    function_to_call = FUNCTION_MAP.get(function_name)
                    if function_to_call is None:
                        error_msg = f"Function '{function_name}' not found in FUNCTION_MAP"
                        logger.error(error_msg)
                        return {
                            "response_text": error_msg,
                            "updated_history": self.history,
                            "error": True
                        }

                    # Execute function with error handling
                    try:
                        tool_output = await function_to_call(**function_args)
                    except Exception as e:
                        logger.error(f"Function execution failed: {e}")
                        tool_output = json.dumps({"error": f"Function execution failed: {str(e)}"})

                    # 4. Send the function result back to the model
                    tool_response_part = Part.from_function_response(
                        name=function_name,
                        response={"result": tool_output}
                    )

                    function_content = Content(role="function", parts=[tool_response_part])
                    self.history.append(function_content)

                    # 5. Second API Call: Get final answer
                    try:
                        final_response: GenerateContentResponse = await asyncio.to_thread(
                            client.models.generate_content,
                            model="gemini-2.5-flash",
                            contents=self.history,
                            config=genai.types.GenerateContentConfig(
                                tools=TOOLS,
                                system_instruction=SYSTEM_PROMPT
                            )
                        )
                    except Exception as e:
                        logger.error(f"Second API call failed: {e}")
                        return {
                            "response_text": f"Error getting final response: {str(e)}",
                            "updated_history": self.history,
                            "error": True
                        }

                    # Validate second response
                    if final_response.candidates and len(final_response.candidates) > 0:
                        final_response_text = final_response.text if final_response.text else ""
                        self.history.append(final_response.candidates[0].content)
                    else:
                        logger.warning("Final response has no candidates")

                except Exception as e:
                    logger.error(f"Error during function call handling: {e}")
                    return {
                        "response_text": f"Error during function handling: {str(e)}",
                        "updated_history": self.history,
                        "error": True
                    }

            return {
                "response_text": final_response_text,
                "updated_history": self.history,
                "error": False
            }

        except Exception as e:
            logger.error(f"Unexpected error in run_conversation_turn: {e}")
            return {
                "response_text": f"Unexpected error: {str(e)}",
                "updated_history": self.history,
                "error": True
            }