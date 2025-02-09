import os
from io import BytesIO
from typing import List

import PIL.Image
import requests
from google import genai
from google.genai import types


class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)

    def send_message(self, message: str) -> str:
        """
        Send a text message to Gemini and get the response
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash", contents=[message]
            )
            return response.text
        except Exception as e:
            print(f"Error sending message to Gemini: {str(e)}")
            return "Sorry, I couldn't process your message."

    def send_message_with_images(self, message: str, image_urls: List[str]) -> str:
        """
        Send a message with images to Gemini and get the response
        """
        try:
            images = []
            for url in image_urls:
                response = requests.get(url)
                img = PIL.Image.open(BytesIO(response.content))
                images.append(img)

            response = self.client.models.generate_content(
                model="gemini-2.0-flash", contents=[message, *images]
            )
            return response.text
        except Exception as e:
            print(f"Error sending message with images to Gemini: {str(e)}")
            return "Sorry, I couldn't process your message and images."

    def start_chat(self):
        """
        Start a new chat session with Gemini
        """
        # Note: Update this method based on the new client API chat functionality
        pass
