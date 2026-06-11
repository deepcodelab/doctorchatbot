class ConversationState:
    def __init__(self):
        self.conversation = []
        self.authorization = None

        self.medical_context = {
            "primary_symptom": None,
            "duration": None,
            "temperature": None,
            "associated_symptoms": [],
            "negative_symptoms": [],
            "pain": {
                "location": None,
                "severity": None,
                "pattern": None
            },
            "specialty": None,
            "city": None,
            "selected_doctor_id": None
        }

        # New fields
        self.stage = None
        self.available_slots = {}
        self.selected_slot = None
        self.appointment = None

        self.doctors = []