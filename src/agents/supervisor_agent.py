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


SUPERVISOR_PROMPT = """
You are the Supervisor Agent for Doc Ref AI.

Responsibilities:
- understand conversation
- extract structured medical information
- update medical memory
- decide next agent
- avoid repeated questions

Workflow Rules:

1. If specialty is missing:
   → route to SymptomAgent or SpecialtyAgent

2. If specialty exists AND city is missing:
   → ask for city

3. If specialty exists AND city exists:
   → route to DoctorSearchAgent

4. Do NOT return to SymptomAgent after specialty is determined
   unless the user introduces new symptoms.

5. Avoid repeated questions.

6. Respect already collected memory.

Extract:
- primary symptom
- duration
- temperature
- associated symptoms
- negative symptoms
- pain details
- specialty
- city

If enough information exists to recommend a specialty,
STOP asking follow-up questions.

Do not continue collecting unnecessary details.

If:
- primary symptom exists
- duration exists
- severity or temperature exists
- associated symptoms checked

then determine specialty.

Return ONLY valid JSON.

Example:

{
  "next_agent": "SymptomAgent",

  "memory_update": {

    "primary_symptom": "fever",

    "duration": "2 days",

    "temperature": "100F",

    "associated_symptoms": [
      "body pain"
    ],

    "pain": {
      "location": "legs",
      "severity": "mild",
      "pattern": "constant"
    }
  },

  "task": {
    "goal": "Determine specialty"
  }
}
"""


class SupervisorAgent:

    def __init__(self):

        self.symptom_agent = SymptomAgent()

        self.doctor_agent = DoctorSearchAgent()
        self.specialty_agent = SpecialtyAgent()

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