import json
from services.gemini_client import groq_client
from services.prompts import SYMPTOM_AGENT_PROMPT




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