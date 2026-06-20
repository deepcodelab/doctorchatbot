import json
import httpx


api_url = "http://127.0.0.1:8000/api"
# api_url = "https://doctotrrefweb.onrender.com/api"

async def my_appointment(token):
    url = f"{api_url}/appointments/"
    headers = {
        "Authorization": token
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers
        )

    response.raise_for_status()
    return response.json()


class ShowAppointments:
    async def run(self, state):
        token = state.authorization

        appointment = await my_appointment(token)
        print(appointment,"lkkkk")
        return {
            "reply": (
                f"Your appointments"
            )
        }