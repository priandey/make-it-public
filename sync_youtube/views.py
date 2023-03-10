import logging
import json
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect

from sync_youtube.models.song import YoutubeSong
from sync_youtube.models.playlist import RemotePlaylist
from sync_youtube.api.youtube import YoutubeAPI
# Create your views here.

logger = logging.getLogger("app")


def index(request: HttpRequest):
    liked_songs = []
    user_playlist_ids = []
    if request.user.is_authenticated:
        liked_songs.extend(
            list(
                YoutubeSong.objects.filter(local_playlist__user=request.user).order_by("is_synched", "title")
            )
        )
        user_playlist_ids.extend(
            RemotePlaylist.objects.filter(
                local_playlist__user=request.user,
                is_synched=True,
            ).values_list("third_party_id", flat=True)
        )

    return render(
        request,
        "sync_youtube/index.html",
        context={
            "liked_songs": liked_songs,
            "user_playlist_ids": user_playlist_ids
        }
    )


def fetch_songs(request: HttpRequest):
    YoutubeAPI.extract_liked_musics(request)
    YoutubeAPI.make_playlists_split(request)
    return redirect("index", permanent=False)


def publish_songs(request: HttpRequest):
    YoutubeAPI.sync_remote_playlists(request)
    YoutubeAPI.sync_remote_playlists_content(request)
    return redirect("index", permanent=False)


def switch_song(request: HttpRequest):
    if request.method == "POST":
        body = json.loads(request.body)
        song_id = body.get("id")
        if song_id is not None:
            song = YoutubeSong.objects.filter(
                local_playlist__user=request.user,
                id=song_id,
            ).first()
            if song is None:
                logger.warning("Failed to fetch song with id %s in user %s", song_id, request.user)
                return HttpResponseNotFound()
            song.should_not_be_published = not song.should_not_be_published
            song.save()
        return HttpResponse(status=200)
    else:
        return HttpResponseNotFound()


def policies(request: HttpRequest):
    return render(
        request,
        template_name="sync_youtube/policies.html"
    )


def terms_of_service(request: HttpRequest):
    return render(
        request,
        template_name="sync_youtube/terms-of-service.html"
    )
