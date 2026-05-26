import json
import httpx

api_url = "http://127.0.0.1:8000/api"

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
        print(doctor_list,"lkkkk")
        return {
            "reply": (
                f"I found these doctors "
                f"in {city}:\n\n"
                f"{doctor_list}\n"
                f"Which doctor would "
                f"you like to book?"
            )
        }