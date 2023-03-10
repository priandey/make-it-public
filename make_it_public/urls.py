"""make_it_public URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from sync_youtube.views import index, fetch_songs, publish_songs, policies, switch_song, terms_of_service
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("", index, name="index"),
    path("fetch-songs/", fetch_songs, name="fetch-songs"),
    path("publish-songs/", publish_songs, name="publish-songs"),
    path("switch-song/", switch_song, name="switch_song"),
    path("policies/", policies, name="policies"),
    path("terms-of-service/", terms_of_service, name="terms_of_service"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
