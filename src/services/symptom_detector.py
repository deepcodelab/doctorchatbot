class SymptomDetector:

    SYMPTOM_MAP = {
        "fever": "General Physician",
        "headache": "Neurologist",
        "skin": "Dermatologist",
        "eye": "Ophthalmologist",
        "chest pain": "Cardiologist",
        "stomach": "Gastroenterologist",
    }

    @classmethod
    def detect(cls, message: str) -> str | None:
        message = message.lower()
        for symptom, specialization in cls.SYMPTOM_MAP.items():
            if symptom in message:
                return specialization
        return None
