import mimetypes
import os
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from ..models.twilio_message import TwilioMedia, TwilioMessage

# Load environment variables
load_dotenv()


class TwilioService:
    """
    Twilio Service for WhatsApp communication with media support
    WhatsApp number format: if number is "+1234567890", it becomes "whatsapp:+1234567890"
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        self.client = Client(self.account_sid, self.auth_token)
        self.media_storage_path = "whatsapp_media"

    def format_whatsapp_number(self, phone_number: str) -> str:
        """Format phone number for WhatsApp"""
        return f"whatsapp:{phone_number}"

    def _download_media(self, media_url: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download media from Twilio URL using authentication
        Returns: Tuple of (content_bytes, filename)
        """
        try:
            response = requests.get(
                media_url, auth=(self.account_sid, self.auth_token), stream=True
            )
            if response.status_code == 200:
                # Get filename from URL or Content-Disposition header
                filename = os.path.basename(urlparse(media_url).path)
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition and "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')
                return response.content, filename
            return None, None
        except Exception as e:
            print(f"Error downloading media: {str(e)}")
            return None, None

    def _save_media(
        self, content: bytes, filename: str, message_sid: str
    ) -> Optional[str]:
        """
        Save media content to Django storage
        Returns: Saved file path or None
        """
        try:
            # Create path: whatsapp_media/YYYY-MM-DD/message_sid/filename
            today = datetime.now().strftime("%Y-%m-%d")
            relative_path = os.path.join(
                self.media_storage_path, today, message_sid, filename
            )

            # Save file using Django's storage
            file_path = default_storage.save(relative_path, ContentFile(content))
            return file_path
        except Exception as e:
            print(f"Error saving media: {str(e)}")
            return None

    def _get_file_extension(self, content_type: str) -> str:
        """Get file extension from content type"""
        extension = mimetypes.guess_extension(content_type)
        if not extension:
            # Fallback extensions for common types
            fallbacks = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "audio/ogg": ".ogg",
                "audio/mpeg": ".mp3",
                "video/mp4": ".mp4",
                "application/pdf": ".pdf",
            }
            extension = fallbacks.get(content_type, ".bin")
        return extension

    def process_incoming_message(self, request_data: dict) -> str:
        """
        Process incoming WhatsApp message and save any media
        Returns: TwiML response
        """
        try:
            message_sid = request_data.get("MessageSid")
            num_media = int(request_data.get("NumMedia", 0))
            saved_files = []

            # Handle media if present
            for i in range(num_media):
                media_url = request_data.get(f"MediaUrl{i}")
                content_type = request_data.get(f"MediaContentType{i}")

                if media_url and content_type:
                    content, original_filename = self._download_media(media_url)
                    if content:
                        # Get extension from content type
                        extension = self._get_file_extension(content_type)

                        # Create filename with proper extension
                        base_filename = (
                            os.path.splitext(original_filename)[0]
                            if original_filename
                            else f"media_{i}"
                        )
                        filename = f"{base_filename}{extension}"

                        saved_path = self._save_media(content, filename, message_sid)
                        if saved_path:
                            saved_files.append(saved_path)

            # Create response based on received content
            if saved_files:
                response_message = f"Received {len(saved_files)} media files"
            else:
                response_message = "Received your message"

            return self.create_response(response_message)

        except Exception as e:
            print(f"Error processing incoming message: {str(e)}")
            return self.create_response(
                "Sorry, there was an error processing your message"
            )

    def send_message(
        self,
        to_phone: str,
        message: str,
        media_paths: List[str] = None,
        media_urls: List[str] = None,
    ) -> Optional[TwilioMessage]:
        """
        Send WhatsApp message with optional media
        :param media_paths: List of local file paths
        :param media_urls: List of public URLs for media
        """
        try:
            # Prepare message parameters
            message_params = {
                "body": message,
                "from_": self.format_whatsapp_number(self.whatsapp_number),
                "to": self.format_whatsapp_number(to_phone),
            }

            # Handle media
            if media_paths:
                message_params["media_url"] = [
                    default_storage.url(path) for path in media_paths
                ]
            elif media_urls:
                message_params["media_url"] = media_urls

            # Send message
            twilio_message = self.client.messages.create(**message_params)

            # Create media items for response
            media_items = []
            if media_paths:
                for path, url in zip(media_paths, message_params["media_url"]):
                    media_items.append(
                        TwilioMedia(
                            url=url,
                            content_type=mimetypes.guess_type(path)[0],
                            local_path=path,
                        )
                    )
            elif media_urls:
                for url in media_urls:
                    media_items.append(
                        TwilioMedia(url=url, content_type=mimetypes.guess_type(url)[0])
                    )

            # Return message object
            return TwilioMessage(
                message_sid=twilio_message.sid,
                body=message,
                sender=self.whatsapp_number,
                recipient=to_phone,
                media=media_items,
                direction="outbound",
                timestamp=datetime.now().isoformat(),
                status=twilio_message.status,
            )

        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return None

    def parse_incoming_message(self, request_data: dict) -> TwilioMessage:
        """Parse incoming webhook data into TwilioMessage object"""
        try:
            # Extract basic message info
            message_sid = request_data.get("MessageSid", "")
            body = request_data.get("Body", "")
            sender = request_data.get("From", "").replace("whatsapp:", "")
            recipient = request_data.get("To", "").replace("whatsapp:", "")
            num_media = int(request_data.get("NumMedia", 0))
            timestamp = request_data.get("DateCreated", datetime.now().isoformat())

            # Process media if present
            media_items = []
            for i in range(num_media):
                media_url = request_data.get(f"MediaUrl{i}")
                content_type = request_data.get(f"MediaContentType{i}")

                if media_url and content_type:
                    # Download and save media
                    local_path = self._save_incoming_media(
                        media_url, content_type, message_sid
                    )

                    media_items.append(
                        TwilioMedia(
                            url=media_url,
                            content_type=content_type,
                            local_path=local_path,
                        )
                    )

            return TwilioMessage(
                message_sid=message_sid,
                body=body,
                sender=sender,
                recipient=recipient,
                media=media_items,
                direction="inbound",
                timestamp=timestamp,
            )

        except Exception as e:
            print(f"Error parsing message: {str(e)}")
            raise

    def _save_incoming_media(
        self, media_url: str, content_type: str, message_sid: str
    ) -> Optional[str]:
        """Download and save media file, return local path"""
        try:
            content, _ = self._download_media(media_url)
            if content:
                extension = self._get_file_extension(content_type)
                filename = f"{message_sid}_{datetime.now().timestamp()}{extension}"

                return self._save_media(content, filename, message_sid)
            return None
        except Exception as e:
            print(f"Error saving media: {str(e)}")
            return None

    def get_message_history(self, limit: int = 10) -> List[dict]:
        """
        Retrieve WhatsApp message history
        """
        try:
            messages = self.client.messages.list(limit=limit)
            return [
                {
                    "sid": msg.sid,
                    "body": msg.body,
                    "from": msg.from_,
                    "to": msg.to,
                    "status": msg.status,
                    "media_urls": (
                        [media.uri for media in msg.media.list()]
                        if msg.num_media != "0"
                        else []
                    ),
                }
                for msg in messages
                if msg.from_.startswith("whatsapp:") or msg.to.startswith("whatsapp:")
            ]
        except Exception as e:
            print(f"Error retrieving messages: {str(e)}")
            return []

    def create_response(self, message: str, media_urls: List[str] = None) -> str:
        """
        Create a TwiML response for incoming WhatsApp messages
        """
        response = MessagingResponse()
        msg = response.message(message)

        if media_urls:
            for media_url in media_urls:
                msg.media(media_url)

        return str(response)
