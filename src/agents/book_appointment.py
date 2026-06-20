import json
import httpx
from services.gemini_client import groq_client

api_url = "http://127.0.0.1:8000/api/"
# api_url = "https://doctotrrefweb.onrender.com/api/"

async def book_doctor(token, data):
    print("4444")
    headers = {
        "Authorization": token
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{api_url}book_appointment/",
            headers=headers,
            json=data
        )
        print(response,"888")

        response.raise_for_status()

    return response.json()



class BookAppointment:
    async def run(self, state):
        token = state.authorization
        doctor_id = state.medical_context.get("selected_doctor_id")

        available_slots = state.available_slots
        selected_option = state.selected_slot

        print("Selected Option:", selected_option)
        print("Available Slots:", available_slots)

        if not selected_option:
            return {
                "success": False,
                "error": "No slot selected"
            }

        selected_slot = available_slots.get(str(selected_option))

        if not selected_slot:
            return {
                "success": False,
                "error": f"Invalid slot selected: {selected_option}"
            }
        print(type(doctor_id),"ll")
        booking_data = {
            "doctor": int(doctor_id),
            "appointment_date": selected_slot["date"],
            "appointment_time": selected_slot["start_time"],
        }

        try:
            result = await book_doctor(
                token=token,
                data=booking_data
            )

            state.appointment = result

            return {
                "reply": (
                    f"Appointment booked successfully.\n\n"
                    f"Date: {selected_slot['date']}\n"
                    f"Time: {selected_slot['start_time']} - "
                    f"{selected_slot['end_time']}"
                )
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }