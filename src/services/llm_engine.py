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
    client = genai.Client(api_key="AIzaSyAw6JrwEAdz-VF7hiyBRDlruaZ_SQKOoLo")
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

# check_slots_func = types.FunctionDeclaration(
#     name="check_available_slots",
#     description="Get availability slots for a doctor using their unique ID",
#     parameters=types.Schema(
#         type=types.Type.OBJECT,
#         properties={
#             "doctor_id": types.Schema(type=types.Type.INTEGER, description="The unique ID of the doctor."),
#         },
#         required=["doctor_id"],
#     ),
# )

# Create Tool object with function declarations
# TOOLS = [types.Tool(function_declarations=[search_doctors, check_slots])]

# SYSTEM_PROMPT = """
# You are a concise, helpful medical AI assistant. Your primary function is to recommend doctors and check their availability using the provided tools.

# RULES:
# 1. If the user mentions any medical symptom (fever, cough, pain, headache, vomiting, etc.):
#       When the user mentions any medical symptom, DO NOT suggest a doctor directly.
#         First ask the user: “Would you like me to suggest a doctor?”
#         If the user gives consent, you may then call the search_doctors tool.
#         You must decide the correct doctor specialization based on the user’s symptoms.
#         Do not use any fixed mapping. Let the model infer the best specialization.
# 2. If the user mentions a specific doctor ID or asks about booking/slots → ALWAYS call `check_available_slots`.
# 3. Do not reply with normal text if a tool should be called.
# 4. When reporting tool results, summarize the information clearly and politely.
# 5. If no doctors are found, politely inform the user.
# """


SYSTEM_PROMPT = """
You are Doc Ref AI Assistant.

Your role is to help users:
- describe symptoms
- identify the appropriate medical specialty
- find suitable doctors
- continue conversations naturally

IMPORTANT WORKFLOW:

1. Understand the user's symptoms carefully.
2. Suggest the most appropriate medical specialty.
3. Explain briefly why that specialty may help.
4. Ask the user which city they are looking in.
5. ONLY AFTER the city is known:
   call the search_doctors function.

RULES:

- Do not diagnose diseases.
- Do not prescribe medications.
- Do not create fake doctors.
- Do not restart the conversation repeatedly.
- Continue the existing context naturally.
- Ask one follow-up question at a time.
- Keep responses concise and professional.
- If symptoms seem urgent or dangerous,
  advise the user to seek immediate medical attention.

FUNCTION RULES:

- search_doctors requires:
  - specialty
  - city

- Never call search_doctors unless BOTH are known.

EXAMPLES:

User:
"I have headache and dizziness"

Assistant:
"For these symptoms, a Neurologist may be the most appropriate specialist.
Which city are you looking in?"

User:
"Delhi"

Assistant:
(call search_doctors)

IMPORTANT:
The search_doctors function returns REAL doctor data from the backend.
Never invent doctor names yourself.
"""

RESULT_PROMPT = """ The result should be in Human readble formet"""


# =======================================================================
# MOCK ASYNCHRONOUS BACKEND FUNCTIONS
# =======================================================================



async def search_doctors(symptom: str, city: str = None):

    symptom_lower = symptom.lower()

    # Mock doctor database
    all_doctors = [
        {
            "id": 101,
            "name": "Dr. Alex Johnson",
            "specialty": "Internal Medicine",
            "city": "New York"
        },
        {
            "id": 102,
            "name": "Dr. Sarah Lee",
            "specialty": "Family Practice",
            "city": "Chicago"
        },
        {
            "id": 103,
            "name": "Dr. Robert Chen",
            "specialty": "Neurology",
            "city": "New York"
        },
        {
            "id": 104,
            "name": "Dr. Emily Davis",
            "specialty": "Internal Medicine",
            "city": "Los Angeles"
        },
        {
            "id": 105,
            "name": "Dr. Michael Brown",
            "specialty": "Cardiology",
            "city": "Chicago"
        },
    ]

    # Determine specialty from symptom
    specialty = None

    if "fever" in symptom_lower or "cold" in symptom_lower:
        specialty = "Internal Medicine"

    elif "headache" in symptom_lower or "migraine" in symptom_lower:
        specialty = "Neurology"

    elif "chest pain" in symptom_lower:
        specialty = "Cardiology"

    # No specialty found
    if not specialty:
        return {
            "doctors": [],
            "message": f"No doctors found for symptom: {symptom}"
        }

    # Filter doctors
    filtered_doctors = []

    for doctor in all_doctors:

        specialty_match = doctor["specialty"] == specialty

        city_match = (
            city is None
            or doctor["city"].lower() == city.lower()
        )

        if specialty_match and city_match:
            filtered_doctors.append(doctor)

    
    response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=RESULT_PROMPT
                )
    

    return str({
        # "specialty": specialty,
        # "city": city or "Anywhere",
        "doctors": filtered_doctors
    })

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
# FUNCTION_MAP = {
#     "search_doctors": search_doctors,
#     "check_available_slots": check_available_slots,
# }

# =======================================================================
# ASYNCHRONOUS ENGINE LOGIC (StatelessChatbot)
# =======================================================================

class StatelessChatbot:

    def __init__(self,history):
        self.history = history


    async def run_conversation_turn(self, current_message: str) -> Dict[str, Any]:
        retry = 3
        for attampts in range(retry):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=self.history,
                    config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
         tools=[
            types.Tool(
                function_declarations=[
                    search_doctors_func
                ]
            )
        ]
                    )
                )

                if response.function_calls:
                    function_call = response.function_calls[0]
                    if function_call.name == "search_doctors":

                        doctors_result = await search_doctors(
                        symptom=function_call.args["symptom"],
                        city=function_call.args.get("city")
                        )
                    print("kkkk", doctors_result)

                    return {
                        "response_text": doctors_result
                    }

                return {
                    "response_text": response.text
                }
            except Exception as e:
                print(e,"lll")
                return {
                    "response_text": str(e)
                }