import io
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from PIL import Image

from .services.gemini_api import GeminiService
from .services.twilio_api import TwilioService
from .services.reward_generator import RewardGenerator

SAMPLE_IMAGE_URL = "https://picsum.photos/200/300"


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Handle incoming WhatsApp messages using TwilioService
    Endpoint: /whatsapp/
    """
    try:
        twilio_service = TwilioService()

        # Parse incoming message
        twilio_message = twilio_service.parse_incoming_message(request.POST)
        print(f"Received message from {twilio_message.sender}: {twilio_message.body}")

        if twilio_message.has_media:
            print(f"Message contains {len(twilio_message.media)} media files")
            for media in twilio_message.media:
                print(f"Media saved at: {media.local_path}")

        # Create response with text and image
        response_text = "Thanks for your message! Here's a random image for you."
        if twilio_message.has_media:
            response_text += (
                f" I also received your {len(twilio_message.media)} media files."
            )

        return HttpResponse(
            content=twilio_service.create_response(
                response_text, media_urls=[SAMPLE_IMAGE_URL]
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
def generate_reward(request):
    """
    Generate a random reward coupon
    Endpoint: /reward/
    """
    category_name = request.GET.get("category", None).lower()
    if not category_name:
        return JsonResponse({"success": False, "error": "Category not provided"}, status=400)
    return JsonResponse(
        {
            "success": True,
            "reward": RewardGenerator().generate_coupon(category_name),
        }
    )
@require_GET
def hello_world(request):
    """
    Simple hello world endpoint
    Endpoint: /hello/
    """
    return HttpResponse("Hello, World!")
