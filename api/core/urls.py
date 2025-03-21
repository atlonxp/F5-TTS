from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
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
    return redirect("/f5/api/docs/")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('filer/', include('filer.urls')),
    path('', redirect_landing),
]
if settings.DEBUG:  # Serve static files only in Debug mode
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
