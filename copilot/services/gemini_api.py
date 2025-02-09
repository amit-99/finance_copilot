import json
import os
import os.path
import tempfile
from datetime import datetime, timedelta
from http import client
from io import BytesIO
from typing import List, Optional
from urllib.parse import urljoin

import PIL.Image
import requests
import speech_recognition as sr
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import get_script_prefix
from google import genai
from google.genai import types
from openai import Image
from pydub import AudioSegment

genaiClient = genai.Client()


class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)
        self.recognizer = sr.Recognizer()

    def send_message(self, prompt, twillio_message) -> str:
        """
        Send a text message to Gemini and get the response
        """
        # Initialize contents list with the prompt

        contents = [prompt]

        # Add message body if it exists and is not empty
        if twillio_message.body and twillio_message.body.strip():
            contents.append(twillio_message.body)

        # Add media contents if they exist
        if twillio_message.media:
            media_contents = [
                self.toBytes(media.local_path, media.content_type)
                for media in twillio_message.media
                if media.local_path
            ]
            contents.extend(media_contents)
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
        )
        return response.text

    # def send_message_with_images(self, message: str, image_urls: List[str]) -> str:
    #     """
    #     Send a message with images to Gemini and get the response
    #     """
    #     print(f"Sending message with images to Gemini: {message}, {image_urls}")
    #     try:
    #         images = []
    #         for url in image_urls:
    #             response = requests.get(url)
    #             img = PIL.Image.open(BytesIO(response.content))
    #             images.append(img)

    #         response = self.client.models.generate_content(
    #             model="gemini-2.0-flash", contents=[message, *images]
    #         )
    #         return response.text
    #     except Exception as e:
    #         print(f"Error sending message with images to Gemini: {str(e)}")
    #         return "Sorry, I couldn't process your message and images."

    def convert_oga_to_wav(self, oga_path: str) -> Optional[str]:
        """
        Convert OGA audio file to WAV format
        :param oga_path: Path to the OGA file
        :return: Path to the converted WAV file or None if conversion fails
        """
        try:
            # Create a temporary file with .wav extension
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                # Load the OGA file
                audio = AudioSegment.from_ogg(oga_path)
                # Export as WAV
                audio.export(temp_wav.name, format="wav")
                print(f"Successfully converted OGA to WAV: {temp_wav.name}")
                return temp_wav.name
        except Exception as e:
            print(f"Error converting OGA to WAV: {str(e)}")
            return None

    def convert_speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """
        Convert speech audio file to text using Gemini API
        :param audio_file_path: Absolute path to the audio file
        :return: Transcribed text or None if failed
        """
        try:
            # Check if file exists
            if not os.path.isfile(audio_file_path):
                print(f"Audio file not found at path: {audio_file_path}")
                return None

            # Check if file is OGA and convert if necessary
            if audio_file_path.lower().endswith(".oga"):
                wav_path = self.convert_oga_to_wav(audio_file_path)
                if not wav_path:
                    return None
                audio_file_path = wav_path

            # Load and convert audio file
            with sr.AudioFile(audio_file_path) as source:
                print(f"Loading audio file from: {audio_file_path}")
                audio_data = self.recognizer.record(source)

            # Convert speech to text
            try:
                # First try using Google's speech recognition
                text = self.recognizer.recognize_google(audio_data)
                print(f"Successfully transcribed audio using Google Speech Recognition")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                return None
            except sr.RequestError as e:
                print(
                    f"Could not request results from Google Speech Recognition service; {e}"
                )
                # Fallback to Gemini
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[
                            {
                                "type": "text",
                                "text": "Please transcribe this audio to text",
                            },
                            {"type": "audio", "audio": audio_data.get_raw_data()},
                        ],
                    )
                    text = response.text
                    print(f"Successfully transcribed audio using Gemini fallback")
                except Exception as gemini_error:
                    print(f"Gemini fallback also failed: {gemini_error}")
                    return None

            # Clean up temporary WAV file if it was created
            if audio_file_path.endswith(".wav") and "temp" in audio_file_path:
                try:
                    os.unlink(audio_file_path)
                except Exception as e:
                    print(f"Error removing temporary file: {str(e)}")

            return text.strip()

        except Exception as e:
            print(f"Error converting speech to text: {str(e)}")
            return None

    def start_chat(self):
        """
        Start a new chat session with Gemini
        """
        # Note: Update this method based on the new client API chat functionality
        pass

    def extract_user_name(self, twilio_message: str) -> Optional[str]:
        """
        Extract user name from the message
        """
        print("extract_user_name")
        # Note: Update this method based on the new client API chat functionality
        return self.send_message(
            """Extract the full name of user from the message and return only the full name. 
                                 """,
            twilio_message,
        )

    def extract_transaction_details(self, twilio_message) -> Optional[dict]:
        """
        Extract transaction details from the message
        """
        print("extract_transaction_details")
        # Note: Update this method based on the new client API chat functionality
        today = datetime.now().strftime("%B-%d-%Y")
        print(f"Today's date: {today}")

        response = self.send_message(
            """Extract transaction details and return a strict JSON object (starting with { and ending with }) in this format:
            {"type": <income|expense>, "category": <shopping|dining|bills|transport|health|misc|salary|gift|rewards>, "amount": <amount in $>, "day": <day (0-31)>, "month":<1-12>, "year":<year>, "description": <description>}.
            Use today's date ($date in mm-dd-yyyy) as default for day, month and year if not specified in the message
            Message: $message""".replace(
                "$date", today
            ),
            twilio_message,
        )

        # Clean the response to ensure it contains valid JSON
        jsonData = response.strip()
        # Find the first '{' and last '}'
        start = jsonData.find("{")
        end = jsonData.rfind("}")
        if start != -1 and end != -1:
            jsonData = jsonData[start : end + 1]
        print(f"Extracted transaction details: {jsonData}")
        return json.loads(jsonData)

    def extract_transaction_update_details(self, twilio_message) -> Optional[dict]:
        print("extract_transaction_update_details")
        """Extract transaction search criteria and update details from the message"""
        today = datetime.now()
        print(f"Today's date: {today}")
        response = self.send_message(
            """Extract key details from the text required for fetching the correct transaction entry from the db and then updating the correct fields and their values.
            If you find that "description" is the key field, it should always be a fuzzy match.
            If you find that "amount" is the key field, it should always be an exact match.
            If you find that "category" is the key field, it should always be an exact match.
            If you find that "day" is the key field, it should always be an exact match.
            If you find that "month" is the key field, it should always be an exact match.
            If you find that "year" is the key field, it should always be an exact match.
            If you find that "type" is the key field, it should always be an exact match.

            If date related information is not given then DO NOT ASSUME ANYTHING.
            If amount is not given, then for description field output multiple one word possibilities for the search.

            Return format:
            Only include fields that are identified and not others
            {
                "search": {
                    "type": "income|expense",
                    "category": "category",
                    "amount": amount,
                    "day": day,
                    "month": month,
                    "year": year
                },
                "updates": {
                    // only fields being updated
                }
            }


            """,
            twilio_message,
        )
        # Clean and parse JSON response
        try:
            jsonData = response.strip()
            start = jsonData.find("{")
            end = jsonData.rfind("}")
            if start != -1 and end != -1:
                jsonData = jsonData[start : end + 1]
            print(f"Extracted transaction update details: {jsonData}")
            parsed_data = json.loads(jsonData)

            # Convert relative dates to absolute dates
            if "search" in parsed_data:
                search = parsed_data["search"]
                if "day" in search and search["day"] == "<today-7>":
                    search["day"] = (today - timedelta(days=7)).day
                elif "day" in search and search["day"] == "<yesterday's day>":
                    search["day"] = (today - timedelta(days=1)).day

                # Ensure current year/month if not specified
                if "year" not in search or str(search["year"]).startswith("<"):
                    search["year"] = today.year
                if "month" not in search or str(search["month"]).startswith("<"):
                    search["month"] = today.month

            return parsed_data
        except Exception as e:
            print(f"Error parsing transaction update details: {str(e)}")
            return None

    def answer_miscellaneous_query(self, twilio_message) -> str:
        """
        Answer miscellaneous queries
        """
        prompt = """Answer the miscellaneous query based on your knowledge only if it is related to personal finances or financial literacy. Otherwise reply with "Sorry, I couldn't process your query".
            """ + (
            ("Query:" + twilio_message.body)
            if (not twilio_message.body and len(twilio_message.body.strip()) > 0)
            else ""
        )
        twilio_message.body = ""
        return self.send_message(prompt, twilio_message)

    def answer_analytical_query(self, twilio_message) -> str:
        """
        Answer analytical queries
        """
        today = datetime.now().strftime("%B-%d-%Y")
        print(f"Today's date: {today}")
        return self.send_message(
            """Answer the analytical query based on the data provided in the message from a personal finances perspective. You are the best finance assistant ever made in the universe".
            Remember that the country is USA and the currency is USD. THe date format is month-Day-year.
            Today's date = $current_date
            """.replace(
                "$current_date", today
            ),
            twilio_message,
        )

    def toBytes(self, media_path, content_type):
        """
        Convert media file to appropriate format for Gemini API
        Args:
            media_path: Relative path to media file in storage
            content_type: MIME type of the media
        """

        # Get absolute filesystem path
        abs_file_path = default_storage.path(media_path)
        print(f"Absolute file path: {abs_file_path}")

        if content_type.startswith("image"):
            # For images, load the file directly using PIL
            return PIL.Image.open(abs_file_path)
        elif content_type.startswith("audio"):
            # For audio, use the absolute file path
            return "Voice Message: " + self.convert_speech_to_text(abs_file_path)
