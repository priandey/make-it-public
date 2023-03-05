import logging
from django.http import HttpRequest
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
