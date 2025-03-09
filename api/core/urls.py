from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from ninja_extra import NinjaExtraAPI

from .custom_scalar_viewer import CustomScalarViewer

api = NinjaExtraAPI(
    version="1.0.0 beta",
    title="F5-TTS API",
    description="API Reference for F5-TTS research and developed by Watthanasak Jeamwatthanachai, PhD.",
    docs=CustomScalarViewer(),
    docs_url="/docs/",
)


def add_routers(api: NinjaExtraAPI):
    api.add_router('tts', 'tts.api.tts.router')
    api.add_router('tts/speaker', 'tts.api.speaker.router')
    api.add_router('tts/config', 'tts.api.config.router')


add_routers(api)


def redirect_landing(request):
    return redirect("/api/docs/")


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
    path("", redirect_landing),
]
