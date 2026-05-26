# agents/symptom_agent.py

# import json

# from services.gemini_client import groq_client


# SYMPTOM_AGENT_PROMPT = """
# You are SymptomAgent for Doc Ref AI.

# Your responsibilities:
# - analyze user symptoms
# - ask intelligent follow-up questions
# - determine the appropriate medical specialty

# Rules:
# - Never diagnose diseases
# - Never prescribe medicine
# - Ask follow-up questions if information is insufficient
# - Determine specialty only when enough information exists

# Always return ONLY valid JSON.

# Possible responses:

# 1. Ask follow-up question

# {
#     "status": "needs_more_information",
#     "question": "..."
# }

# 2. Specialty determined

# {
#     "status": "specialty_determined",
#     "specialty": "...",
#     "reason": "..."
# }
# """


# class SymptomAgent:

#     async def run(self, message, state):

#         prompt = f"""

#         Current conversation state:

#         Symptoms:
#         {state.symptom}

#         User message:
#         {message}
#         """

#         response = client.models.generate_content(
#             model="gemini-2.5-flash-lite",
#             contents=prompt,
#             config={
#                 "system_instruction": SYMPTOM_AGENT_PROMPT,
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

#         data = json.loads(cleaned_text)

#         status = data["status"]

#         # Save user symptom history
#         state.symptom.append(message)

#         # Case 1 → AI needs more information
#         if status == "needs_more_information":

#             return {
#                 "reply": data["question"]
#             }

#         # Case 2 → Specialty determined
#         elif status == "specialty_determined":

#             state.specialty = data["specialty"]

#             return {
#                 "reply": (
#                     f"{data['reason']}\n\n"
#                     f"You may need a "
#                     f"{state.specialty}.\n\n"
#                     f"Which city are you looking in?"
#                 )
#             }

#         return {
#             "reply": (
#                 "I could not analyze "
#                 "the symptoms properly."
#             )
#         }


# agents/symptom_agent.py

import json

from services.gemini_client import groq_client


SYMPTOM_AGENT_PROMPT = """
You are SymptomAgent for Doc Ref AI.

Responsibilities:
- analyze symptoms
- ask smart follow-up questions
- determine medical specialty

Rules:
- never diagnose diseases
- never prescribe medicine
- ask ONE follow-up question at a time
- avoid repeating previous questions
- determine specialty when enough information exists
- return ONLY valid JSON
- no markdown

You should stop asking questions once enough information is available.

Do not continue unnecessary medical intake.

Prioritize identifying the correct specialty early.

Response formats:

1. Need more information

{
  "status": "needs_more_information",
  "question": "..."
}

2. Specialty determined

{
  "status": "specialty_determined",
  "specialty": "...",
  "reason": "..."
}

Do not ask questions already answered.

Use existing medical context.

Only ask about missing information.
"""


class SymptomAgent:

    async def run(self, message, state,task=None):
        print(state.authorization,"fhffgfg")

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
            {task.get("known_symptoms", []) if task else []}

            Negative Symptoms:
            {task.get("negative_symptoms", []) if task else []}

            Goal:
            {task.get("goal", "") if task else ""}

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
                    "content": SYMPTOM_AGENT_PROMPT
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

        data = json.loads(content)

        status = data["status"]

        # Save symptom memory
        # state.symptom.append(message)

        # Needs more information
        if status == "needs_more_information":

            return {
                "reply": data["question"]
            }

        # Specialty determined
        elif status == "specialty_determined":

            state.speciality = data["specialty"]

            return {
                "reply": (
                    f"{data['reason']}\n\n"
                    f"You may need a "
                    f"{state.speciality} specialist.\n\n"
                    f"Which city are you looking in?"
                )
            }

        return {
            "reply": (
                "I could not analyze "
                "the symptoms properly."
            )
        }