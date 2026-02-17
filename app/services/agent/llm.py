import os
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY environment variable not set.")

llm = ChatMistralAI(api_key=MISTRAL_API_KEY, model="mistral-large-latest", temperature=0.2, max_tokens=2000)
