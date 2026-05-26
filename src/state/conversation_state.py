# class ConversationState:
#     def __init__(self):
#         self.conversation = []
#         self.symptom=[]
#         self.speciality = None
#         self.city = None
#         self.doctors = []
#         self.selected_doctor = None



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

            "city": None
        }

        self.doctors = []