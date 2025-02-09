import io
import json
from difflib import SequenceMatcher

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
    elif intent == "CREATE_TRANSACTION":
        create_transaction(twilio_message)
    elif intent == "UPDATE_TRANSACTION":
        update_transaction(twilio_message)
    elif intent == "DELETE_TRANSACTION":
        delete_transaction(twilio_message)
    elif intent == "ANALYTICS_REQUEST":
        pass
    elif intent == "MULTIPLE_TRANSACTIONS":
        pass
    else:
        print(answer_miscellaneous_query(twilio_message))

    # twilio_service.send_message(twilio_message.sender, intent)
    return HttpResponse(
        content=twilio_service.create_response(intent, media_urls=[SAMPLE_IMAGE_URL]),
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


def fetchUser(twilio_message: TwilioMessage):
    """
    Fetch user details
    Args:
        twilio_message: TwilioMessage object containing user details
    Returns:
        User object
    """
    try:
        user = User.objects.get(number=twilio_message.sender)
        return user
    except User.DoesNotExist:
        return None


def create_transaction(twilio_message: TwilioMessage):
    """
    Create a new transaction record
    Args:
        twilio_message: TwilioMessage containing transaction details
    Returns:
        Created transaction object
    """
    try:
        user = fetchUser(twilio_message)
        if user:
            jsonData = gemini_service.extract_transaction_details(
                twilio_message.body, [media.url for media in twilio_message.media]
            )
            if jsonData:
                # Initialize transaction with required fields
                transaction = Transaction(
                    familyId=user.familyId,
                    userId=user.userId,
                    type=jsonData.get("type", "expense"),
                    category=jsonData.get("category", "misc"),
                    year=int(jsonData.get("year")),
                    month=int(jsonData.get("month")),
                    day=int(jsonData.get("day")),
                    amount=float(jsonData.get("amount", 0.0)),
                    description=jsonData.get("description", ""),
                )
                transaction.save()
                return transaction
        return None
    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        return None


def update_transaction(twilio_message: TwilioMessage):
    """
    Update the latest transaction matching amount and type for a user's family
    using brute force search
    Args:
        twilio_message: TwilioMessage containing search criteria and update details
    Returns:
        Updated transaction object
    """

    user = fetchUser(twilio_message)
    if user:
        data = gemini_service.extract_transaction_update_details(
            twilio_message.body, [media.url for media in twilio_message.media]
        )

        # Get all transactions for the family
        all_transactions = Transaction.objects.all()
        family_transactions = all_transactions.filter(familyId=user.familyId)

        print(f"Found {len(family_transactions)} transactions for family")
        # Search criteria
        search_type = data["search"].get("type", "expense")
        search_amount = int(data["search"].get("amount", 0))

        print(f"Searching for type: {search_type}, amount: {search_amount}")

        # Filter matching transactions
        matching_transactions = []
        for transaction in family_transactions:
            print(f"Checking transaction: {transaction}")
            if search_amount == int(transaction.amount):
                if search_type and transaction.type == search_type:
                    matching_transactions.append(transaction)

        print("Matching transactions:", matching_transactions)
        for t in matching_transactions:
            print(
                f"ID: {t.id}, Type: {t.type}, Amount: {t.amount}, Date: {t.year}-{t.month}-{t.day}"
            )
        # Get the latest matching transaction
        if matching_transactions:
            latest_transaction = max(
                matching_transactions, key=lambda x: (x.year, x.month, x.day)
            )

            print(f"Found transaction to update: {latest_transaction.id}")
            # Apply updates to the latest transaction
            for field, value in data["updates"].items():
                if field in ["year", "month", "day"]:
                    value = int(value)
                elif field == "amount":
                    value = float(value)
                setattr(latest_transaction, field, value)
            latest_transaction.save()
            return latest_transaction
    return None


def delete_transaction(twilio_message: TwilioMessage):
    """
    Update the latest transaction matching amount and type for a user's family
    using brute force search
    Args:
        twilio_message: TwilioMessage containing search criteria and update details
    Returns:
        Updated transaction object
    """

    user = fetchUser(twilio_message)
    if user:
        data = gemini_service.extract_transaction_update_details(
            twilio_message.body, [media.url for media in twilio_message.media]
        )

        # Get all transactions for the family
        all_transactions = Transaction.objects.all()
        family_transactions = all_transactions.filter(familyId=user.familyId)

        print(f"Found {len(family_transactions)} transactions for family")
        # Search criteria
        search_type = data["search"].get("type", "expense")
        search_amount = int(data["search"].get("amount", 0))

        print(f"Searching for type: {search_type}, amount: {search_amount}")

        # Filter matching transactions
        matching_transactions = []
        for transaction in family_transactions:
            print(f"Checking transaction: {transaction}")
            if search_amount == int(transaction.amount):
                if search_type and transaction.type == search_type:
                    matching_transactions.append(transaction)

        print("Matching transactions:", matching_transactions)
        for t in matching_transactions:
            print(
                f"ID: {t.id}, Type: {t.type}, Amount: {t.amount}, Date: {t.year}-{t.month}-{t.day}"
            )
        # Get the latest matching transaction
        if matching_transactions:
            latest_transaction = max(
                matching_transactions, key=lambda x: (x.year, x.month, x.day)
            )

            latest_transaction.delete()
            return latest_transaction
    return None


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


def answer_miscellaneous_query(twilio_message: TwilioMessage):
    """
    Answer miscellaneous queries using Gemini API
    Endpoint: /answer/
    """
    return gemini_service.answer_miscellaneous_query(
        twilio_message.body, [media.url for media in twilio_message.media]
    )
