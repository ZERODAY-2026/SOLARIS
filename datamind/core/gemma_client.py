import os
import json
import re
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class GemmaClient:
    """
    Communicates with Google Gemma 4 models via OpenRouter or NVIDIA NIM.
    Provides structured intent extraction, Text-to-SQL synthesis, and
    evidence-grounded plain-language explanations.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("GEMMA_MODEL", "google/gemma-4-26b-a4b-it")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://zerodayoss.iiitdharwad.ac.in",
            "X-Title": "DataMind PS1"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                return f"Error from Gemma API ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Exception calling Gemma: {str(e)}"

    def extract_sql_from_response(self, text: str) -> str:
        """
        Extracts raw SQL from markdown code fences or plain text.
        """
        match = re.search(r'```(?:sql)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        lines = [line.strip() for line in text.strip().split("\n")]
        sql_lines = [l for l in lines if not l.startswith("#") and not l.startswith("//")]
        return "\n".join(sql_lines).strip().rstrip(";")
