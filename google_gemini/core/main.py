from google import genai
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain about Agentic AI?"
)
pprint(response.text)

