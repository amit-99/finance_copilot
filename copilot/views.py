import io
import json

from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from PIL import Image

from copilot.constants import INTENTS, PROMPT_CLASSIFY_MESSAGE
from copilot.datamodels.twilio_message import TwilioMessage
from copilot.models import Transaction, User

from .services.gemini_api import GeminiService
from .services.twilio_api import TwilioService

SAMPLE_IMAGE_URL = "https://picsum.photos/200/300"

twilio_service = TwilioService()
gemini_service = GeminiService()


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Handle incoming WhatsApp messages using TwilioService
    Endpoint: /whatsapp/
    """
    try:

        # Parse incoming message
        twilio_message = twilio_service.parse_incoming_message(request.POST)
        print(f"Received message from {twilio_message.sender}: {twilio_message.body}")

        # if not check_user_exists(twilio_message.sender):
        #     print(f"User not found, creating new user")
        #     twilio_service.send_message(
        #         twilio_message.sender,
        #         "Hello! I'm your financial copilot. Please tell me your name to get started.",
        #     )
        #     return HttpResponse(
        #         content=twilio_service.create_response("Please tell me your name"),
        #         content_type="text/xml",
        #     )

        # Identify intent of the message
        intent = identify_intent(twilio_message, gemini_service)
        print(f"Identified intent: {intent}")
        if intent == "INPUT_NAME" and not check_user_exists(twilio_message.sender):
            create_user(twilio_message)
        # if twilio_message.has_media:
        #     print(f"Message contains {len(twilio_message.media)} media files")
        #     for media in twilio_message.media:
        #         print(f"Media saved at: {media.local_path}")

        #         # Handle audio files
        #         if media.content_type and media.content_type.startswith("audio/"):
        #             print(f"Processing audio file: {media.content_type}")
        #             # Get absolute file path from storage
        #             abs_file_path = default_storage.path(media.local_path)
        #             transcribed_text = gemini_service.convert_speech_to_text(
        #                 abs_file_path
        #             )
        #             if transcribed_text:
        #                 print(f"Transcribed audio: {transcribed_text}")
        #                 audio_transcriptions.append(transcribed_text)

        # # Build response message
        # if audio_transcriptions:
        #     response_text += "\nTranscribed audio message(s):\n" + "\n".join(
        #         f"- {text}" for text in audio_transcriptions
        #     )
        # elif twilio_message.has_media:
        #     response_text += (
        #         f" I received your {len(twilio_message.media)} media files."
        #     )
        twilio_service.send_message(twilio_message.sender, intent)
        return HttpResponse(
            content=twilio_service.create_response(
                intent, media_urls=[SAMPLE_IMAGE_URL]
            ),
            content_type="text/xml",
        )

    except Exception as e:
        print(f"Error processing WhatsApp message: {str(e)}")
        return HttpResponse(
            content=TwilioService().create_response("Sorry, an error occurred"),
            content_type="text/xml",
        )


@csrf_exempt
def test_gemini(request):
    """
    Test Gemini API integration
    GET: /gemini/test/ - Test text-only queries
    POST: /gemini/test/ - Test queries with images
    """
    try:
        gemini_service = GeminiService()

        if request.method == "GET":
            # Test simple text query
            query = request.GET.get("query", "Tell me about financial planning")
            response = gemini_service.send_message(query)
            return JsonResponse({"success": True, "response": response})

        elif request.method == "POST":
            data = json.loads(request.body)
            query = data.get("query", "What do you see in these images?")
            image_urls = data.get("image_urls", [])

            if image_urls:
                response = gemini_service.send_message_with_images(query, image_urls)
            else:
                response = gemini_service.send_message(query)

            return JsonResponse({"success": True, "response": response})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_GET
def hello_world(request):
    """
    Simple hello world endpoint
    Endpoint: /hello/
    """
    return HttpResponse("Hello, World!")


def identify_intent(
    twilio_message: TwilioMessage, gemini_service: GeminiService
) -> str:
    """
    Identify the intent of a TwilioMessage using Gemini API
    Returns one of the predefined INTENTS
    """
    try:
        # Replace placeholder in prompt with actual message
        prompt = PROMPT_CLASSIFY_MESSAGE.replace("$message", twilio_message.body)

        # If message has media, use multimodal classification
        if twilio_message.has_media:
            # Get media URLs for all media items
            media_urls = [media.url for media in twilio_message.media]
            response = gemini_service.send_message_with_images(prompt, media_urls)
        else:
            # Text-only classification
            response = gemini_service.send_message(prompt)

        # Clean and validate the response
        intent = response.strip().upper()
        if intent in INTENTS:
            return intent.strip().upper()

        return intent

    except Exception as e:
        print(f"Error identifying intent: {str(e)}")
        return "OTHER"


def create_transaction(payload: dict):
    """
    Create a new transaction record
    Args:
        payload: Dictionary containing transaction details (amount, category, description, date)
    Returns:
        Created transaction object
    """
    try:
        transaction = Transaction.objects.create(
            amount=payload.get("amount"),
            category=payload.get("category"),
            description=payload.get("description"),
            date=payload.get("date"),
        )
        return transaction
    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        return None


def update_transaction(transaction_id: int, payload: dict):
    """
    Update an existing transaction
    Args:
        transaction_id: ID of transaction to update
        payload: Dictionary containing updated transaction details
    Returns:
        Updated transaction object
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        for field, value in payload.items():
            setattr(transaction, field, value)
        transaction.save()
        return transaction
    except Exception as e:
        print(f"Error updating transaction: {str(e)}")
        return None


def delete_transaction(transaction_id: int):
    """
    Delete a transaction
    Args:
        transaction_id: ID of transaction to delete
    Returns:
        Boolean indicating success
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        transaction.delete()
        return True
    except Exception as e:
        print(f"Error deleting transaction: {str(e)}")
        return False


def check_user_exists(phone_number: str) -> bool:
    """
    Check if user needs to provide name (True if user doesn't exist or has no name)
    Args:
        phone_number: Phone number to check
    Returns:
        True if user registration is needed, False if user exists with name
    """
    try:
        user = User.objects.get(number=phone_number)
        return not user.name  # True if name is empty/None, False if name exists
    except User.DoesNotExist:
        return True  # True if user doesn't exist


def create_user(twilio_message: TwilioMessage):
    """
    Create a new user record
    Args:
        twilio_message: TwilioMessage object containing user details
    Returns:
        Created user object
    """
    try:
        # Extract user's name using gemini service
        extractedName = gemini_service.extract_user_name(twilio_message.body).strip()
        print(f"Extracted name: {extractedName}")
        user = User(
            name=extractedName,
            number=twilio_message.sender,
        ).save()
        return user
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return None
