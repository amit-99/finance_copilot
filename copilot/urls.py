from django.urls import path

from . import views

app_name = "copilot"

urlpatterns = [
    path(
        "whatsapp", views.whatsapp_webhook, name="whatsapp_webhook"
    ),  # Ensure trailing slash
    path("reward", views.generate_reward, name="generate_reward"),
    path("hello/", views.hello_world, name="hello_world"),
    path("gemini/test", views.test_gemini, name="test_gemini"),
]
