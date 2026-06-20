import json
import httpx
from services.gemini_client import groq_client
from services.prompts import DOCTOR_SEARCH_PROMPT

api_url = "http://127.0.0.1:8000/api"
# api_url = "https://doctotrrefweb.onrender.com/api"

async def search_doctor(spicility, city, token):
    url = f"{api_url}/chat_doctors/bot_search/"
    headers = {
        "Authorization": token
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={
                "specialty": spicility,
                "city": city
            },
            headers=headers
        )
    response.raise_for_status()
    return response.json()


class DoctorSearchAgent:
    async def run(self,message,state,task=None):
        medical_context = state.medical_context
        specialty = medical_context.get("specialty")
        city = medical_context.get("city")
        token = state.authorization

        if not specialty:
            return {
                "reply": (
                    "I still need to determine "
                    "the medical specialty."
                )
            }

        if not city:
            return {
                "reply": (
                    "Which city are you "
                    "looking in?"
                )
            }

        doctor_list = await search_doctor(specialty, city, token)

        prompt = f"""
            Specialty:
            {specialty}
            City:
            {city}
            Doctor API Response:
            {json.dumps(doctor_list, indent=2)}
            """

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": DOCTOR_SEARCH_PROMPT
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

        return {
            "reply": f"{data['message']}\n\n{data['follow_up']}"}