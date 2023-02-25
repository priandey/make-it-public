from django.core.management.base import BaseCommand

from sync_youtube.models.playlist import LocalPlaylist
from sync_youtube.api.youtube import YoutubeAPI, DummyRequest


class Command(BaseCommand):
    help = "Fetch youtube songs for all users that have opted in"

    def handle(self, *args, **options):
        playlists_to_update = LocalPlaylist.objects.filter(should_update=True)
        for local_playlist in playlists_to_update:
            context = DummyRequest(user=local_playlist.user)
            YoutubeAPI.extract_liked_musics(context=context)
            YoutubeAPI.make_playlists_split(context=context)
