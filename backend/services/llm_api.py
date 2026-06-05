from config.settings import GEMINI_API_KEY
from google import genai

class LLM_GEN:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = "gemma-4-31b-it"

    def generate_content(self, content):
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=content
        )
        return response.text