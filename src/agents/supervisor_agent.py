# from agents.symptom_agent import SymptomAgent
# from agents.doctor_search_agent import DoctorSearchAgent


# SUPERVISOR_PROMPT = """
# You are the Supervisor Agent for Doc Ref AI.

# Your job:
# - manage the overall workflow
# - decide which specialized agent should act next
# - decide what information is missing
# - continue conversations intelligently

# Available agents:

# 1. SymptomAgent
#    Responsibilities:
#    - analyze symptoms
#    - ask follow-up questions
#    - determine medical specialty

# 2. DoctorSearchAgent
#    Responsibilities:
#    - search doctors
#    - filter by specialty and city

# 3. BookingAgent
#    Responsibilities:
#    - manage appointment booking

# Rules:
# - Do not diagnose diseases
# - Do not prescribe medications
# - Dynamically decide the next best action
# - Continue the workflow until the user's goal is complete

# Always return valid JSON only.

# Format:

# {
#   "next_agent": "AgentName",
#   "goal": "What the next agent should accomplish"
# }
# """


# class SupervisorAgent:

#     def __init__(self):
#         self.symptom_agent = SymptomAgent()
#         self.doctor_search_agent = DoctorSearchAgent()

#     async def run(self, message, state):

#         if not state.speciality:
#             return await self.symptom_agent.run(
#                 message,
#                 state
#             )

#         if not state.city:
#             return await self.doctor_search_agent.run(
#                 state
#             )

        



# # agents/supervisor_agent.py

# import json

# from services.gemini_client import client

# from agents.symptom_agent import SymptomAgent
# from agents.doctor_search_agent import DoctorSearchAgent
# # from agents.booking_agent import BookingAgent


# SUPERVISOR_PROMPT = """
# You are the Supervisor Agent for Doc Ref AI.

# Your responsibilities:
# - understand the entire conversation
# - extract important medical context
# - decide which agent should act next
# - prepare the minimum relevant context for that agent

# Available agents:

# 1. SymptomAgent
# Needs:
# - symptoms
# - negative symptoms
# - follow-up context

# 2. DoctorSearchAgent
# Needs:
# - specialty
# - city

# 3. BookingAgent
# Needs:
# - selected doctor
# - appointment preference

# Rules:
# - Do not send unnecessary history
# - Extract structured information from conversation
# - Delegate only relevant context
# - Continue workflow intelligently

# Always return JSON only.

# Example format:

# {
#   "next_agent": "SymptomAgent",
#   "task": {
#       "known_symptoms": [
#           "fever",
#           "headache"
#       ],
#       "negative_symptoms": [
#           "cough"
#       ],
#       "goal": "Determine specialty"
#   }
# }
# """


# class SupervisorAgent:

#     def __init__(self):

#         self.symptom_agent = SymptomAgent()

#         self.doctor_agent = DoctorSearchAgent()

#         # self.booking_agent = BookingAgent()

#     async def run(self, message, state):

#         conversation_text = ""

#         for msg in state.conversation:

#             conversation_text += (
#                 f"{msg['role']}: "
#                 f"{msg['content']}\n"
#             )

#         prompt = f"""
#             Conversation History:

#             {conversation_text}

#             Current State:

#             Symptoms:
#             {state.symptom}

#             Specialty:
#             {state.speciality}

#             City:
#             {state.city}

#             Doctors:
#             {state.doctors}

#             Latest User Message:
#             {message}
#             """

#         response = client.models.generate_content(
#             model="gemini-2.5-flash-lite",
#             contents=prompt,
#             config={
#                 "system_instruction": SUPERVISOR_PROMPT,
#                 "response_mime_type": "application/json"
#             }
#         )

#         cleaned_text = response.text.strip()

#         cleaned_text = cleaned_text.replace(
#             "```json",
#             ""
#         )

#         cleaned_text = cleaned_text.replace(
#             "```",
#             ""
#         )

#         cleaned_text = cleaned_text.strip()

#         print(cleaned_text)

#         decision = json.loads(cleaned_text)

#         next_agent = decision["next_agent"]

        

#         print("Supervisor Decision:", next_agent)
#         # print("Goal:", goal)

#         # Route to correct agent

#         if next_agent == "SymptomAgent":

#             return await self.symptom_agent.run(
#                 message=message,
#                 state=state,
#             )

#         elif next_agent == "DoctorSearchAgent":

#             return await self.doctor_agent.run(
#                 message=message,
#                 state=state,
#             )

#         # elif next_agent == "BookingAgent":

#         #     return await self.booking_agent.run(
#         #         message=message,
#         #         state=state,
#         #         goal=goal
#         #     )

#         return {
#             "reply": "I could not determine the next step."
#         }


# agents/supervisor_agent.py

import json

from services.gemini_client import groq_client

from agents.symptom_agent import SymptomAgent
from agents.doctor_search_agent import DoctorSearchAgent
from agents.specialty_agent import SpecialtyAgent
from agents.show_appointment import ShowAppointments


SUPERVISOR_PROMPT = """
You are the Supervisor Agent for Doc Ref AI.

Your role:
- understand the user's intent
- manage the overall workflow
- decide which specialized agent should handle the request
- update conversation memory
- avoid repeated questions
- continue conversations intelligently

You are NOT a medical diagnosis system.

Never:
- diagnose diseases
- prescribe medicines
- provide emergency medical decisions

-----------------------------------
AVAILABLE AGENTS
-----------------------------------

1. GreetingAgent
Responsibilities:
- greet users
- start conversations

2. SymptomAgent
Responsibilities:
- analyze symptoms
- ask follow-up questions
- collect medical context

Needs:
- symptoms
- duration
- severity
- associated symptoms

3. SpecialtyAgent
Responsibilities:
- determine appropriate medical specialty

Needs:
- enough symptom context

4. DoctorSearchAgent
Responsibilities:
- search doctors
- filter doctors by specialty and city

Needs:
- specialty
- city

5. BookingAgent
Responsibilities:
- manage appointment booking

Needs:
- selected doctor
- appointment preference

6. ShowAppointments
Responsibilities:
- fetch and show user appointments

Needs:
- appointment intent only

-----------------------------------
GENERAL RULES
-----------------------------------

1. First determine the user's REAL intent.

The user may:
- describe symptoms
- search doctors
- ask medical questions
- book appointments
- view appointments
- continue previous conversations
- greet

2. Respect already collected memory.

3. Avoid repeated questions.

4. Do not ask unnecessary follow-up questions.

5. If enough information exists to determine a specialty,
stop collecting symptom details.

6. Do NOT return to SymptomAgent after specialty is determined
unless the user introduces NEW symptoms.

7. Use conversation history and memory before asking questions.

8. Always choose the MOST relevant next agent.

-----------------------------------
MEDICAL WORKFLOW RULES
-----------------------------------

1. If specialty is missing:
→ route to SymptomAgent or SpecialtyAgent

2. If specialty exists AND city is missing:
→ ask for city OR route to DoctorSearchAgent

3. If specialty exists AND city exists:
→ route to DoctorSearchAgent

4. If user introduces new symptoms:
→ route back to SymptomAgent

5. If enough symptom context exists:
→ route to SpecialtyAgent

Enough symptom context means:
- primary symptom exists
- duration exists
- severity OR temperature exists
- associated symptoms checked

-----------------------------------
APPOINTMENT RULES
-----------------------------------

If the user asks about:
- my appointments
- show appointments
- appointment history
- upcoming appointments
- booked appointments
- scheduled appointments
- my bookings
- do i have any bookings

Then ALWAYS route to:
"ShowAppointments"

Do NOT:
- ask symptom questions
- collect medical information
- route to SymptomAgent

-----------------------------------
GREETING RULES
-----------------------------------

If the user says:
- hi
- hello
- hey

AND no medical context exists:
→ route to GreetingAgent

-----------------------------------
MEMORY EXTRACTION
-----------------------------------

Extract and update structured memory when available:

- primary_symptom
- duration
- temperature
- associated_symptoms
- negative_symptoms
- pain details
- specialty
- city

Pain object format:

"pain": {
    "location": "",
    "severity": "",
    "pattern": ""
}

-----------------------------------
OUTPUT RULES
-----------------------------------

Return ONLY valid JSON.

Do not return markdown.

Do not explain reasoning.

-----------------------------------
JSON FORMAT
-----------------------------------

{
  "next_agent": "AgentName",

  "memory_update": {

    "primary_symptom": "fever",

    "duration": "2 days",

    "temperature": "100F",

    "associated_symptoms": [
      "body pain"
    ],

    "negative_symptoms": [
      "cough"
    ],

    "pain": {
      "location": "legs",
      "severity": "mild",
      "pattern": "constant"
    },

    "specialty": "General Physician",

    "city": "Delhi"
  },

  "task": {
    "goal": "Determine specialty"
  }
}

-----------------------------------
EXAMPLES
-----------------------------------

User:
"Hi"

Response:
{
  "next_agent": "GreetingAgent",
  "memory_update": {},
  "task": {
    "goal": "Greet user"
  }
}

User:
"I have fever and body pain for 2 days"

Response:
{
  "next_agent": "SymptomAgent",
  "memory_update": {
    "primary_symptom": "fever",
    "duration": "2 days",
    "associated_symptoms": [
      "body pain"
    ]
  },
  "task": {
    "goal": "Collect severity information"
  }
}

User:
"My fever is 101F"

Response:
{
  "next_agent": "SpecialtyAgent",
  "memory_update": {
    "temperature": "101F"
  },
  "task": {
    "goal": "Determine specialty"
  }
}

User:
"I need a skin doctor in Mumbai"

Response:
{
  "next_agent": "DoctorSearchAgent",
  "memory_update": {
    "specialty": "Dermatologist",
    "city": "Mumbai"
  },
  "task": {
    "goal": "Search doctors"
  }
}

User:
"Show my appointments"

Response:
{
  "next_agent": "ShowAppointments",
  "memory_update": {},
  "task": {
    "goal": "Fetch user appointments"
  }
}

User:
"Do I have any bookings?"

Response:
{
  "next_agent": "ShowAppointments",
  "memory_update": {},
  "task": {
    "goal": "Fetch user appointments"
  }
}
"""


class SupervisorAgent:

    def __init__(self):

        self.symptom_agent = SymptomAgent()

        self.doctor_agent = DoctorSearchAgent()
        self.specialty_agent = SpecialtyAgent()
        self.show_appointment = ShowAppointments()

    async def run(self, message, state):

        # Keep only recent history
        recent_history = state.conversation[-6:]

        conversation_text = ""

        for msg in recent_history:

            conversation_text += (
                f"{msg['role']}: "
                f"{msg['content']}\n"
            )

        prompt = f"""
            Conversation History:
            {conversation_text}

            Medical Context:
            {state.medical_context}

            Doctors:
            {state.doctors}

            Latest User Message:
            {message}
            """

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            response_format={
                "type": "json_object"
            },

            messages=[

                {
                    "role": "system",
                    "content": SUPERVISOR_PROMPT
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.3,

            max_completion_tokens=300
        )

        content = response.choices[0].message.content

        print(content)

        decision = json.loads(content)

        memory_update = decision.get(
            "memory_update",
            {}
        )

        next_agent = decision["next_agent"]

        # Update state memory
        for key, value in memory_update.items():

            if isinstance(value, dict):

                state.medical_context[key].update(value)

            else:

                state.medical_context[key] = value

                next_agent = decision["next_agent"]

                task = decision.get("task", {})

        print("Supervisor Decision:", next_agent)

        # Route agents

        if next_agent == "SymptomAgent":

            return await self.symptom_agent.run(
                message=message,
                state=state,
                # task=task
            )

        elif next_agent == "DoctorSearchAgent":

            return await self.doctor_agent.run(
                message=message,
                state=state,
                # task=task
            )
        
        elif next_agent == "SpecialtyAgent":

            return await self.specialty_agent.run(
                state=state,
                task=task
            )
        
        elif next_agent == "ShowAppointments":

            return await self.show_appointment.run(state=state)


        elif next_agent == "GreetingAgent":

            return {
                "reply": (
                    "Hello! "
                    "What symptoms are you experiencing?"
                )
            }

        return {
            "reply": "I could not determine the next step."
        }