from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services.twilio_api import TwilioService

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


@require_GET
def hello_world(request):
    """
    Simple hello world endpoint
    Endpoint: /hello/
    """
    return HttpResponse("Hello, World!")
