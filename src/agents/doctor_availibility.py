import httpx

api_url = "http://127.0.0.1:8000/api/"
# api_url = "https://doctotrrefweb.onrender.com/api/"


async def doctor_availability(doctor_id, token):

    headers = {"Authorization": token}

    async with httpx.AsyncClient() as client:

        response = await client.get(
            url=f"{api_url}chat_doctor_availability/{doctor_id}/",
            headers=headers
        )
        print("fdfgfdg")
        response.raise_for_status()

    return response.json()


class DoctorAvailability:
    async def run(self, state):
        try:
            doctor_id = state.medical_context.get("selected_doctor_id")
            available_slots = await doctor_availability(
                doctor_id,
                state.authorization
            )
            if not available_slots:
                return {
                    "reply": (
                        "No appointment slots are available right now."
                    )
                }

            message = "Available appointment slots:\n\n"
            # for slot in available_slots:
            #     message += (
            #         f"Date: {slot.get('date')}\n"
            #         f"Time: {slot.get('time')}\n"
            #         f"Doctor: Dr. {slot.get('doctor')}\n\n"
            #     )
            # print(available_slots,"hhshs")

            message = "Available appointment slots:\n\n"

            for index, slot in enumerate(available_slots.get("doctor_data", []),start=1):
                state.available_slots[str(index)] = slot
                message += (
                    f"{index}. "
                    f"Date: {slot.get('date')} | "
                    f"Time: {slot.get('start_time')} - {slot.get('end_time')}\n"
                )

            state.stage = "select_slot"
            message += (
                "\nTo book an appointment, "
                "type: 'book slot 1' or 'book slot 2'"
            )
            print("message", message)
            return {
                "reply": message
            }

        except httpx.HTTPStatusError:
            return {
                "reply": (
                    "Failed to fetch appointment availability."
                )
            }
        except Exception as e:

            return {
                "reply": f"Error: {str(e)}"
            }