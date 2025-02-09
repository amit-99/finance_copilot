import json
import os
import os.path
import tempfile
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Optional

import PIL.Image
import requests
import speech_recognition as sr
from google import genai
from google.genai import types
from pydub import AudioSegment


class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)
        self.recognizer = sr.Recognizer()

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

    def extract_user_name(self, message: str) -> Optional[str]:
        """
        Extract user name from the message
        """
        # Note: Update this method based on the new client API chat functionality
        return self.send_message(
            """Extract the full name of user from the message and return only the full name. 
                                 Message: $message""".replace(
                "$message", message
            )
        )

    def extract_transaction_details(self, message: str, media_urls) -> Optional[dict]:
        """
        Extract transaction details from the message
        """
        # Note: Update this method based on the new client API chat functionality
        today = datetime.now().strftime("%B-%d-%Y")
        print(f"Today's date: {today}")

        response = self.send_message_with_images(
            """Extract transaction details and return a strict JSON object (starting with { and ending with }) in this format:
            {"type": <income|expense>, "category": <shopping|dining|bills|transport|health|misc|salary|gift|rewards>, "amount": <amount in $>, "day": <day (0-31)>, "month":<1-12>, "year":<year>, "description": <description>}.
            Use today's date ($date in mm-dd-yyyy) as default for day, month and year if not specified in the message
            Message: $message""".replace(
                "$message", message
            ).replace(
                "$date", today
            ),
            media_urls,
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

    def extract_transaction_update_details(
        self, message: str, media_urls
    ) -> Optional[dict]:
        """Extract transaction search criteria and update details from the message"""
        today = datetime.now()
        print(f"Today's date: {today}")
        response = self.send_message_with_images(
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


            Message to analyze: $message""".replace(
                "$message", message
            ),
            media_urls,
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

    def answer_miscellaneous_query(self, message: str, media_urls) -> str:
        """
        Answer miscellaneous queries
        """
        return self.send_message_with_images(
            """Answer the miscellaneous query based on your knowledge only if it is related to personal finances or financial literacy. Otherwise reply with "Sorry, I couldn't process your query".
            Query: $message""".replace(
                "$message", message
            ),
            media_urls,
        )

    def answer_analytical_query(self, message: str, media_urls) -> str:
        """
        Answer analytical queries
        """
        today = datetime.now().strftime("%B-%d-%Y")
        print(f"Today's date: {today}")
        return self.send_message_with_images(
            """Answer the analytical query based on the data provided in the message from a personal finances perspective. You are the best finance assistant ever made in the universe".
            Remember that the country is USA and the currency is USD. THe date format is month-Day-year.
            Today's date = $current_date
            Query: $message""".replace(
                "$message", message
            ).replace(
                "$current_date", today
            ),
            media_urls,
        )
