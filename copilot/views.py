from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services.twilio_api import TwilioService


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Handle incoming WhatsApp messages using TwilioService
    Endpoint: /whatsapp/
    """
    try:
        twilio_service = TwilioService()

        # Get message details from request
        incoming_msg = request.POST.get("Body", "").lower()
        sender = request.POST.get("From", "").replace("whatsapp:", "")
        num_media = int(request.POST.get("NumMedia", 0))

        print(f"Received message from {sender}: {incoming_msg}")

        # Process message and any media using our service
        twiml_response = twilio_service.process_incoming_message(request.POST)

        # Send a response back with a random image
        if num_media > 0:
            print(f"Message contains {num_media} media files")

        return HttpResponse(content=twiml_response, content_type="text/xml")

    except Exception as e:
        print(f"Error processing WhatsApp message: {str(e)}")
        return HttpResponse(
            content=twilio_service.create_response("Sorry, an error occurred"),
            content_type="text/xml",
        )


@require_GET
def hello_world(request):
    """
    Simple hello world endpoint
    Endpoint: /hello/
    """
    return HttpResponse("Hello, World!")
