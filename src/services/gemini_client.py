from google import genai
from groq import Groq


try:
    # client = genai.Client(api_key="AIzaSyAw6JrwEAdz-VF7hiyBRDlruaZ_SQKOoLo")
    client = genai.Client(api_key="AIzaSyALD3fh17pypq4qaEUiohOQKQJZKwlZJkM")
except Exception as e:
    print(f"Failed to initialize Genai client: {e}")
    raise



try:
    groq_client = Groq(api_key="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")
except Exception as e:
    print(f"Failed to initialize the Gorq client: {e}")
    raise
