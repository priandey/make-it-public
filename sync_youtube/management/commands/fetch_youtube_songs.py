import logging
from django.core.management.base import BaseCommand

from sync_youtube.models.playlist import LocalPlaylist
from sync_youtube.api.youtube import YoutubeAPI, DummyRequest

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = "Fetch youtube songs for all users that have opted in"

    def handle(self, *args, **options):
        playlists_to_update = LocalPlaylist.objects.filter(should_update=True)
        for local_playlist in playlists_to_update:
            try:
                context = DummyRequest(user=local_playlist.user)
                YoutubeAPI.extract_liked_musics(context=context)
            except Exception:
                logger.exception(
                    "Failed to extract liked musics for user %s",
                    local_playlist.user.email,
                    exc_info=True
                )
            YoutubeAPI.make_playlists_split(context=context)
