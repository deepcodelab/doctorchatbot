import json
import httpx

from services.gemini_client import groq_client
api_url = "https://doctotrrefweb.onrender.com"

async def get_specializations():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{api_url}/api/speclization_list/"
        )

    return response.json()


SPECIALTY_AGENT_PROMPT = """
        You are SpecialtyAgent.

        Your task:
        - determine the most relevant medical specialty
        - based on structured medical context

        Rules:
        - only choose from available specializations
        - never invent a specialization
        - do not diagnose diseases
        - return valid JSON only

        Example:

        {
        "specialty": "General Physician",
        "reason": "Fever with mild symptoms is best evaluated by a general physician."
        }
        """


class SpecialtyAgent:

    async def run(self,state,task=None):
        specializations = await get_specializations()

        prompt = f"""
            Medical Context:
            {state.medical_context}
            Available Specializations:
            {specializations}

            IMPORTANT:
            You MUST choose ONLY from the available specializations list.
            Do not invent new specializations.
            """

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": SPECIALTY_AGENT_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_completion_tokens=200
        )

        content = response.choices[0].message.content
        print(content)
        data = json.loads(content)
        specialty = data["specialty"]
        state.medical_context["specialty"] = specialty
        return {
            "reply": (
                f"{data['reason']}\n\n"
                f"You should consult a "
                f"{specialty}.\n\n"
                f"Which city are you looking in?"
            )
        }