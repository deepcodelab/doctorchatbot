import json

from services.gemini_client import groq_client

from agents.symptom_agent import SymptomAgent
from agents.doctor_search_agent import DoctorSearchAgent
from agents.specialty_agent import SpecialtyAgent
from agents.show_appointment import ShowAppointments
from agents.doctor_availibility import DoctorAvailability
from services.prompts import SUPERVISOR_PROMPT
from agents.book_appointment import BookAppointment


class SupervisorAgent:

    def __init__(self):
        self.symptom_agent = SymptomAgent()
        self.doctor_agent = DoctorSearchAgent()
        self.specialty_agent = SpecialtyAgent()
        self.show_appointment = ShowAppointments()
        self.doctor_availability = DoctorAvailability()
        self.book_appointment = BookAppointment()

    async def run(self, message, state):

        # =====================================
        # Handle slot booking directly
        # =====================================

        if state.stage == "select_slot":

            msg = message.lower().strip()

            if msg.startswith("book slot"):

                try:
                    slot_number = msg.split()[-1]

                    if slot_number not in state.available_slots:
                        return {
                            "reply": (
                                "Invalid slot number. "
                                "Please select one of the available slots."
                            )
                        }

                    state.selected_slot = slot_number

                    print(
                        "Selected Slot:",
                        state.selected_slot
                    )

                    return await self.book_appointment.run(
                        state=state
                    )

                except Exception as e:
                    return {
                        "reply": (
                            "Please type something like "
                            "'book slot 1'"
                        )
                    }
        print("kkk", groq_client.api_key)

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
                print(state.__dict__,"ksksk")
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

        elif next_agent == "DoctorAvailability":
          return await self.doctor_availability.run(
              state=state
          )
        
        elif next_agent == "BookAppointment":
            return await self.book_appointment.run(state=state)


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