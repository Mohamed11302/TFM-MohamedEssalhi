import os
import requests
from dotenv import load_dotenv

load_dotenv()
class LLMmodel:
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        
        if self.env != "DEV":
            self.local_model_url = os.getenv("DEEPSEEK_PROD_URL")
            self.local_model_name = os.getenv("DEEPSEEK_PROD_MODEL")  
            self.token = os.getenv("DEEPSEEK_PROD_TOKEN", "token")  
            self.headers["Authorization"] = f"Bearer {self.token}"         
        else:
            self.local_model_url = os.getenv("DEEPSEEK_DEV_URL")
            self.local_model_name = os.getenv("DEEPSEEK_DEV_MODEL")

    def ask_model(self, prompt):
        try:
            response = requests.post(
                self.local_model_url,
                headers=self.headers,
                json={
                    "model": self.local_model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            print(f"Error llm model: {e}")
            return None
        
